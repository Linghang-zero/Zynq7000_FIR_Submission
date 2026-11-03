
#include <ap_fixed.h>
#include <ap_axi_sdata.h>
#include <hls_stream.h>
#include <stdint.h>

#define N_TAPS 51
#define N_SAMPLES 1000
#define N_PAIRS 25

typedef ap_fixed<24, 4> data_t;
typedef ap_fixed<24, 2> coeff_t;
typedef ap_fixed<40, 8> accum_t;
typedef ap_fixed<48, 8> product_t;

// 32-bit AXI4-Stream data with TLAST.
typedef ap_axiu<32, 1, 1, 1> axis_t;

static const coeff_t h[N_TAPS] = {
    0.00000000, 0.00016465, 0.00038504, 0.00070848,
    0.00118405, 0.00185986, 0.00278022, 0.00398283,
    0.00549623, 0.00733749, 0.00951047, 0.01200451,
    0.01479393, 0.01783813, 0.02108243, 0.02445963,
    0.02789218, 0.03129494, 0.03457835, 0.03765189,
    0.04042769, 0.04282411, 0.04476907, 0.04620310,
    0.04708181, 0.04737780, 0.04708181, 0.04620310,
    0.04476907, 0.04282411, 0.04042769, 0.03765189,
    0.03457835, 0.03129494, 0.02789218, 0.02445963,
    0.02108243, 0.01783813, 0.01479393, 0.01200451,
    0.00951047, 0.00733749, 0.00549623, 0.00398283,
    0.00278022, 0.00185986, 0.00118405, 0.00070848,
    0.00038504, 0.00016465, 0.00000000
};

static float bits_to_float(uint32_t bits)
{
    union {
        uint32_t u;
        float f;
    } converter;

    converter.u = bits;
    return converter.f;
}

static uint32_t float_to_bits(float value)
{
    union {
        uint32_t u;
        float f;
    } converter;

    converter.f = value;
    return converter.u;
}

void fir(hls::stream<axis_t>& in,
         hls::stream<axis_t>& out,
         int N)
{
#pragma HLS INTERFACE axis port=in
#pragma HLS INTERFACE axis port=out
#pragma HLS INTERFACE s_axilite port=N bundle=CTRL
#pragma HLS INTERFACE s_axilite port=return bundle=CTRL

    data_t history[N_TAPS];
#pragma HLS ARRAY_PARTITION variable=history complete

    for (int i = 0; i < N_TAPS; i++) {
#pragma HLS UNROLL
        history[i] = 0;
    }

    for (int n = 0; n < N; n++) {
#pragma HLS PIPELINE II=1

        axis_t input_word = in.read();
        float input_float = bits_to_float(
            (uint32_t)input_word.data
        );

        data_t sample = (data_t)input_float;

        for (int i = N_TAPS - 1; i > 0; i--) {
#pragma HLS UNROLL
            history[i] = history[i - 1];
        }
        history[0] = sample;

        accum_t acc0 = 0;
        accum_t acc1 = 0;
        accum_t acc2 = 0;
        accum_t acc3 = 0;

        for (int k = 0; k < N_PAIRS; k++) {
#pragma HLS UNROLL
            data_t pair_sum = history[k] + history[N_TAPS - 1 - k];
            product_t product = h[k] * pair_sum;

            if (k % 4 == 0)
                acc0 += product;
            else if (k % 4 == 1)
                acc1 += product;
            else if (k % 4 == 2)
                acc2 += product;
            else
                acc3 += product;
        }

        accum_t acc = (acc0 + acc1) + (acc2 + acc3);
        acc += h[N_PAIRS] * history[N_PAIRS];

        axis_t output_word;
        output_word.data = float_to_bits((float)acc);
        output_word.keep = -1;
        output_word.strb = -1;
        output_word.user = 0;
        output_word.id = 0;
        output_word.dest = 0;
        output_word.last = (n == N - 1) ? 1 : 0;

        out.write(output_word);
    }
}
