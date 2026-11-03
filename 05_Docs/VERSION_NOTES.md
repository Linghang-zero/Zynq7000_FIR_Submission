# VERSION_NOTES — V1.0 与性能测试版的区别

本文档说明提交包中两个 `main.c` 版本的差异、各自用途，以及**为什么两个都必须保留**。

---

## 0. 一句话总结

| | V1.0（功能验证版） | 性能测试版 |
|---|---|---|
| 文件 | `03_SDK_Software/fir_test/src/main_v1.0.c` | `03_SDK_Software/fir_test/src/main.c` |
| 行数 / 大小 | 198 行 / 4,682 B | 326 行 / 9,069 B |
| MD5 | `fe8ef6b440a14de2b4fc2c6a66ab7f1b` | `51ba9aeeb89a1b79ac9e0ee58c67788a` |
| 硬件测试次数 | 1 组（仅 MixedInput） | 2 组（SineInput + MixedInput） |
| 计时 | **无** | 硬件端到端 + ARM 软件基准，共 8 个计时变量 |
| 最终状态码 | `test_status = 2` | `test_status = 4` |
| 用途 | 证明"FIR 硬件通路能跑通、结果正确" | 证明"加速效果"，产出加速比数据 |

> 二者是**同一条硬件通路的两个阶段**，不是替代关系。V1.0 用于功能正确性，性能版在其上叠加计时与软件对照实现。

---

## 1. V1.0 功能验证版（`main_v1.0.c`）

**流程**（单次、单向）：

```
初始化 DMA + FIR
→ 装填 RxBuffer/TxBuffer（TxBuffer 填 MixedInput）
→ DCacheFlush(Tx, Rx)
→ XFir_Set_N(1000) + DisableAutoRestart
→ DMA RX 装载(S2MM) → XFir_Start → DMA TX 装载(MM2S)
→ 忙等双通道完成（timeout = TIMEOUT_LIMIT，仅作保护）
→ DCacheInvalidate(Rx)
→ first_output = RxBuffer[0]；test_status = 2
→ while(1)
```

**特征**：
- 无任何时间测量。第 158–177 行的 `timeout` 循环是**忙等保护**，计数值本身不被记录，**不是耗时**。
- `ReferenceCoeffs[51]` 在该版本中**只定义、未使用**（编译警告 `ReferenceCoeffs defined but not used`）。
- `max_abs_error` / `max_error_count` 等误差变量仅清零占位，数值比对由队友用 Python 离线完成。
- 状态码：`1` 运行中 → `2` 完成；错误 `-1`…`-7`（DMA 初始化/复位/配置/RX 装载/FIR 启动/TX 装载/超时）。
- 输出数据：`04_Test_Evidence/output/fir_mixed_fpga_1000.bin`、`fir_sine_fpga_1000.bin`、`fir_impulse_fpga_1000.bin`。

**结论**：DMA→FIR→DMA 通路打通，1000 点混频/正弦/冲激响应输出与 Python 参考一致。

---

## 2. 性能测试版（`main.c`）

在 V1.0 基础上新增 **250 行差异**，分四块：

### 2.1 新增头文件
```c
#include "xtime_l.h"      /* 64 位 Global Timer，COUNTS_PER_SECOND = 333,333,343 */
```

### 2.2 新增 ARM 软件 FIR 基准
```c
static float SwSineOut[SAMPLE_COUNT];
static float SwMixedOut[SAMPLE_COUNT];

static void sw_fir_filter(const float *x, int n, float *y)   /* 因果 FIR，越界历史视为 0 */
```
- 复用 `ReferenceCoeffs[51]`（已逐值核对与 HLS `h[51]` 完全一致，未重新编造系数）
- 输出写入全局数组，防止编译器优化掉计算
- 计时区间内**只有** `XTime_GetTime()` 与 `sw_fir_filter()`，无 UART/打印/文件操作
- 微秒换算在计时区间外完成

### 2.3 硬件流程封装为可复用函数
```c
static int hw_fir_run(const float *input);
```
- 每次调用都重新：填充 TxBuffer、清零 RxBuffer、双向 flush、`XFir_Set_N`、装载 RX、`XFir_Start`、装载 TX、忙等、invalidate Rx
- 返回原错误码（-5/-6/-7），失败即 `return -1`，**不会继续执行后续测试**

### 2.4 两组硬件测试 + 计时
```c
XTime_GetTime(&t_start);  hw_fir_run(SineInput);  XTime_GetTime(&t_end);
XTime_GetTime(&t_start);  hw_fir_run(MixedInput); XTime_GetTime(&t_end);
```

**新增变量（全部 `volatile`，供调试器读取）**：

| 变量 | 类型 | 含义 |
|---|---|---|
| `hw_sine_cycles` / `hw_mixed_cycles` | `u64` | 硬件端到端原始计数 |
| `hw_sine_us` / `hw_mixed_us` | `double` | 换算后微秒 |
| `sw_sine_cycles` / `sw_mixed_cycles` | `u64` | 软件纯计算原始计数 |
| `sw_sine_us` / `sw_mixed_us` | `double` | 换算后微秒 |
| `sw_sine_checksum` / `sw_mixed_checksum` | `float` | 软件输出校验和（防优化） |
| `sw_sine_out0` / `sw_mixed_out0` | `float` | 软件首样本输出 |

**状态码扩展**：`1` 初始化 → `2` 两组硬件完成 → `3` 软件计时中 → `4` 全部完成。
> 注意：性能版中 `2` 的语义已从"单次 DMA 完成"扩展为"两组硬件完成"，解读旧日志时需留意。

---

## 3. 计时口径差异（**引用加速比时必须注明**）

| | 硬件端到端（`hw_*_us`） | 软件纯计算（`sw_*_us`） |
|---|---|---|
| 起点 | `hw_fir_run()` 调用前（含输入准备前） | 进入 `sw_fir_filter()` 前 |
| 终点 | 输出 cache invalidate 完成 | 循环结束 |
| 包含 | 1000 次 float 拷贝、双向 cache flush、DMA 装载、FIR 处理、忙等、RX invalidate | **仅** 51×1000 次乘加循环 |
| 不含 | UART、打印、文件 I/O | 缓存维护、内存拷贝、任何 IO |
| 编译选项 | — | `-O0`（未优化） |
| 实测（正弦） | **96.2880 µs**（32,096 计数） | **2469.3239 µs**（823,108 计数） |
| 实测（混频） | **95.5110 µs**（31,837 计数） | **2468.7209 µs**（822,907 计数） |

因此：
- 对照比 **正弦 25.64 倍、混频 25.85 倍** = 同组输入的软件纯计算 ÷ 硬件端到端。
- 这是一个**偏保守**的对照（硬件侧含 CPU 侧准备工作）；若只比较纯计算核，硬件优势更大。
- 软件侧为 `-O0`，若换 `-O2/-O3` 软件基准会变快、对照比会下降——引用时须注明"软件基线为 -O0、单核 A9"。
- **数据来源**：上表 4 组数值来自**同一次完整板测**（报告图 12 截图对应运行，SDK Expressions 8 变量同屏读取，截图存于 `04_Test_Evidence/screenshots/`）。10-24 当天另有两次独立运行：XSCT 日志【一】（sw 823,720 → 2471.1599 µs）与日志【三】（hw 96.3210/95.4480 µs），差异均 < 0.5%，详见 `04_Test_Evidence/logs/性能测试原始日志_恢复_20261024.txt` 的勘误注记。

---

## 4. 数值结果（两版共用同一硬件）

| 项 | 值 | 说明 |
|---|---|---|
| 误差 | **约 2×10⁻⁶** | 24 位定点量化 + float 往返；1000 点中最大绝对误差量级如此，**不是严格零误差** |
| 对拍方法 | Python 独立实现同 51 系数因果 FIR | 逐点比对，两组各 1000 点 |
| 是否板上校验 | 否（离线导出后比对） | 板内仅读 `first_output`，无在线误差计算 |

---

## 5. 为什么两个版本都要提交

1. **可追溯**：V1.0 是性能版的基础，评审可看清"先功能后性能"的迭代路径。
2. **可复算**：性能版的 `main.c` 已覆盖原 SDK 工程里的 V1.0 文件（原文件仅存于备份），若只交一份，V1.0 状态将永久丢失。
3. **避免误读**：V1.0 的 `test_status=2` 与性能版的 `test_status=2` 语义不同，两版并列可防止混淆。

> 原工程 `sdk_workspace\fir_test\src\main.c` **当前内容即性能版**（MD5 `51ba9aee…`），V1.0 原文只保留了备份副本——本提交包中的 `main_v1.0.c` 就是那份备份的复制，内容一字未改。

---

## 6. 硬件侧版本说明

| 项 | 版本 |
|---|---|
| Bitstream | `fir_system_wrapper.bit`（2026-10-27 21:22，4,045,678 B）— 与 10-24 板测所用设计**逐字节比对仅 5 字节 ASCII 头时间戳不同，配置数据完全一致**（已核实） |
| HDF | 2026-10-24 11:06（671,591 B） |
| HLS 解决方案 | `solution1`（`ii=25版本` 之后，最后一次 export 2026-10-20 21:16） |
| HLS git 提交 | `d71deb5 ii=25版本`、`5533e32 Week 1: FIR simulation passed and initial synthesis`（仅在原工程 `.git`，未纳入提交包） |

> HLS 工程工作区存在未提交改动（`fir.cpp`、`fir_test.cpp`、`script.tcl` 等 13 项 modified）——提交包中的文件是**工作区当前实际使用的版本**，而非 git HEAD 版本。
