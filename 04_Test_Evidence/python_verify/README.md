# Python 验证程序说明（队友提供，已按实际代码整理）

本目录存放队友提供的 Python 侧验证程序，用于 **51 抽头 FIR 的 Golden 基准生成、板上输出比对与性能对照比计算**。
本目录 **不含** Vivado/HLS/SDK 硬件工程，硬件部分见 `01_HLS_Accelerator`、`02_Vivado_Hardware`、`03_SDK_Software`。

> **与 `readme.txt` 的关系**：`readme.txt` 是队友原始说明，**按原样保留**供溯源；其中"文件清单"一段与实际代码存在出入（见文末《勘误》），**以本 README 为准**。

---

## 1. 文件清单

| 文件 | 大小 | 作用 |
|---|---:|---|
| `fir_hw_verify.py` | 24.9 KB | 主程序，Jupyter 导出脚本，9 个 Cell：滤波器设计 → Golden 基准 → bin 解析 → 冲激/正弦/混频/性能组比对 |
| `signal_generate.py` | 1.2 KB | 早期信号生成（5 Hz 目标 + 50 Hz 干扰 + 高斯噪声），产出 `signal.npy/t.npy/clean.npy`；**仅用于前期设计调试，不是板上测试输入** |
| `readme.txt` | 1.6 KB | 队友原始说明（未改动，仅作溯源） |
| `README.md` | 本文件 | 按代码实际内容重写，含运行方法、参数、结论与勘误 |

两个 `.py` 内含 `# In[1]:` ~ `# In[9]:` 注释，是 `jupyter nbconvert --to python` 的导出产物，**不是独立应用**；按 Cell 顺序整体执行可跑通，单独执行某个 Cell 会因缺少上文变量报 `NameError`。

---

## 2. 依赖

| 依赖 | 用途 | 必需 |
|---|---|---|
| Python 3.x | 运行环境（原在 Jupyter Notebook 中执行） | 必需 |
| `numpy` | 数组、`savetxt/loadtxt` | 必需 |
| `scipy` | Cell 1 的 `firwin`（系数设计）、`lfilter`、`freqz` | 必需 |
| `matplotlib` | 全部绘图（12 处 `plt.show()`） | 必需 |
| `struct` | float32 ↔ 小端字节（AXI4-Stream TDATA 口径） | 标准库，无需安装 |

安装：`pip install numpy scipy matplotlib`（原工程未提供 `requirements.txt`，也未锁版本）

---

## 3. 运行方法

```bash
# 建议在独立临时工作目录中运行，避免把中间产物写进提交包
mkdir /tmp/fir_py_run && cd /tmp/fir_py_run
cp <包>/04_Test_Evidence/output/*.bin .
python <包>/04_Test_Evidence/python_verify/fir_hw_verify.py
```

- 脚本用**相对路径**读取 `*.bin`、`ref_*.csv`，所以必须在"bin 所在目录"下运行（或把 bin 复制到当前目录）。
- 运行顺序：Cell 1 → 2 → 3 → 4 → 5 → **6（先生成 `ref_*.csv` Golden）** → 7 → 8 → **9（性能组）**。
- Cell 1 依赖 `signal.npy / t.npy / clean.npy`（由 `signal_generate.py` 生成，**未随包提供**；若只关心 Cell 6~9 的板测比对，可跳过 Cell 1~5）。
- Cell 7/8/9 读取的 5 个 bin 均由板上导出，已随包在 `04_Test_Evidence/output/`：

| bin | 说明 |
|---|---|
| `fir_impulse_fpga_1000.bin` | 冲激激励（首点 1，其余 0） |
| `fir_sine_fpga_1000.bin` | 正弦激励（V1.0 功能验证） |
| `fir_mixed_fpga_1000.bin` | 混频激励（V1.0 功能验证） |
| `fir_sine_fpga_perf_1000.bin` | 正弦激励（性能测试版） |
| `fir_mixed_fpga_perf_1000.bin` | 混频激励（性能测试版） |

格式：**4000 字节 = 1000 × float32 小端**（已核实）。

- ⚠️ Cell 8/9 还要读 `ref_sine.csv`，但**脚本内没有生成该文件的代码**（Cell 6 只导出 `ref_mixed.csv`，正弦生成函数 `gen_sine_signal()` 处于注释状态）。复现正弦组时需自行调用 `gen_sine_signal()` 生成并另存为 `ref_sine.csv`，或直接用 `05_Docs/compare.py` 复算正弦参考值。
- Cell 6 会向当前目录写入 `input_mixed.txt`、`ref_mixed.csv`，请确保工作目录可写（建议用临时目录，避免写入提交包）。

---

## 4. 算法与参数（与硬件侧严格对齐）

| 项 | 值 | 说明 |
|---|---|---|
| 抽头数 | **51** | 奇数、线性相位、系数对称 |
| 设计方法 | `scipy.signal.firwin(51, cutoff=20, fs=1000, window='hamming')` | 低通，截止 20 Hz @ 1 kHz，保 5 Hz、抑 50 Hz |
| 系数 | 与 `01_HLS_Accelerator/src/fir.cpp` 的 `h[51]` **逐值一致**（8 位小数差 0.0，中心 `h[25]=0.04737780`） | 已复核：用 hamming-sinc 公式重算，与 `h[]` 差 4.98×10⁻⁹ |
| 初始条件 | **零填充**：`x[n<0] = 0`，输出保留全部 1000 点、**不做延迟裁剪** | 与 HLS 行为一致（Cell 2 的裁剪 25 点仅用于观察波形，作者已注明） |
| 数据格式 | 系数/输出 `float32`；累加为 Python float（≈float64） | 见第 6 节口径说明 |
| 测试激励 | 正弦 `sin(2π·50·n/1000)`；混频 `sin(2π·30·n/1000) + 0.5·sin(2π·200·n/1000)` | 与 `03_SDK_Software/fir_test/src/fir_test_inputs.h` 的 `SineInput / MixedInput` 逐点吻合（差 2.4×10⁻⁸ / 5.9×10⁻⁸，仅 float32 舍入） |

---

## 5. 实测结果（2026-10-24 最终板测）

数据取自 **SDK Expressions 同屏记录（技术报告图 12 那一次运行）**，计数基准 `COUNTS_PER_SECOND = 333,333,343`（Global Timer = CPU 666.67 MHz / 2）：

| 指标 | 正弦 | 混频 | 口径 |
|---|---:|---:|---|
| ARM 纯计算耗时 | 2469.3239 µs（823,108 计数） | 2468.7209 µs（822,907 计数） | Cortex-A9 单核、`-O0`，仅 `sw_fir_filter()` 循环 |
| FPGA 耗时 | 96.2880 µs（32,096 计数） | 95.5110 µs（31,837 计数） | **端到端**：缓存维护 + DMA 启动 + FIR 计算 + 传输完成 |
| 对照比 | **约 25.65** | **约 25.85** | ARM 纯计算 ÷ FPGA 端到端 |
| 最大绝对误差 | 1.86×10⁻⁶ | 2.09×10⁻⁶ | 本脚本浮点参考模型（见第 6 节） |

> **对照比为"非严格同口径"**：分子是纯计算，分母含 CPU 侧准备与 cache 维护开销。文档中一律称"对照比"，不称"加速比"。
> 上表的 4 个数值必须**同一次运行取用**，不可与其它运行的数值混配（混配会得到 25.64 / 25.86 这类偏差值）。

---

## 6. 误差计算口径（与 `05_Docs/compare.py` 的差异）

本脚本与提交包内独立的 `05_Docs/compare.py` **都能复算同一批 bin**，但参考模型不同，**结果不应被强行对齐**：

| 项 | 本脚本（`fir_hw_verify.py`） | `05_Docs/compare.py` |
|---|---|---|
| 系数 | `float32` 常量，**不量化** | 按 `ap_fixed<24,2>` 量化到 2⁻²² |
| 输入 | `float32`，**不量化** | 按 `ap_fixed<24,4>` 量化到 2⁻²⁰ |
| 累加 | Python float（≈float64） | Python float（≈float64） |
| 输出 | 舍入为 `float32` | 舍入为 `float32` |
| 依赖 | 需要 `numpy` | **纯标准库**，无第三方依赖 |
| 最大绝对误差（正弦/混频） | **1.86×10⁻⁶ / 2.09×10⁻⁶** | **2.19×10⁻⁶ / 2.98×10⁻⁶** |

**差异原因**：`compare.py` 额外模拟了 HLS 的定点量化（输入 2⁻²⁰、系数 2⁻²²），因此参考值本身带有量化台阶，与板上实测的偏差略大；本脚本用的是"理想浮点系数 + 高精度累加"，更接近数学真值。

**两者同为 10⁻⁶ 量级**，都支持技术报告中"最大绝对误差约 2×10⁻⁶"的表述。引用时必须注明用的是哪一个模型，**不可混用数值**。

---

## 7. 已知限制

1. 全部输出用 `plt.show()`，**不落盘 PNG**；无图形后端（headless）时不会产生图片。报告中的对拍图来自当时的同屏截图（已存于 `04_Test_Evidence/screenshots/`）。
2. Cell 9 的 4 个耗时是**人工录入的常量**，不从 bin 或日志读取；修改数据不会自动同步别处。
3. `signal_generate.py` 未设随机种子，`signal.npy` **不可精确复现**。
4. `ref_mixed.csv` 未随包提供，需先跑 Cell 6 生成（依赖内置系数，可离线重算）；`ref_sine.csv` **脚本内无生成代码**（需自行调用 `gen_sine_signal()`，详见第 3 节）。
5. `fir_zeropad()`、`bin_to_float_csv()`、`plot_compare()` 在不同 Cell 中重复定义（notebook 常见写法），三处实现一致。
6. 未随包提供 `.ipynb` 原件与 `requirements.txt`。
7. **原文件第 169 行存在语法错误**（`输出：output_software.csv` 缺 `#`），整脚本无法执行；本目录副本已补 `#` 修正，属唯一一处代码级改动，不涉及算法与口径。

---

## 8. 勘误：`readme.txt` 与实际代码的出入

| `readme.txt` 原文 | 实际情况 |
|---|---|
| "signal_generate.ipynb：生成正弦、混频输入信号，输出统一 51 抽头 FIR 滤波器系数、1000 点理论参考 Golden 结果" | `signal_generate.py` **只生成 5 Hz + 50 Hz + 噪声信号**并保存 `.npy`；**不生成系数、不生成 Golden、不生成混频信号**。系数与 Golden 实际在 `fir_hw_verify.py` 的 Cell 1 与 Cell 6 |
| 文件名为 `signal_generate.ipynb` / `fir_hw_verify.ipynb` | 包内提供的是 `.py` 导出脚本，**无 `.ipynb` 原件** |
| 性能组"对照比 25.64 / 25.86，最大误差 1.86e-6 / 2.09e-6" | 误差值正确；对照比的 25.64 / 25.86 来自**跨运行混配**，改为同一运行数据后为 **25.65 / 25.85**（本目录 `fir_hw_verify.py` 已按此更新，见第 5 节） |

> `readme.txt` 中关于**计时口径**的表述（"ARM 为纯计算耗时、FPGA 为端到端，因此称对照比而非严格同口径加速比"）**准确，可直接引用**。

---

## 9. 本目录副本的改动记录（相对队友原始文件）

除以下两处外，`fir_hw_verify.py` 与 `signal_generate.py` 与原始 RAR 内文件逐字节一致；`readme.txt` 未改动。

| 位置 | 改动前 | 改动后 | 原因 |
|---|---|---|---|
| 第 169 行（Cell 5） | `输出：output_software.csv` | `#输出：output_software.csv` | 原文件缺注释符，导致整脚本 `SyntaxError` 无法执行；补 `#` 恢复作者原意，不涉及逻辑 |
| 第 620–631 行（Cell 9） | `time_fpga_sine = 96.3210`<br>`time_arm_mixed = 2468.6969`<br>`time_fpga_mixed = 95.4480` | `96.2880`<br>`2468.7209`<br>`95.5110` | 原值为**跨运行混配**（FPGA 取自另一次运行），与"同一运行取数"原则冲突；改为技术报告图 12 那次运行的同组数据。`time_arm_sine = 2469.3239` 本就正确，未动 |

- **未改动**：误差计算公式、`fir_zeropad()`、bin 解析、绘图函数、系数数组、测试信号生成函数、Cell 1~8 的任何逻辑。
- 修改后对照比由公式自动算得 **25.65 / 25.85**（原为 25.64 / 25.86），与 README 第 5 节一致。
