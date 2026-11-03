# QUALITY_CHECK_REPORT — 提交前质量检查

- 检查对象：`D:\vivado_file\Zynq7000_FIR_Submission`
- 检查时间：2026-11-02
- 检查方式：**只读核对**（解析源码/报告/工程文件/二进制），并**新生成** 1 个独立验证脚本
- 本阶段未做的事：未修改原始工程、未移动/删除任何提交文件、未重新生成工程、未上传、未压缩
- 本次仅新增 2 个文件：
  - `05_Docs/compare.py`（独立误差复算脚本，纯标准库）
  - `QUALITY_CHECK_REPORT.md`（本报告）

---

## 0. 结论摘要

> **⚠️ 2026-11-03 勘误（重要）**：本报告 §3 **P1-1 的结论有误，现予更正**。
> 当时的判断"823,720 计数应换算为 2471.1599 µs、文档 2469.3239 是算术错误"**不成立**。
> 真实情况：日志中保存了 `sw_sine_us` 的**完整 64 位双精度内存值**，解码后证实：
> - 运行【一】(10-24 18:31)：`sw_sine_cycles`=823,720，`sw_sine_us` 双精度值解码 = **2471.1599 µs**（两者自洽）；
> - 运行【三】(10-24 19:40) 与报告图12截图运行：`sw_sine_us` = **2469.3239 µs**（= 823,108 计数，自洽）。
> 即 **2471.1599 与 2469.3239 是两次不同运行的真实结果**，此前文档的错误仅在于把【一】的计数与【三】的微秒**混配成一对**。
> 最终定版采用**图12截图对应运行**（8 变量同屏、自洽）：hw 96.2880/95.5110 µs，sw 2469.3239/2468.7209 µs，对照比 25.64/25.85。详见 `04_Test_Evidence/logs/性能测试原始日志_恢复_20261024.txt` 文末【五】勘误注记。

| 项 | 结论 |
|---|---|
| 材料主体是否完整 | **基本完整**：HLS 源码/IP 导出、Vivado 工程/BD/bit/HDF、SDK 源码/驱动/平台、测试证据、文档 5 大类齐全 |
| 硬件数据是否可信 | **可信**：时序全部满足（WNS +8.855 / WHS +0.036，TNS/THS=0），DRC 无 Critical/Error，bit 与 HDF 同批构建 |
| 数值误差是否可复算 | **可以复算**：本次落盘 `compare.py`，实测最大绝对误差 **2.19×10⁻⁶（正弦）/ 2.98×10⁻⁶（混频）**，与"约 2×10⁻⁶"量级一致 |
| 是否可直接压缩提交 | **有条件具备**，但需先处理 4 项 P1（见 §3），其中 2 项属文档措辞、2 项属缺失文件/路径声明 |
| 是否有阻断性（P0）缺陷 | **无**。不存在伪造数据、无源可查的结论、或坏文件 |

**一句话**：成果与数据站得住，问题集中在"数字口径"和"复现声明"两处，改文档 + 补 2 个小文件即可提交。

---

## 1. 检查通过的项目

### 1.1 HLS 加速器（`01_HLS_Accelerator/`）

| 检查点 | 结果 | 证据 |
|---|---|---|
| 51 抽头 | ✅ | `fir.cpp` `#define N_TAPS 51`，`h[51]` 实际 51 个元素（脚本计数） |
| 对称线性相位 | ✅ | `h[i] == h[50-i]` 逐值检查通过；中心 `h[25]=0.04737780`；首尾为 0 |
| 数据类型 | ✅ | `data_t=ap_fixed<24,4>`、`coeff_t=ap_fixed<24,2>`、`accum_t=ap_fixed<40,8>`、`product_t=ap_fixed<48,8>` |
| AXI 接口 | ✅ | `#pragma HLS INTERFACE axis port=in/out`；`s_axilite port=N bundle=CTRL` 与 `port=return bundle=CTRL`；`component.xml` 中 `in_r`/`out_r` 为 `axis_rtl`、`s_axi_CTRL` 为 AXI4-Lite、参数 `N` 存在 |
| II = 1 证据 | ✅ | `fir_csynth.rpt`：`Loop 1`，Iteration Latency 10，**achieved 1 / target 1**，`Pipelined=yes` |
| 时钟估计 | ✅ | `ap_clk` target 10.00 ns / estimated **8.705 ns** / uncertainty 1.25 |
| HLS 资源 | ✅ | BRAM 2、DSP 25、FF 3 447、LUT 3 842（与 README 表一致） |
| C 仿真 1000 点通过 | ✅ | `fir_csim.log`：`Samples compared: 1000`、`Max absolute error: 6.13928e-006`、`Failed checks: 0`、`TEST PASS!`，`CSim done with 0 errors` |
| testbench 逻辑 | ✅ | 1000 点比对 + 容差 1e-3 + TLAST 校验；超出容差点会打印前 10 条 |
| 导出 IP 齐全 | ✅ | `component.xml`、`xilinx_com_hls_fir_1_0.zip`（39 项，含 hdl/verilog、hdl/vhdl、drivers、doc、bd/bd.tcl、xgui）、`constraints/fir_ooc.xdc` |
| xfir 驱动 | ✅ | 5 个源文件（`xfir.c/h/hw.h/linux.c/sinit.c`）+ `Makefile` + `fir.mdd` + `fir.tcl`；与 `03_SDK_Software/hw_platform/drivers/...` 中 `xfir.h` MD5 完全一致（`6d74a1c9…`） |

### 1.2 Vivado 硬件（`02_Vivado_Hardware/`）

| 检查点 | 结果 | 证据 |
|---|---|---|
| Block Design | ✅ | `fir_system.bd`(18 894 B) + `bxml`(5 879 B，XML 完整闭合) + `hwh`(312 778 B) + `bd.tcl`(11 486 B 内嵌于 HDF) |
| 8 个 XCI | ✅ | `axi_dma:7.1`、`hls:fir:1.0`、`processing_system7:5.5`、`smartconnect:1.0`、`axi_interconnect:2.1`、`proc_sys_reset:5.0`、`axi_protocol_converter:2.1`、`axi_crossbar:2.1` |
| wrapper | ✅ | `fir_system_wrapper.v`，生成时间 2026-10-24 11:02:10，端口为 DDR/FIXED_IO |
| FIR 接口 | ✅ | `axi_dma_0/M_AXIS_MM2S → fir_0/in_r`；`fir_0/out_r → axi_dma_0/S_AXIS_S2MM`；`ps7_0_axi_periph/M01_AXI → fir_0/s_axi_CTRL` |
| DMA 接口 | ✅ | `M_AXI_MM2S → axi_smc/S00_AXI`、`M_AXI_S2MM → axi_smc/S01_AXI`、`axi_smc/M00_AXI → PS/S_AXI_HP0`、`M00_AXI → DMA/S_AXI_LITE` |
| DMA 配置 | ✅ | `C_INCLUDE_SG=0`（Simple）、MM2S/S2MM TDATA 均 32 bit、多通道关闭 |
| PS 配置 | ✅ | `PCW_USE_S_AXI_HP0=1`；`FCLK_CLK0` 同时驱动 DMA/FIR/SmartConnect/互联/复位（单时钟域，无跨时钟） |
| 复位 | ✅ | `rst_ps7_0_50M` 统一分发，`slowest_sync_clk` 接 FCLK_CLK0 |
| XDC | ⚠️ 说明 | `constrs_1` FileSet **为空**，包内仅有 `bd/fir_system_ooc.xdc`（BD 自动生成的 OOC 约束）。PS 设计的时钟/引脚由 `processing_system7` IP 自动约束，**功能上不缺**；但若评审要求"板级引脚约束文件"，需在文档中说明"本设计无自定义引脚约束" |
| bitstream | ✅ | `output/fir_system_wrapper.bit` 4 045 678 B，头 `7z020clg400`、`Version=2019.1` |
| HDF | ✅ | 671 591 B，内含 `sysdef.xml`、`fir_system.hwh`(312 778，与 bd 目录同尺寸)、`ps7_init.c/h/tcl`、`pw` 驱动、`fir_system_wrapper.bit`(4 045 678) |
| HDF 双份一致 | ✅ | `02/output/*.hdf` 与 `03/hw_platform/system.hdf` MD5 相同（`ae9bf3a4…`） |
| 时序 | ✅ | **WNS +8.855 ns、TNS 0.000、WHS +0.036 ns、THS 0.000**，26 520 endpoints，0 failing，`All user specified timing constraints are met` |
| 资源 | ✅ | Slice LUT 7 084(13.32%)、Slice Register 8 010(7.53%)、Block RAM Tile 2(1.43%)、DSP 25(11.36%)、BUFG 1 |
| DRC | ✅ | 58 项全部为 **Warning/Advisory**（DPIP-1 22、DPOP-1 9、DPOP-2 25、REQP-181 2），**无 Critical/Error**，不阻断生成 bit |
| 实现时钟 | ⚠️ 见 P2-2 | `clk_fpga_0` 周期 **20.000 ns → 50 MHz**（不是 HLS 目标的 10 ns） |

### 1.3 SDK 软件（`03_SDK_Software/`）

| 检查点 | 结果 | 证据 |
|---|---|---|
| `main.c`（性能版） | ✅ | 326 行，MD5 `51ba9aeeb89a1b79ac9e0ee58c67788a`，含 `xtime_l.h`、`XTime_GetTime`、`sw_fir_filter`、`hw_fir_run`、8 个计时变量全 `volatile`、状态机 1→2→3→4 |
| `main_v1.0.c`（基线） | ✅ | 198 行 / 4 682 B，MD5 `fe8ef6b440a14de2b4fc2c6a66ab7f1b`，**命名保留**，与 `VERSION_NOTES.md` 声明完全一致 |
| 两版说明准确性 | ✅ | 行数/大小/MD5/测试组数/状态码语义/计时口径 全部与代码实际行为一致（逐条核对） |
| BSP 配置 | ✅ | `system.mss`：standalone 7.0、`ps7_cortexa9_0`、`axidma 9.9`、**`fir 1.0` 挂在 `fir_0`**、stdin/stdout = coresight |
| 硬件平台 | ✅ | `system.hdf`、`ps7_init.c/h/tcl`、`ps7_init_gpl.c/h`、`drivers/fir_v1_0/`、`fir_system_wrapper.bit` 共 7 类齐全 → **自包含成立** |
| 三个 ELF | ✅ 未擅定 | 仍在 `_PENDING/elf_candidates/`，未纳入正式目录，未选版 |

### 1.4 测试证据（`04_Test_Evidence/`）

| 检查点 | 结果 | 证据 |
|---|---|---|
| BIN 格式 | ✅ 已确证 | 5 个文件均 **4 000 B = 1000 × float32 小端**（非猜测：`cmp` 值与 hex 文本逐字对应） |
| HEX/TXT 格式 | ✅ 已确证 | `dumps/*.txt` 各 1000 行、每行 8 位 hex = 该样本 32 位字本身；转小端 float32 后与对应 `.bin` **逐字节完全一致**（脚本校验 3 组） |
| BIN ↔ TXT ↔ 日志对应 | ✅ | `sine_dump.txt ↔ fir_sine_fpga_1000.bin`、`mixed_dump.txt / mixed_dump_clean.txt ↔ fir_mixed_fpga_1000.bin` 全部对上 |
| 性能版 BIN 与 V1.0 BIN | ✅ | `fir_*_perf_1000.bin` 与 `fir_*_fpga_1000.bin` **MD5 完全相同** → 硬件确定性行为，同一输入必得同一输出，非重复导出错误 |
| 误差可复算 | ✅ 已复算 | 见 §2，`compare.py` 可直接重跑 |
| 冲激响应 | ✅ | 前 51 点与 `h[]` 最大偏差 **2.324×10⁻⁷**，符合"输出≈系数"的预期 |

### 1.5 文档（`README.md`、`05_Docs/`）

| 检查点 | 结果 | 证据 |
|---|---|---|
| README 路径/文件名 | ✅ | 所有 `0X_*/...` 相对路径均实际存在；无指向不存在文件的链接 |
| 时序/资源数字 | ✅ | 与 `timing_summary_routed.rpt`、`utilization_placed.rpt` 逐项一致 |
| HLS 数字 | ✅ | 与 `fir_csynth.rpt`、`fir_csim.log` 逐项一致 |
| 加速比口径 | ✅ | 明确写出"软件纯计算 `-O0` ÷ 硬件端到端"，并说明"口径不同须注明"，未夸大 |
| 误差表述 | ✅ 量级正确 | "约 2×10⁻⁶" 与实测 2.19~2.98×10⁻⁶ 相符；并明确"不是严格零误差" |
| 未验证声明 | ✅ | 已明确写"本副本未做过独立于原工程的重新构建验证""不宣称可一键复现" —— 措辞合规，无过度声明 |

---

## 2. 独立复算结果（`05_Docs/compare.py`）

脚本设计（不依赖 numpy / Xilinx 工具，纯标准库）：

- 输入：解析 `fir_test_inputs.h` 的 `SineInput`/`MixedInput`（1000 点，float32 舍入）
- 系数：解析 `fir.cpp` 的 `h[51]`
- 参考模型：输入按 `ap_fixed<24,4>`（2⁻²⁰）、系数按 `ap_fixed<24,2>`（2⁻²²）量化 → float64 累加 → float32 输出
- 比对：与 `output/*.bin` 逐点算绝对误差

实测输出：

| 组 | 最大绝对误差 | 出现位置 | 平均绝对误差 | >1e-3 点数 | dump 一致性 |
|---|---|---|---|---|---|
| 正弦 / V1.0 板测 | **2.194196×10⁻⁶** | idx 50 | 1.157701×10⁻⁶ | 0 | ✅ 逐字一致 |
| 混频 / V1.0 板测 | **2.980232×10⁻⁶** | idx 48 | 1.495614×10⁻⁶ | 0 | ✅ 逐字一致 |
| 正弦 / 性能版 | 2.194196×10⁻⁶ | idx 50 | 1.157701×10⁻⁶ | 0 | — |
| 混频 / 性能版 | 2.980232×10⁻⁶ | idx 48 | 1.495614×10⁻⁶ | 0 | ✅ 逐字一致 |
| 冲激 vs `h[]` | 2.324133×10⁻⁷ | — | — | — | — |

**结论**：最大误差 **2.98×10⁻⁶**（混频），"约 2×10⁻⁶" 的量级表述成立；1000/1000 点全部远低于 1e-3 容差。**误差数字不是编造的，评审可自行重跑脚本复现。**

运行方式：

```
python 05_Docs/compare.py
```

---

## 3. 存在的问题

### P0 — 阻断性（无）

未发现伪造数据、坏文件、无据结论、或与源码矛盾的关键声明。

### P1 — 影响评审，建议提交前处理

**P1-1　软件基准微秒换算有算术错误（连带加速比）**

原始计数（权威，来自 `性能测试原始日志_恢复_20261024.txt`）：

| 变量 | 计数 | 按 `COUNTS_PER_SECOND=333 333 343` 正确换算 | 文档当前值 | 偏差 |
|---|---|---|---|---|
| `sw_sine_cycles` | 823 720 | **2 471.1599 µs** | 2 469.3239 µs | −1.84 µs（0.07%） |
| `sw_mixed_cycles` | 822 906 | **2 468.7179 µs** | 2 468.6969 µs | −0.02 µs |
| `hw_sine_cycles` | 32 107 | 96.3210 µs | 96.3210 µs | 0 ✅ |
| `hw_mixed_cycles` | 31 816 | 95.4480 µs | 95.4480 µs | 0 ✅ |

由此正弦加速比应为 **25.66×**（文档 25.64×），混频 **25.86×**（文档正确），总体"约 25.8 倍"**结论不变**。
> 该错误已扩散到 4 处：`README.md` L84/L87、`05_Docs/VERSION_NOTES.md` L109/L113、`05_Docs/PENDING_ITEMS.md` L17、恢复日志 L143。

**P1-2　SDK 目录改名 + 扁平化，导致工程文件里的相对路径失效**

| 原工程实际结构 | 提交包结构 | 后果 |
|---|---|---|
| `sdk_workspace/fir_test/src/{main.c, fir_test_inputs.h, lscript.ld, README.txt, Xilinx.spec}` | `03_SDK_Software/app/`（文件平铺到根） | `app/.cproject` 引用 `../src/lscript.ld` → **路径不存在**，链接脚本丢失 |
| `sdk_workspace/fir_test_bsp/` | `03_SDK_Software/bsp/` | `app/.cproject` 引用 `../../fir_test_bsp/ps7_cortexa9_0/{include,lib}` → **路径不存在**，头文件与库找不到 |
| `sdk_workspace/fir_system_wrapper_hw_platform_0/` | `03_SDK_Software/hw_platform/` | `.project` 内工程名仍为 `fir_system_wrapper_hw_platform_0`，Eclipse 按**工程名**解析（`bsp/.sdkproject` 也记此名），**此项可正常工作** |

结论：README §5 步骤 3"导入 → 按 system.mss 生成 BSP → 编译"在**当前目录结构下不能直接成立**，需手工改 include 路径与链接脚本。要么恢复原结构，要么在文档里写明"需修正 2 处路径"。
> 注：`.project`/`.cproject` 内**无任何绝对路径**（已确认 0 处），所以问题纯粹来自目录改名，修正成本很低。

**P1-3　HLS C 仿真依赖的 2 个数据文件未随包提供**

`fir_test.cpp` 用**绝对路径**读取：

```
D:\vivado_file\fir_hls_practice\solution1\data\input_signal.txt     (12 498 B，原始工程存在)
D:\vivado_file\fir_hls_practice\solution1\data\expected_output.txt  (12 476 B，原始工程存在)
```

两个文件在**原始工程里确实存在**（均已核实），但**提交包内没有** → 评审无法复跑 csim，`fir_csim.log` 变成"只能看不能验"。

**P1-4　HLS / Vivado 工程的路径指向包外**

| 文件 | 指向 | 包内是否存在 |
|---|---|---|
| `01/project/.project` | `D:/vivado_file/fir_hls/fir.cpp`、`fir_test.cpp` | ❌（但源码已在 `01/src/`，内容 MD5 与 `fir_hls/fir.cpp` 一致 `d1d0455d…`） |
| `02/prj/fir_zynq_system.xpr` | IP repo `../fir_hls/solution1/impl/ip` | ❌ |
| `02/prj/...xpr` | 自身路径 1 处（`D:/vivado_file/fir_zynq_system/fir_zynq_system.xpr`） | 仅影响工程自识别，不影响源文件解析 |
| `01/script/script.tcl` | `add_files fir_hls/fir.cpp`（相对上级目录） | ❌ 需改路径才能跑 |

README 已声明"绝对路径仍保留、不宣称一键复现"，但**未点明 IP repo 缺失**——这是打开 xpr 时最先弹出的错误。

### P2 — 建议修正（不影响结论）

| 编号 | 问题 | 位置 | 建议 |
|---|---|---|---|
| P2-1 | "乘法次数 25 次/样本（对称配对，中心抽头单独）"**自相矛盾**：实际是 25 对 + 1 个中心 = **26 次乘法**；HLS 报 DSP=25 是因为中心抽头 `h[25]` 为常数、乘法定数化后未占 DSP | `README.md` L71 | 改为"26 次乘法/样本（25 对对称 + 1 中心），映射 25 个 DSP48E" |
| P2-2 | 实现时钟为 **50 MHz**（`clk_fpga_0` 20 ns），文档只写了 HLS 目标 10 ns，读者易误认为 100 MHz | `README.md` §2 | 补一行"PL 实际运行 50 MHz（PS FCLK_CLK0），HLS 按 10 ns 约束综合，估计 8.705 ns，仍有提升空间" |
| P2-3 | DRC 58 项违规未在文档说明 | `README.md` §2 | 补"DRC 58 项均为 Warning/Advisory（DSP 流水建议），无 Critical/Error" |
| P2-4 | `FILE_MANIFEST.md` 统计失真：头部写"共 134 个文件"，实际 **139**（含 `compare.py` 为 140）；§04 写"15 文件/177 KB"，实际 **16/181 KB**；`05_Docs` **整章缺失** | `FILE_MANIFEST.md` L5/L148 | 重新生成统计行并补 05_Docs 章节（建议用脚本统计，避免再错） |
| P2-5 | 两个 bitstream 时间戳不同（`02/output` 为 10-27 21:22，`03/hw_platform` 为 10-24 11:06），易被质疑"不是同一次构建" | `VERSION_NOTES.md` L143 | **本次已核实**：两者逐字节仅差 **5 字节，且全部落在 ASCII 头的日期/时间字段**，配置数据完全一致 → 建议把"同源"升级为"逐字节比对仅头部时间戳不同" |
| P2-6 | C 仿真误差 **6.139×10⁻⁶** 与板上对拍 **2.19~2.98×10⁻⁶** 不同源（前者对比未量化 float 参考，后者对比定点参考），文档未区分，易被问"到底几个误差" | `README.md` §4 | 加一句"`fir_csim.log` 的 6.14×10⁻⁶ 为 C 仿真对未量化参考的偏差；板上对拍为 2.19/2.98×10⁻⁶，两者参考模型不同，不可混用" |
| P2-7 | `script.tcl` 含 `cosim_design`，但 `report/` 内**无 `fir_cosim.rpt`** → 协同仿真实际未产出证据 | `01/script/script.tcl` | **不要声称通过 C/RTL 协同仿真**；或在文档注明"cosim 脚本存在但未保留报告" |
| P2-8 | `_PENDING/` 目录内含 1.4 MB 且顶层可见，若误打包会带入无关内容 | 根目录 | 压缩时**明确排除**（用户已定：不纳入正式包） |

---

## 4. 必须补充的文件

按优先级：

| # | 文件 | 大小 | 来源/做法 | 缺失后果 |
|---|---|---|---|---|
| 1 | `input_signal.txt`、`expected_output.txt` | 12.5 KB × 2 | 原工程 `D:\vivado_file\fir_hls_practice\solution1\data\` 直接复制到 `01_HLS_Accelerator/data/`，并把 `fir_test.cpp` 的两处绝对路径改为相对路径 | csim 无法复跑，"1000 点通过"只能看日志 |
| 2 | 性能测试截图（SDK Expressions，`test_status=4`） | — | 重新下板运行 5 s → Suspend → 截图（**不要在计时区间内停顿**） | 加速比数据缺少可视化背书（PENDING A-1） |
| 3 | 项目报告 / 答辩 PPT / 演示视频 | — | 待编写 | 参赛材料完整性（PENDING A-3） |
| 4 | `fir_impulse_fpga.csv`（可选） | ~30 KB | 由 `fir_impulse_fpga_1000.bin` 转换 | 仅影响"清单曾列但未生成"的一致性问题 |
| 5 | ELF 定版（3 选 1） | — | 需人工确认（建议 ① `29119d69…`，唯一有板上实测背书） | 无法提供"实测所用固件" |

---

## 5. 建议修改的文档（精确到行）

| # | 文件 | 位置 | 现状 | 建议 |
|---|---|---|---|---|
| 1 | `README.md` | L84 | `2469.3239 µs`（823,720 计数） | `2471.1599 µs` |
| 2 | `README.md` | L87 | 正弦 `25.64×` | `25.66×`（总体"约 25.8 倍"不变） |
| 3 | `README.md` | L71 | 乘法 25 次 | 26 次（25 对 + 中心），映射 25 DSP |
| 4 | `README.md` | §2 末 | 无时钟频率 | 补"PL 50 MHz"与 DRC 说明 |
| 5 | `README.md` | §4 误差说明 | 仅"约 2×10⁻⁶" | 补一句区分 csim 6.14×10⁻⁶ 与板上 2.19/2.98×10⁻⁶ |
| 6 | `README.md` | §5 步骤 1/3 | "直接打开/导入即可" | 补"SDK 目录已改名+扁平化，导入后需修正 `../src/lscript.ld` 与 `../../fir_test_bsp/...` 两处路径"；注明 IP repo 指向包外 |
| 7 | `05_Docs/VERSION_NOTES.md` | L109、L113 | 同上数值 | 同步 2 471.1599 / 25.66× |
| 8 | `05_Docs/PENDING_ITEMS.md` | L17 | `sw_sine_us≈2469.3` | `≈2471.2` |
| 9 | `05_Docs/PENDING_ITEMS.md` | A-4 | "误差脚本未落盘" | **已解决**：改为"见 `05_Docs/compare.py`，实测 2.19/2.98×10⁻⁶" |
| 10 | `05_Docs/FILE_MANIFEST.md` | L5、L148 | 134 / 15 文件 | 139（含本报告与脚本为 141）/ 16，并补 05_Docs 章节 |
| 11 | `05_Docs/VERSION_NOTES.md` | L143 | "与 10-24 板测同源" | 升级为"逐字节比对仅 5 字节头部时间戳不同，配置数据一致"（已验证） |
| 12 | `04_Test_Evidence/logs/性能测试原始日志_恢复_20261024.txt` | L143 | `823720 -> 2469.3239 us` | **不建议改原始记录**，加一行勘误注记："换算应为 2471.1599 µs；原文 2469.3239 系换算笔误" |

---

## 6. 是否具备正式压缩提交条件

**具备，但需先完成 3 件事（约 1 小时内可完成）：**

1. **改数字**（P1-1）：4 处 `2469.3239 → 2471.1599`、`25.64× → 25.66×`。这是硬错误，评审拿计数器一除就能发现。
2. **补 csim 数据文件**（P1-3）：2 个 txt + `fir_test.cpp` 改相对路径。否则"1000 点 TEST PASS"无法自证。
3. **改复现声明**（P1-2/P1-4）：要么恢复 SDK 原结构（`fir_test/src/` + `fir_test_bsp/`），要么在 README 写明"导入后需修正 2 处相对路径 + 添加 IP repo"。二者选其一，**不要保留当前"导入即可编译"的暗示**。

**不影响压缩、但应在提交前定的事：**

- 三个 ELF 定版（B-1，建议 ①）
- 性能测试截图（A-1）——若时间实在来不及，至少保证正文不出现"有截图为证"之类表述
- 压缩时排除 `_PENDING/`（1.4 MB）

**以下事项本阶段未做、也不建议现在做：**

- 不重新生成 Vivado/HLS 工程（会破坏"实测 bit 与报告同批"的证据链）
- 不修 xpr/HLS 的绝对路径（改动后 bit 与报告可能不再对应；宁可如实声明"归档副本"）
- 不擅自决定 ELF 版本

---

## 7. 附录：本次核对的关键原始数据

```
器件/工具        xc7z020clg400-2 / Vivado 2019.1 / HLS 2019.1 / SDK 2019.1
HLS 时钟         10.00 ns 目标，8.705 ns 估计，uncertainty 1.25
HLS 循环         Loop 1: iteration latency 10, II achieved 1 / target 1, pipelined yes
HLS 资源         BRAM 2 / DSP 25 / FF 3447 / LUT 3842
csim             1000 samples, max 6.13928e-6, mean 3.01009e-6, failed 0, TEST PASS
实现时序         WNS 8.855 / TNS 0.000 / WHS 0.036 / THS 0.000，26520 endpoints，全 MET
实现时钟         clk_fpga_0，20.000 ns（50 MHz）
实现资源         LUT 7084(13.32%) / FF 8010(7.53%) / BRAM 2(1.43%) / DSP 25(11.36%)
DRC              58 项，全 Warning/Advisory（DPIP-1 22、DPOP-1 9、DPOP-2 25、REQP-181 2）
bit              4045678 B，2026-10-27 21:22:16，与 10-24 版本仅 5 字节头差异
HDF              671591 B，内含 bit + hwh(312778) + ps7_init.* + fir 驱动
板测（10-24）    hw_sine 32107 → 96.3210 µs；hw_mixed 31816 → 95.4480 µs
                 sw_sine 823720 → 2471.1599 µs；sw_mixed 822906 → 2468.7179 µs
复算误差         正弦 2.194e-6（均值 1.158e-6）；混频 2.980e-6（均值 1.496e-6）
文件规模         139 文件（不含本报告与 compare.py）/ 约 14 MB
```
