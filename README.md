# 基于 Zynq-7000 的 51 抽头 FIR 滤波器（AMD FPGA 创新赛道参赛提交）

Zynq-7020（`xc7z020clg400-2`）上的软硬件协同 FIR 滤波器：
**ARM Cortex-A9 负责控制与软件基准，PL 侧 FIR 由 Vivado HLS 生成，数据经 AXI DMA 以 AXI4-Stream 直连加速器。**

- 工具链：Vivado 2019.1 / Vivado HLS 2019.1 / Xilinx SDK 2019.1
- 目标器件：`xc7z020clg400-2`
- 加速器：51 抽头、对称线性相位、24 位定点、**II = 1**
- 数据通路：DDR → AXI DMA(MM2S) → FIR(HLS) → AXI DMA(S2MM) → DDR，全程 AXI4-Stream，无 CPU 参与搬运

---

## 1. 目录结构

```
Zynq7000_FIR_Submission/
├─ README.md                     ← 本文件
├─ 01_HLS_Accelerator/           HLS 加速器工程
│   ├─ src/                      fir.cpp（算法）、fir_test.cpp（C 仿真 testbench）
│   ├─ project/                  HLS GUI 工程配置（.project/.cproject/.settings/vivado_hls.app）
│   ├─ script/                   script.tcl（构建脚本）、directives.tcl、solution1_data.json
│   ├─ report/                   fir_csynth.rpt/.xml（II、时序、资源）、fir_csim.log（TEST PASS）、solution1.log
│   └─ ip_export/                导出 IP：component.xml、xilinx_com_hls_fir_1_0.zip、hdl/、drivers/
├─ 02_Vivado_Hardware/           Vivado 硬件工程
│   ├─ prj/                      fir_zynq_system.xpr
│   ├─ bd/                       fir_system.bd/.bxml、fir_system_wrapper.v、fir_system_ooc.xdc、fir_system_bd.tcl、fir_system.hwh
│   ├─ ip_config/                8 个 *.xci（DMA / FIR / PS7 / 互联 / SmartConnect / 复位 / auto_pc / xbar）
│   ├─ output/                   fir_system_wrapper.bit、fir_system_wrapper.hdf
│   └─ report/                   timing_summary / utilization / drc / clock_utilization
├─ 03_SDK_Software/              SDK 软件工程（与原 sdk_workspace 同构）
│   ├─ fir_test/                 应用工程（.project/.cproject）
│   │   └─ src/                  main.c（性能版）、main_v1.0.c（V1.0 基线）、fir_test_inputs.h、lscript.ld
│   ├─ fir_test_bsp/             BSP 工程配置（system.mss 等，BSP 源码由 SDK 按 mss 生成）
│   └─ fir_system_wrapper_hw_platform_0/  硬件平台：system.hdf、ps7_init.*、drivers/fir_v1_0（xfir 驱动）
├─ 04_Test_Evidence/             测试证据
│   ├─ input/                    输入数据说明（数据本体在 fir_test_inputs.h 中）
│   ├─ output/                   5 个 1000 点输出 .bin
│   ├─ logs/                     测试结果说明、性能测试原始日志（XSCT 恢复）、板测脚本
│   ├─ dumps/                    JTAG 逐字读取的 1000 点原始 hex
│   └─ screenshots/              V1.0 功能测试截图
├─ 05_Docs/                      FILE_MANIFEST.md、VERSION_NOTES.md、PENDING_ITEMS.md
└─ _PENDING/                     待人工确认项（3 个 ELF 候选、2 个独立 FIR IP 实例）
```

---

## 2. 硬件架构

```
                 ┌──────────────── Zynq-7020 PS ────────────────┐
 DDR (HP0) ◄────►│ AXI DMA (Simple 模式, AXIS 32bit)            │
                 │   MM2S ──► fir_0/in_r                        │
                 │   S2MM ◄── fir_0/out_r                       │
                 │ M_AXI_GP0 ──► 互联 ──┬─► DMA/S_AXI_LITE       │
                 │                      └─► fir_0/s_axi_CTRL     │
                 └──────────────────────────────────────────────┘
   fir_0 = xilinx.com:hls:fir:1.0（HLS 导出 IP，51 抽头）
```

- DMA：`C_INCLUDE_SG = 0`（Simple 模式）、`C_M_AXIS_MM2S_TDATA_WIDTH = 32`、`C_S_AXIS_S2MM_TDATA_WIDTH = 32`，双向通道均启用
- PS：`PCW_USE_S_AXI_HP0 = 1`，单时钟 `FCLK_CLK0 = 50 MHz`（周期 20 ns，见 timing report Clock Summary）全域同步，复位由 `proc_sys_reset` 统一分发
- 实现结果：**WNS +8.855 ns / WHS +0.036 ns，TNS/THS = 0，所有时序约束满足**
- 资源：LUT 7,084 (13.32%)、FF 8,010 (7.53%)、BRAM 2 (1.43%)、DSP 25 (11.36%)

## 3. 加速器实现要点

| 项目 | 值 | 出处 |
|---|---|---|
| 抽头数 | 51（`N_TAPS`） | `fir.cpp` |
| 系数类型 | `ap_fixed<24,2> h[51]`，偶对称线性相位 | `fir.cpp` |
| 数据类型 | 输入 `ap_fixed<24,4>`、累加 `ap_fixed<40,8>`、乘积 `ap_fixed<48,8>` | `fir.cpp` |
| 乘法次数 | 26 次/样本（25 次对称配对 + 1 次中心抽头），综合后映射 25 个 DSP48E（中心抽头系数为常数，未占 DSP） | `fir.cpp` |
| 循环 II | **achieved 1 / target 1** | `fir_csynth.rpt` |
| 时钟 | 目标 10.00 ns，估计 8.705 ns | `fir_csynth.rpt` |
| HLS 资源 | BRAM 2、DSP 25、FF 3,447、LUT 3,842 | `fir_csynth.rpt` |
| C 仿真 | `Samples compared: 1000`、`Failed checks: 0`、`TEST PASS!` | `fir_csim.log` |
| 接口 | `axis` in/out（`ap_axiu<32,1,1,1>`）+ `s_axilite` 端口 `N`（bundle CTRL） | `fir.cpp` |

## 4. 实测结果（板上，2026-10-24）

**采用数据：报告图 12 截图对应的那次完整板测**——8 个计时变量在 SDK Expressions 中**同一次运行内**同屏读取（截图已存档于 `04_Test_Evidence/screenshots/性能测试_SDK_Expressions_20261024.png`），内部自洽：计数 ÷ `COUNTS_PER_SECOND` 与显示的 µs 值逐位吻合。

| 指标 | 数值 | 原始计数 | 口径 |
|---|---|---|---|
| 硬件端到端（正弦 1000 点） | **96.2880 µs** | 32,096 | 含输入准备、双向 cache 维护、DMA 启动、FIR、等待、输出 cache invalidate |
| 硬件端到端（混频 1000 点） | **95.5110 µs** | 31,837 | 同上 |
| 软件纯计算（正弦 1000 点） | **2469.3239 µs** | 823,108 | ARM A9 单核、`-O0`、纯 `sw_fir_filter()` 循环，不含打印 |
| 软件纯计算（混频 1000 点） | **2468.7209 µs** | 822,907 | 同上 |
| 数值误差 | **约 2×10⁻⁶**（混频最大 2.98×10⁻⁶、正弦 2.19×10⁻⁶） | — | `05_Docs/compare.py` 独立复算，1000/1000 点 |
| 对照比 | **正弦 25.64 倍、混频 25.85 倍** | — | 同组输入：软件纯计算 ÷ 硬件端到端 |
| 计数器基准 | `COUNTS_PER_SECOND = 333,333,343` | — | Global Timer = CPU 666.67 MHz / 2（BSP `xtime_l.h`） |

**历史运行记录（互为一致性验证，均真实存在、均未采用为主数据）**：

| 运行 | 时间 | hw 正弦 / 混频 | sw 正弦 / 混频 | 记录形式 |
|---|---|---|---|---|
| 【一】 | 10-24 18:31 | —（未测） | 823,720 → **2471.1599 µs** / 822,906 → 2468.7179 µs | XSCT mrd（日志【一】；该次运行 sw_sine_us 双精度内存值解码即为 2471.1599，与前版文档误配的 2469.32 无关） |
| 【三】 | 10-24 19:40 | 32,107 → 96.3210 µs / 31,816 → 95.4480 µs | 2469.3239 µs / 2468.6969 µs | XSCT mrd（日志【三】，"最终有效计时"） |
| **图12 截图（采用）** | 10-24 | 32,096 → 96.2880 µs / 31,837 → 95.5110 µs | 823,108 → 2469.3239 µs / 822,907 → 2468.7209 µs | SDK Expressions 同屏截图 |

各次干净运行的硬件耗时差异 < 0.5%，软件纯计算差异 < 0.1%，可重复性良好。

> **误差与对照比说明**
> - 误差为**约 2×10⁻⁶**，是 24 位定点系数量化与 float 往返转换的结果，**不是严格的零误差**；`fir_csim.log` 中的 6.14×10⁻⁶ 是 C 仿真对**未量化 float 参考**的偏差，与本表板上对拍（对**定点参考**）口径不同，不可混用。
> - 对照比 = 软件基准（纯计算，`-O0`，不含计时/打印开销）÷ 硬件端到端（含输入准备与 cache 维护的完整链路）。**两端口径不同，是"对照比"而非严格同口径加速比**，引用时须注明；若只看纯计算对比，硬件优势会被低估。

## 5. 复现步骤（需在 Xilinx 工具环境中操作）

1. **HLS**：打开 `01_HLS_Accelerator/project`，或直接用 `script/script.tcl` 重建 `solution1`（`csim → csynth → export_design`）。IP 已随包提供，可不重建。**注意**：`fir_test.cpp` 以绝对路径读取 `D:\vivado_file\fir_hls_practice\solution1\data\` 下的 `input_signal.txt` / `expected_output.txt`（两文件已随包存于 `01_HLS_Accelerator/data/`）；重跑 csim 前需将该目录恢复到原路径，或将 tb 中两处路径常量改为本地路径。
2. **Vivado**：打开 `02_Vivado_Hardware/prj/fir_zynq_system.xpr`。IP Repository 已指向包内相对路径 `$PPRDIR/../../01_HLS_Accelerator/ip_export`（即 HLS 导出 IP），`ip_config/` 中另有 8 个 xci、BD 可由 `bd/fir_system_bd.tcl` 脚本重建。Bitstream 已提供（`output/`），无需重跑实现。
3. **SDK**：新建 workspace，依次导入 `03_SDK_Software/` 下的 `fir_system_wrapper_hw_platform_0` → `fir_test_bsp` → `fir_test`（三者 `.project` 工程名与原工作区一致，相对引用 `../src/lscript.ld`、`../../fir_test_bsp/...` 已闭合）；按 `fir_test_bsp/system.mss` 生成 BSP 后编译 `fir_test` 下载。
4. **上板**：JTAG 下载 ELF，运行约 5 秒后 Suspend，在 Expressions 中观察 `test_status`（应为 4）、`hw_*_us`、`sw_*_us`（参考 `04_Test_Evidence/screenshots/性能测试_SDK_Expressions_20261024.png`）。

> ⚠️ **重要限制**：本目录是**源码与成果归档副本**。SDK 三个工程的 `.project` 名称与相对引用已恢复为与原 `sdk_workspace` 同构、Vivado IP repo 已改为包内相对路径，但 HLS `.project/.cproject` 与 `fir_test.cpp` 内部仍保留原始工程绝对路径（`D:\vivado_file\...`）。**本副本未做过"独立于原工程的重新构建验证"**，因此不宣称可一键复现；如需可独立打开的工程，需在副本内重新创建工程并重指源文件（见 `05_Docs/PENDING_ITEMS.md`）。

## 6. 文档索引

| 文档 | 内容 |
|---|---|
| `05_Docs/FILE_MANIFEST.md` | 每个文件的来源路径、大小、用途 |
| `05_Docs/VERSION_NOTES.md` | V1.0 与性能测试版的差异（代码、计时、结果） |
| `05_Docs/PENDING_ITEMS.md` | 缺失材料、待确认 ELF、待补 CSV/报告 |
| `05_Docs/compare.py` | 独立误差复算脚本（纯标准库，`python compare.py` 直接运行） |
| `05_Docs/FIR滤波器Zynq软硬件协同实现报告_修订版.docx` | 参赛技术报告（修订版） |
| `QUALITY_CHECK_REPORT.md` | 第三阶段质量检查报告（含性能数据来源核查） |

## 7. 已知缺口

- `fir_impulse_fpga.csv` 从未生成（bin 已提供，可由 `compare.py` 同款方法转换）
- 答辩 PPT / 演示视频 尚未提供
- 三个 `fir_test.elf` 版本待定版（见 `_PENDING/elf_candidates/`）

详见 `05_Docs/PENDING_ITEMS.md`。
