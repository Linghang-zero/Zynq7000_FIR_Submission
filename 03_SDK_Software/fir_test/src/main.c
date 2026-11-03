/*
 * main.c
 *
 *  Created on: 2026��10��23��
 *      Author: pig22
 */



#include "xparameters.h"
#include "xstatus.h"
#include "xaxidma.h"
#include "xfir.h"
#include "xil_cache.h"
#include "xil_types.h"
#include "fir_test_inputs.h"
#include "xtime_l.h"

#define SAMPLE_COUNT 1000
#define BUFFER_BYTES (SAMPLE_COUNT * sizeof(float))
#define TIMEOUT_LIMIT 100000000U

#define DMA_DEVICE_ID XPAR_AXIDMA_0_DEVICE_ID
#define FIR_DEVICE_ID XPAR_FIR_0_DEVICE_ID

#define FIR_TAPS 51
#define ERROR_TOLERANCE 0.00001f

static const float ReferenceCoeffs[FIR_TAPS] = {
    0.00000000f, 0.00016465f, 0.00038504f, 0.00070848f,
    0.00118405f, 0.00185986f, 0.00278022f, 0.00398283f,
    0.00549623f, 0.00733749f, 0.00951047f, 0.01200451f,
    0.01479393f, 0.01783813f, 0.02108243f, 0.02445963f,
    0.02789218f, 0.03129494f, 0.03457835f, 0.03765189f,
    0.04042769f, 0.04282411f, 0.04476907f, 0.04620310f,
    0.04708181f, 0.04737780f, 0.04708181f, 0.04620310f,
    0.04476907f, 0.04282411f, 0.04042769f, 0.03765189f,
    0.03457835f, 0.03129494f, 0.02789218f, 0.02445963f,
    0.02108243f, 0.01783813f, 0.01479393f, 0.01200451f,
    0.00951047f, 0.00733749f, 0.00549623f, 0.00398283f,
    0.00278022f, 0.00185986f, 0.00118405f, 0.00070848f,
    0.00038504f, 0.00016465f, 0.00000000f
};

static XAxiDma AxiDma;
static XFir Fir;

/* Aligned buffers for DMA */
static float TxBuffer[SAMPLE_COUNT] __attribute__((aligned(64)));
static float RxBuffer[SAMPLE_COUNT] __attribute__((aligned(64)));

/* Inspect these variables in the SDK debugger */
volatile int test_status = 0;
volatile int completed_samples = 0;
volatile float first_output = 0.0f;
volatile float max_abs_error = 0.0f;

volatile int max_error_index = -1;
volatile int error_count = 0;

/* ===== ARM software FIR benchmark (perf test only) ===== */
static float SwSineOut[SAMPLE_COUNT];
static float SwMixedOut[SAMPLE_COUNT];

volatile u64 sw_sine_cycles = 0;
volatile u64 sw_mixed_cycles = 0;
volatile double sw_sine_us = 0.0;
volatile double sw_mixed_us = 0.0;
volatile float sw_sine_checksum = 0.0f;
volatile float sw_mixed_checksum = 0.0f;
volatile float sw_sine_out0 = 0.0f;
volatile float sw_mixed_out0 = 0.0f;

/*
 * Causal software FIR, same relation as the HLS core:
 *   y[n] = sum(h[k] * x[n-k]), k = 0..50, x[m] = 0 for m < 0.
 * Uses ReferenceCoeffs (51 taps), which are verified identical
 * to h[] in fir_v1_backup.cpp (HLS coeff_t definition).
 */
static void sw_fir_filter(const float *x, int n, float *y)
{
    int i, k;

    for (i = 0; i < n; i++) {
        float acc = 0.0f;
        for (k = 0; k < FIR_TAPS; k++) {
            int idx = i - k;
            if (idx >= 0) {
                acc += ReferenceCoeffs[k] * x[idx];
            }
        }
        y[i] = acc;
    }
}

/* ===== FPGA + DMA end-to-end benchmark (perf test only) ===== */
volatile u64 hw_sine_cycles = 0;
volatile u64 hw_mixed_cycles = 0;
volatile double hw_sine_us = 0.0;
volatile double hw_mixed_us = 0.0;

/*
 * One FPGA + DMA end-to-end run (input prep -> cache flush ->
 * RX DMA arm -> FIR start -> TX DMA arm -> wait both -> RX invalidate).
 * Returns 0 on success, or the original negative error code.
 * NOTE: the caller is responsible for the XTime timing window.
 */
static int hw_fir_run(const float *input)
{
    int status;
    int i;
    u32 timeout;

    /* Input preparation: copy into DMA buffer, clear RX buffer */
    for (i = 0; i < SAMPLE_COUNT; i++) {
        TxBuffer[i] = input[i];
        RxBuffer[i] = 0.0f;
    }

    /* Cache maintenance (inside the timed region by design) */
    Xil_DCacheFlushRange(
        (INTPTR)TxBuffer, BUFFER_BYTES);

    Xil_DCacheFlushRange(
        (INTPTR)RxBuffer, BUFFER_BYTES);

    /* Configure FIR for this run */
    XFir_Set_N(&Fir, SAMPLE_COUNT);
    XFir_DisableAutoRestart(&Fir);

    /* Start DMA receive first */
    status = XAxiDma_SimpleTransfer(
        &AxiDma,
        (UINTPTR)RxBuffer,
        BUFFER_BYTES,
        XAXIDMA_DEVICE_TO_DMA);

    if (status != XST_SUCCESS) {
        return -5;
    }

    /* Start FIR */
    XFir_Start(&Fir);

    /* Start DMA transmit */
    status = XAxiDma_SimpleTransfer(
        &AxiDma,
        (UINTPTR)TxBuffer,
        BUFFER_BYTES,
        XAXIDMA_DMA_TO_DEVICE);

    if (status != XST_SUCCESS) {
        return -6;
    }

    /* Wait for both DMA channels (original timeout protection) */
    timeout = TIMEOUT_LIMIT;

    while (timeout > 0U) {
        int tx_busy = XAxiDma_Busy(
            &AxiDma, XAXIDMA_DMA_TO_DEVICE);

        int rx_busy = XAxiDma_Busy(
            &AxiDma, XAXIDMA_DEVICE_TO_DMA);

        if (!tx_busy && !rx_busy) {
            break;
        }

        timeout--;
    }

    if (timeout == 0U) {
        return -7;
    }

    /* Output cache maintenance (last step of the timed region) */
    Xil_DCacheInvalidateRange((INTPTR)RxBuffer, BUFFER_BYTES);

    return 0;
}

static float abs_float(float x)
{
    return (x < 0.0f) ? -x : x;
}

int main(void)
{
    int status;
    XTime t_start, t_end;

    XAxiDma_Config *DmaConfig;

    test_status = 1;

    /* 1. Initialize DMA */
    DmaConfig = XAxiDma_LookupConfig(DMA_DEVICE_ID);

    if (DmaConfig == NULL) {
        test_status = -1;
        return -1;
    }

    status = XAxiDma_CfgInitialize(&AxiDma, DmaConfig);

    if (status != XST_SUCCESS) {
        test_status = -2;
        return -1;
    }

    if (XAxiDma_HasSg(&AxiDma)) {
        test_status = -3;
        return -1;
    }

    /* 2. Initialize FIR */
    status = XFir_Initialize(&Fir, FIR_DEVICE_ID);

    if (status != XST_SUCCESS) {
        test_status = -4;
        return -1;
    }

    /*
     * For a FIR impulse response, the first
     * 51 outputs should resemble coefficients.
     */

    /* 3. Hardware test 1: SineInput, end-to-end timing.
     * Timing starts BEFORE input prep and cache maintenance and
     * stops after DMA completion + RX cache invalidation
     * (both inside hw_fir_run). No UART/print inside the window. */
    XTime_GetTime(&t_start);
    status = hw_fir_run(SineInput);
    XTime_GetTime(&t_end);

    if (status != 0) {
        test_status = status;
        return -1;
    }

    hw_sine_cycles = (u64)(t_end - t_start);
    hw_sine_us = ((double)hw_sine_cycles * 1000000.0)
                 / (double)COUNTS_PER_SECOND;

    /* 4. Hardware test 2: MixedInput, same data flow and timing rules */
    XTime_GetTime(&t_start);
    status = hw_fir_run(MixedInput);
    XTime_GetTime(&t_end);

    if (status != 0) {
        test_status = status;
        return -1;
    }

    hw_mixed_cycles = (u64)(t_end - t_start);
    hw_mixed_us = ((double)hw_mixed_cycles * 1000000.0)
                  / (double)COUNTS_PER_SECOND;

    first_output = RxBuffer[0];
    completed_samples = SAMPLE_COUNT;

    /* DMA transfer completed.
     * Numerical validation will be performed
     * independently by teammate using Python.
     */
    max_abs_error = 0.0f;
    max_error_index = -1;
    error_count = 0;

    test_status = 2;

    /* ===== ARM software FIR benchmark =====
     * Pure computation timing with the Global Timer (XTime).
     * No UART/print/file output inside the timed regions.
     * Results are exposed via volatile variables for the SDK debugger. */
    {
        XTime t_start, t_end;
        u64 sine_cycles, mixed_cycles;
        float sine_sum, mixed_sum;
        int j;

        test_status = 3;

        /* Timed region 1: sine input, 1000 samples */
        XTime_GetTime(&t_start);
        sw_fir_filter(SineInput, SAMPLE_COUNT, SwSineOut);
        XTime_GetTime(&t_end);
        sine_cycles = (u64)(t_end - t_start);

        /* Timed region 2: mixed input, 1000 samples */
        XTime_GetTime(&t_start);
        sw_fir_filter(MixedInput, SAMPLE_COUNT, SwMixedOut);
        XTime_GetTime(&t_end);
        mixed_cycles = (u64)(t_end - t_start);

        /* Outside the timed regions: checksums so the compiler
         * cannot optimize the computation away, then microseconds
         * using the verified COUNTS_PER_SECOND (Global Timer). */
        sine_sum = 0.0f;
        mixed_sum = 0.0f;
        for (j = 0; j < SAMPLE_COUNT; j++) {
            sine_sum += SwSineOut[j];
            mixed_sum += SwMixedOut[j];
        }

        sw_sine_cycles = sine_cycles;
        sw_mixed_cycles = mixed_cycles;
        sw_sine_us = ((double)sine_cycles * 1000000.0)
                     / (double)COUNTS_PER_SECOND;
        sw_mixed_us = ((double)mixed_cycles * 1000000.0)
                      / (double)COUNTS_PER_SECOND;
        sw_sine_checksum = sine_sum;
        sw_mixed_checksum = mixed_sum;
        sw_sine_out0 = SwSineOut[0];
        sw_mixed_out0 = SwMixedOut[0];

        test_status = 4;
    }

    while (1) {
    }

    return 0;
}
