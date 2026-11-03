
#include <iostream>
#include <fstream>
#include <cmath>
#include <stdint.h>

#include <ap_axi_sdata.h>
#include <hls_stream.h>

#define N_SAMPLES 1000

typedef ap_axiu<32, 1, 1, 1> axis_t;

void fir(hls::stream<axis_t>& in,
         hls::stream<axis_t>& out,
         int N);

static uint32_t float_to_bits(float value)
{
    union {
        uint32_t u;
        float f;
    } converter;

    converter.f = value;
    return converter.u;
}

static float bits_to_float(uint32_t bits)
{
    union {
        uint32_t u;
        float f;
    } converter;

    converter.u = bits;
    return converter.f;
}

int main()
{
    float x[N_SAMPLES];
    float expected[N_SAMPLES];

    hls::stream<axis_t> input_stream;
    hls::stream<axis_t> output_stream;

    std::ifstream inputFile(
        "D:\\vivado_file\\fir_hls_practice\\solution1\\data\\input_signal.txt"
    );

    if (!inputFile.is_open()) {
        std::cout << "ERROR: Cannot open input_signal.txt\n";
        return 1;
    }

    for (int i = 0; i < N_SAMPLES; i++) {
        if (!(inputFile >> x[i])) {
            std::cout << "ERROR: Input data missing at index "
                      << i << "\n";
            return 1;
        }

        axis_t word;
        word.data = float_to_bits(x[i]);
        word.keep = -1;
        word.strb = -1;
        word.user = 0;
        word.id = 0;
        word.dest = 0;
        word.last = (i == N_SAMPLES - 1) ? 1 : 0;

        input_stream.write(word);
    }
    inputFile.close();

    std::ifstream outputFile(
        "D:\\vivado_file\\fir_hls_practice\\solution1\\data\\expected_output.txt"
    );

    if (!outputFile.is_open()) {
        std::cout << "ERROR: Cannot open expected_output.txt\n";
        return 1;
    }

    for (int i = 0; i < N_SAMPLES; i++) {
        if (!(outputFile >> expected[i])) {
            std::cout << "ERROR: Expected data missing at index "
                      << i << "\n";
            return 1;
        }
    }
    outputFile.close();

    fir(input_stream, output_stream, N_SAMPLES);

    const float tolerance = 1e-3f;
    float maxError = 0.0f;
    double sumError = 0.0;
    int errorCount = 0;

    for (int i = 0; i < N_SAMPLES; i++) {
        axis_t word = output_stream.read();
        float y = bits_to_float((uint32_t)word.data);

        float error = fabsf(y - expected[i]);

        if (error > maxError)
            maxError = error;

        sumError += error;

        if (error >= tolerance) {
            if (errorCount < 10) {
                std::cout << "Mismatch at index " << i
                          << ": HLS = " << y
                          << ", expected = " << expected[i]
                          << ", error = " << error << "\n";
            }
            errorCount++;
        }

        if ((i == N_SAMPLES - 1) != ((bool)word.last)) {
            std::cout << "TLAST error at index " << i << "\n";
            errorCount++;
        }
    }

    std::cout << "\n===== FIR AXI Stream Comparison Report =====\n";
    std::cout << "Samples compared: " << N_SAMPLES << "\n";
    std::cout << "Max absolute error: " << maxError << "\n";
    std::cout << "Mean absolute error: "
              << sumError / N_SAMPLES << "\n";
    std::cout << "Failed checks: " << errorCount << "\n";

    if (errorCount == 0)
        std::cout << "TEST PASS!\n";
    else
        std::cout << "TEST FAIL!\n";

    return errorCount == 0 ? 0 : 1;
}
