# input — 输入测试数据说明

本目录**不放数据副本**，因为输入数据已随源码一起提交，且与代码强绑定（同一数组被 C 程序与离线对拍脚本共用）。

## 数据位置

| 数组 | 位置 | 类型 / 长度 | 说明 |
|---|---|---|---|
| `SineInput` | `03_SDK_Software/fir_test/src/fir_test_inputs.h` 第 7–208 行 | `static const float[1000]` | 单频正弦，幅值 ±1.0，1000 点 |
| `MixedInput` | 同上，第 210–411 行 | `static const float[1000]` | 双频混频，幅值约 ±1.47，1000 点 |宏：`#define TEST_INPUT_COUNT 1000`

## 冲激输入

冲激响应测试**不使用数组**：由程序在 `TxBuffer` 中构造单位冲激（`x[0]=1`，其余 0），输出前 51 点即逼近滤波器系数。对应产物为 `../output/fir_impulse_fpga_1000.bin`。

## 与输出文件的对应关系

| 输入 | 输出文件 | 版本 |
|---|---|---|
| `MixedInput` | `fir_mixed_fpga_1000.bin` | V1.0（仅混频一组） |
| `SineInput` | `fir_sine_fpga_1000.bin` | V1.0 |
| 单位冲激 | `fir_impulse_fpga_1000.bin` | V1.0 |
| `SineInput` | `fir_sine_fpga_perf_1000.bin` | 性能版第 1 组 |
| `MixedInput` | `fir_mixed_fpga_perf_1000.bin` | 性能版第 2 组 |

## 文件格式

所有 `.bin` 为 **1000 个 float32 小端**（IEEE-754，4,000 字节），顺序与输入样本一一对应：

```python
import struct
vals = list(struct.unpack('<1000f', open('fir_sine_fpga_perf_1000.bin','rb').read()))
```

`../dumps/*.txt` 是同一批数据的 JTAG 原始读取记录（每行一个 32 位十六进制字，1000 行），可用于交叉核对。

## 复算方法

```python
# 系数与 HLS 一致（51 个，24 位定点量化后）
h = [...]   # 见 01_HLS_Accelerator/src/fir.cpp 的 h[N_TAPS]
y[n] = sum(h[k] * x[n-k] for k in range(51) if n-k >= 0)   # 越界历史视为 0
```
与 `../output/*_perf_1000.bin` 逐点比对，实测最大绝对误差约 **2×10⁻⁶**（**不是零误差**，来自定点量化与 float 往返）。
