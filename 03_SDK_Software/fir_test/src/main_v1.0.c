/*
 * main.c
 *
 *  Created on: 2026Äê10ÔÂ23ÈÕ
 *      Author: pig22
 */



#include "xparameters.h"
#include "xstatus.h"
#include "xaxidma.h"
#include "xfir.h"
#include "xil_cache.h"
#include "xil_types.h"
#include "fir_test_inputs.h"

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

static float abs_float(float x)
{
    return (x < 0.0f) ? -x : x;
}

int main(void)
{
    int status;
    u32 timeout;
    int i;

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

    /* 3. Prepare input and output */
    for (i = 0; i < SAMPLE_COUNT; i++) {
        TxBuffer[i] = 0.0f;
        RxBuffer[i] = 0.0f;
    }

    /* Sine input: 1000 samples */
    for (i = 0; i < SAMPLE_COUNT; i++) {
    	TxBuffer[i] = MixedInput[i];
    }

    /*
     * For a FIR impulse response, the first
     * 51 outputs should resemble coefficients.
     */

    /* 4. Cache maintenance */
    Xil_DCacheFlushRange(
        (INTPTR)TxBuffer, BUFFER_BYTES);

    Xil_DCacheFlushRange(
        (INTPTR)RxBuffer, BUFFER_BYTES);

    /* 5. Configure FIR */
    XFir_Set_N(&Fir, SAMPLE_COUNT);
    XFir_DisableAutoRestart(&Fir);

    /* 6. Start DMA receive first */
    status = XAxiDma_SimpleTransfer(
        &AxiDma,
        (UINTPTR)RxBuffer,
        BUFFER_BYTES,
        XAXIDMA_DEVICE_TO_DMA);

    if (status != XST_SUCCESS) {
        test_status = -5;
        return -1;
    }

    /* 7. Start FIR */
    XFir_Start(&Fir);

    /* 8. Start DMA transmit */
    status = XAxiDma_SimpleTransfer(
        &AxiDma,
        (UINTPTR)TxBuffer,
        BUFFER_BYTES,
        XAXIDMA_DMA_TO_DEVICE);

    if (status != XST_SUCCESS) {
        test_status = -6;
        return -1;
    }

    /* 9. Wait for both DMA channels */
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
        test_status = -7;
        return -1;
    }

    Xil_DCacheInvalidateRange((INTPTR)RxBuffer, BUFFER_BYTES);

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

    while (1) {
    }

    return 0;
}
