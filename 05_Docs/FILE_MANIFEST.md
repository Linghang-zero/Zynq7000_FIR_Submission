# FILE_MANIFEST — 文件清单（来源路径 / 大小 / 用途）

- 生成时间：2026-11-02（2026-11-03 修订：更新统计、SDK 目录恢复原结构、增补 HLS 仿真数据/截图/技术报告，见文末"增补记录"）
- 复制方式：全部为 `cp -p` 单向复制（保留时间戳），**未对原工程做任何移动/删除/重命名/覆盖**
- 统计：正式提交包（不含 `_PENDING/`、`_work/`）共 **136 个文件**，合计 **约 14 MB**
- 路径缩写：
  - `HLS` = `D:\vivado_file\fir_hls`
  - `VIV` = `D:\vivado_file\fir_zynq_system`
  - `SDK` = `D:\vivado_file\fir_zynq_system\sdk_workspace`
  - `BAK` = `D:\FpGA备份\V1.0成果保存`
  - `PFB` = `D:\fp_perf_build`
  - `SUB` = `D:\vivado_file\Zynq7000_FIR_Submission`（本目录）

---

## 01_HLS_Accelerator（61 文件 / 934 KB，含 2026-11-03 增补的 data\ 2 个仿真数据文件）

### src — 算法源码（人工编写，**必须提交**）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `fir.cpp` | 3,180 B | `HLS\fir.cpp` | FIR 核心：`N_TAPS 51`、`ap_fixed<24,2> h[51]` 对称系数、4 种定点类型、AXIS 输入输出、`s_axilite N`、`PIPELINE II=1` |
| `fir_test.cpp` | 3,552 B | `HLS\fir_test.cpp` | C 仿真 testbench：1000 点输入/输出对比、打印 `Samples compared` |

### project — HLS 工程配置

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `.project` | 2,093 B | `HLS\.project` | Eclipse 风格工程描述 |
| `.cproject` | 34,062 B | `HLS\.cproject` | 编译配置（include 路径、宏、优化） |
| `.settings\language.settings.xml` | 2,649 B | `HLS\.settings\` | 语言/索引设置 |
| `.settings\fir_hls.Debug.launch` / `.Release.launch` | 2,016 / 2,020 B | 同上 | 运行配置 |
| `vivado_hls.app` | 585 B | `HLS\vivado_hls.app` | HLS 工程入口描述（GUI 打开用） |

### script — 构建脚本（**关键，可重建 solution1**）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `script.tcl` | 817 B | `HLS\solution1\script.tcl` | 完整流程：`set_top fir`、`xc7z020-clg400-2`、10 ns 时钟、csim→csynth→cosim→`export_design -format ip_catalog` |
| `directives.tcl` | 269 B | `HLS\solution1\directives.tcl` | 指令文件（空，自动生成） |
| `solution1.directive` | 90 B | 同目录 | 解决方案级指令 |
| `solution1.funcunit` | 588 B | 同目录 | 功能单元配置 |
| `solution1_data.json` | 20,417 B | 同目录 | 综合数据（时序/资源/II 的结构化记录） |

### report — 综合与仿真报告（**评审证据**）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `fir_csynth.rpt` | 43,692 B | `HLS\solution1\syn\report\` | 综合报告：时钟 10 ns / 估计 8.705 ns、**Loop 1 II achieved=1 target=1**、资源 BRAM2/DSP25/FF3447/LUT3842 |
| `fir_csynth.xml` | 11,752 B | 同上 | 同内容 XML 版 |
| `csynth.xml` | 11,752 B | 同上 | 综合结果 XML（Vivado 读取用） |
| `fir_csim.log` | 500 B | `HLS\solution1\csim\report\` | **C 仿真证据**：`Samples compared: 1000`、`Failed checks: 0`、`TEST PASS!` |
| `solution1.log` | 97,401 B | `HLS\solution1\` | csynth/export 全过程日志 |

### ip_export — 导出的 FIR IP（**Vivado 依赖，必须提交**）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `component.xml` | 85,164 B | `HLS\solution1\impl\ip\` | IP 元数据（VLNV `xilinx.com:hls:fir:1.0`、端口、参数、地址空间） |
| `xilinx_com_hls_fir_1_0.zip` | 76,833 B | 同上 | **IP 打包（可直接 add_repo / 导入 Vivado）** |
| `fir_info.xml` | 602 B | 同上 | IP 打包信息 |
| `auxiliary.xml` | 2,619 B | 同上 | 辅助元数据 |
| `hdl\verilog\fir.v` | 131,056 B | `...\ip\hdl\verilog\` | 生成的 FIR RTL（顶层） |
| `hdl\verilog\fir_CTRL_s_axi.v` | 9,861 B | 同上 | AXI4-Lite 控制寄存器（`N` 端口） |
| `hdl\verilog\fir_fpext_32ns_64bkb.v` | 1,654 B | 同上 | float 位重解释/转换模块 |
| `hdl\verilog\fir_mul_mul_11~19ns_*.v` | 各 688 B（9 个） | 同上 | 25 路对称配对所实例化的乘法器黑盒 |
| `hdl\vhdl\*.vhd` | 1,570–204,619 B（11 个） | `...\ip\hdl\vhdl\` | 同上的 VHDL 版本（IP 双语言发布） |
| `hdl\ip\fir_ap_fpext_0_no_dsp_32.vhd` | 13,515 B | `...\ip\hdl\ip\` | float 转换 IP 的 RTL |
| `drivers\fir_v1_0\src\xfir.c` | 5,083 B | `...\ip\drivers\fir_v1_0\src\` | **FIR 驱动**（`XFir_Start/Set_N/IsDone/IsIdle/DisableAutoRestart`） |
| `drivers\...\xfir.h` | 3,051 B | 同上 | 驱动头（SDK 编译必需） |
| `drivers\...\xfir_hw.h` | 1,403 B | 同上 | 寄存器偏移定义 |
| `drivers\...\xfir_sinit.c` | 1,046 B | 同上 | 静态初始化/查找 |
| `drivers\...\xfir_linux.c` | 4,611 B | 同上 | Linux 用户态版本（本项目未用） |
| `drivers\...\Makefile` | 746 B | 同上 | 驱动编译脚本 |
| `drivers\fir_v1_0\data\fir.mdd` / `fir.tcl` | 485 / 761 B | `...\drivers\fir_v1_0\data\` | 驱动元数据（BSP 生成时识别 IP） |
| `constraints\fir_ooc.xdc` | 397 B | `...\ip\constraints\` | IP OOC 约束 |
| `xgui\fir_v1_0.tcl` | 757 B | `...\ip\xgui\` | IP GUI 定制脚本 |
| `doc\ReleaseNotes.txt` | 387 B | `...\ip\doc\` | IP 发布说明 |
| `misc\logo.png` | 4,077 B | `...\ip\misc\` | IP 图标 |

---

## 02_Vivado_Hardware（21 文件 / 5.9 MB）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `prj\fir_zynq_system.xpr` | 27,391 B | `VIV\fir_zynq_system.xpr` | Vivado 工程（器件 `xc7z020clg400-2`，顶层 `fir_system_wrapper`） |
| `bd\fir_system.bd` | 18,894 B | `VIV\...\bd\fir_system\` | **Block Design 源文件**（6 实例：PS7 / AXI DMA / HLS FIR / 互联 / 复位 / SmartConnect） |
| `bd\fir_system.bxml` | 5,879 B | 同上 | BD 文本描述 |
| `bd\fir_system_wrapper.v` | 2,555 B | `...\bd\fir_system\hdl\` | **BD 包装（顶层 HDL）** |
| `bd\fir_system_ooc.xdc` | 653 B | `...\bd\fir_system\` | BD OOC 约束 |
| `bd\fir_system_bd.tcl` | 11,486 B | `...\bd\fir_system\hw_handoff\` | **BD 重建脚本**（无 GUI 也可复现设计） |
| `bd\fir_system.hwh` | 312,778 B | 同上 | 硬件描述（SDK 平台生成用） |
| `ip_config\fir_system_axi_dma_0_0.xci` | 65,866 B | `...\bd\fir_system\ip\` | **AXI DMA 配置**：Simple 模式（`C_INCLUDE_SG=0`）、MM2S/S2MM 各 32 bit、双向启用 |
| `ip_config\fir_system_fir_0_0.xci` | 16,702 B | 同上 | **HLS FIR IP 实例配置**（VLNV `xilinx.com:hls:fir:1.0`） |
| `ip_config\fir_system_processing_system7_0_0.xci` | 210,107 B | 同上 | **PS7 配置**：`S_AXI_HP0` 启用、DDR 1 GB 映射、FCLK_CLK0 |
| `ip_config\fir_system_ps7_0_axi_periph_0.xci` | 43,116 B | 同上 | AXI 互联（M00→DMA、M01→FIR） |
| `ip_config\fir_system_axi_smc_0.xci` | 32,912 B | 同上 | SmartConnect（DMA 主口→HP0） |
| `ip_config\fir_system_rst_ps7_0_50M_0.xci` | 9,027 B | 同上 | 处理器系统复位（100 MHz 域） |
| `ip_config\fir_system_auto_pc_0.xci` | 27,950 B | 同上 | 协议转换器（auto_pc） |
| `ip_config\fir_system_xbar_0.xci` | 397,079 B | 同上 | AXI Crossbar |
| `output\fir_system_wrapper.bit` | **4,045,678 B** | `VIV\fir_zynq_system.runs\impl_1\` | **最终 Bitstream**（2026-10-27 21:22，板测所用） |
| `output\fir_system_wrapper.hdf` | 671,591 B | `VIV\exported\` | **硬件导出（HDF）**，SDK 硬件平台来源 |
| `report\fir_system_wrapper_timing_summary_routed.rpt` | 153,198 B | `...\runs\impl_1\` | **时序**：WNS +8.855 ns / WHS +0.036 ns，约束全满足 |
| `report\fir_system_wrapper_utilization_placed.rpt` | 10,328 B | 同上 | **资源**：LUT 7,084(13.32%)、FF 8,010、BRAM 2、DSP 25 |
| `report\fir_system_wrapper_drc_routed.rpt` | 37,679 B | 同上 | DRC 检查结果 |
| `report\fir_system_wrapper_clock_utilization_routed.rpt` | 17,858 B | 同上 | 时钟资源使用 |

---

## 03_SDK_Software（28 文件 / 5.4 MB）— 2026-11-03 已恢复为与原 `sdk_workspace` 同构的目录名

### fir_test — 应用工程（**必须提交**）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `src\main.c` | 9,069 B（326 行） | `SDK\fir_test\src\main.c` | **性能测试版主程序**：DMA+FIR 硬件流程 + ARM 软件 FIR 基准 + 端到端计时（`hw_sine_*`/`hw_mixed_*`/`sw_*`） |
| `src\main_v1.0.c` | 4,682 B | `BAK\项目\main_v1_backup.c` | **V1.0 基线版**（单次 DMA 测试，无计时）。原名 `main_v1_backup.c`，为避免与 `main.c` 混淆已在此重命名 |
| `src\fir_test_inputs.h` | 28,894 B（413 行） | `SDK\fir_test\src\` | **输入测试数据**：`TEST_INPUT_COUNT 1000`、`SineInput[1000]`、`MixedInput[1000]`（float32） |
| `src\lscript.ld` | 6,165 B | 同上 | 链接脚本（DDR/OCM 布局） |
| `src\Xilinx.spec` | 36 B | 同上 | 编译符号定义 |
| `src\README.txt` | 41 B | 同上 | SDK 自动生成的说明模板（无实质内容） |
| `.project` | 825 B | `SDK\fir_test\.project` | 工程描述（引用 BSP `fir_test_bsp`） |
| `.cproject` | 16,951 B | `SDK\fir_test\.cproject` | 编译配置（`-O0 -g3`、include 路径、ARM 硬浮点） |

### fir_test_bsp — 板级支持包配置

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `system.mss` | 3,788 B | `SDK\fir_test_bsp\` | **BSP 配置（重建 BSP 的唯一必需输入）**：驱动列表、stdin/stdout、库选项 |
| `.project` / `.cproject` / `.sdkproject` | 2,477 / 748 / 115 B | 同上 | BSP 工程描述 |

> 未包含 `ps7_cortexa9_0\lib`(1.1 MB) 与 `libsrc`(2.2 MB)——可由 `system.mss` + 硬件平台一键重新生成，属可重建产物。

### fir_system_wrapper_hw_platform_0 — 硬件平台（**含 xfir 驱动，必须提交**）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `.project` | 1,029 B | `SDK\fir_system_wrapper_hw_platform_0\` | 平台工程描述 |
| `system.hdf` | 671,591 B | 同上 | 硬件导出（与 `02\output` 同源） |
| `ps7_init.c` / `.h` / `.tcl` / `_gpl.c` / `_gpl.h` | 320,670 / 5,047 / 25,544 / 320,060 / 4,425 B | 同上 | **PS 初始化代码**（DDR、时钟、MIO）；调试下载必需 |
| `drivers\fir_v1_0\src\xfir.c` / `.h` / `_hw.h` / `_sinit.c` / `_linux.c` / `Makefile` | 5,083 / 3,051 / 1,403 / 1,046 / 4,611 / 746 B | 同上 `drivers\` | **FIR IP 驱动**（HLS 导出时自动装入平台，BSP 从这里生成 `xfir` 库） |
| `drivers\fir_v1_0\data\fir.mdd` / `fir.tcl` | 485 / 761 B | 同上 | 驱动元数据 |
| `fir_system_wrapper.bit` | 4,045,678 B | 同上 | 平台配套 Bitstream（与 `02\output` 完全相同的副本，供 SDK 内部 Program FPGA 使用） |

---

## 04_Test_Evidence（19 文件 / 约 460 KB）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `output\fir_impulse_fpga_1000.bin` | 4,000 B | `BAK\` | V1.0 冲激响应输出（1000×float32 LE），前 51 点应≈系数 |
| `output\fir_sine_fpga_1000.bin` | 4,000 B | `BAK\` | V1.0 正弦输入下的 FPGA 输出 |
| `output\fir_mixed_fpga_1000.bin` | 4,000 B | `BAK\` | V1.0 混频输入下的 FPGA 输出 |
| `output\fir_sine_fpga_perf_1000.bin` | 4,000 B | `BAK\` | 性能版·正弦 FPGA 输出（对拍误差≈2×10⁻⁶） |
| `output\fir_mixed_fpga_perf_1000.bin` | 4,000 B | `BAK\` | 性能版·混频 FPGA 输出（同上） |
| `logs\FIR_V1.0_测试结果.txt` | 3,748 B | `BAK\` | V1.0 测试结果文字记录 |
| `logs\性能测试原始日志_恢复_20261024.txt` | 4,780 B | `BAK\` | **XSCT `mrd` 原始输出逐字恢复**（三次板测：软件基准 / 带断点 / 干净运行），含全部 hex 值 |
| `logs\board_test.tcl` | 807 B | `PFB\` | 板测脚本①：下载运行、读软件 FIR 计时变量 |
| `logs\board_test2.tcl` | 1,272 B | `PFB\` | 板测脚本②：断点导出正弦输出（**注意：断点会污染计时窗口**，该次 `hw_mixed` 值作废） |
| `logs\board_test3.tcl` | 895 B | `PFB\` | 板测脚本③：无断点干净运行，最终有效计时来源 |
| `logs\build_perf.tcl` | 248 B | `PFB\` | XSCT 无头构建脚本（`projects -build -name fir_test -type app`） |
| `dumps\sine_dump.txt` | 10,000 B | `PFB\` | 正弦组 RxBuffer 1000 个 32 位 hex（JTAG 逐字读取） |
| `dumps\mixed_dump.txt` | 10,000 B | `PFB\` | 混频组（带断点运行，数据有效、计时无效） |
| `dumps\mixed_dump_clean.txt` | 10,000 B | `PFB\` | 混频组（干净运行） |
| `screenshots\V1.0成果.png` | 92,713 B | `BAK\` | V1.0 功能测试截图（SDK Expressions，`test_status=2`）。**非性能测试截图** |
| `screenshots\性能测试_SDK_Expressions_20261024.png` | 38,282 B | 技术报告图12原图提取 | **性能测试截图（最终采用数据来源）**：8 个计时变量同屏，`test_status=4`，数值与计数逐位自洽 |
| `screenshots\性能测试_正弦对拍_Jupyter.png` | 80,930 B | 技术报告图12组图提取 | 正弦组 Python 理论 vs FPGA 实测波形 + 绝对误差曲线 |
| `screenshots\性能测试_混频对拍_Jupyter.png` | 103,108 B | 技术报告图12组图提取 | 混频组同上 |
| `input\README.md` | — | 本次新建 | 输入数据说明（数据本体在 `fir_test_inputs.h`） |

---

## 05_Docs（5 文件 / 约 1.0 MB）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `FILE_MANIFEST.md` | — | 本次新建 | 本清单 |
| `VERSION_NOTES.md` | — | 本次新建 | V1.0 与性能版差异、计时口径、数据来源 |
| `PENDING_ITEMS.md` | — | 本次新建 | 待确认项与缺口（A-1/A-4 已解决） |
| `compare.py` | 7,992 B | 本次新建 | **独立误差复算脚本**（纯标准库）：正弦 2.194×10⁻⁶ / 混频 2.980×10⁻⁶ |
| `FIR滤波器Zynq软硬件协同实现报告_修订版.docx` | 约 918 KB | 原 `(1).docx` 修订副本 | 参赛技术报告（原件 `D:\吴凌航\` 未动） |

另：包根目录 `README.md`（提交说明）与 `QUALITY_CHECK_REPORT.md`（第三阶段质量检查报告，含性能数据来源核查）。

---

## 01_HLS_Accelerator 增补（2026-11-03）

| 文件 | 大小 | 来源 | 用途 |
|---|---|---|---|
| `data\input_signal.txt` | 12,498 B | `HLS\..\fir_hls_practice\solution1\data\`（MD5 一致复制） | C 仿真输入激励（`fir_test.cpp` 绝对路径所读文件） |
| `data\expected_output.txt` | 12,476 B | 同上 | C 仿真理论输出（testbench 参考值） |

> `fir_test.cpp` 本体未改动（遵守"不修改原始源码"）；复现 csim 的路径处理见 README §5。

---

## 附：2026-11-03 增补/变更记录

| 变更 | 说明 |
|---|---|
| SDK 目录恢复原结构 | `app\` → `fir_test\src\`（28 文件 MD5 移动前后一致）、`bsp\` → `fir_test_bsp\`、`hw_platform\` → `fir_system_wrapper_hw_platform_0\`，`.cproject` 的 `../src/lscript.ld`、`../../fir_test_bsp/...` 引用全部闭合 |
| `02\prj\fir_zynq_system.xpr` | IPRepoPath 由 `$PPRDIR/../fir_hls/solution1/impl/ip`（包外）改为 `$PPRDIR/../../01_HLS_Accelerator/ip_export`（包内相对路径） |
| `04\logs\性能测试原始日志_恢复_20261024.txt` | 文末追加【五】勘误注记（原始【一】~【四】读取记录未改动一字） |
| 性能数据定版 | 采用报告图12截图对应运行的完整数据（hw 96.2880/95.5110 µs，sw 2469.3239/2468.7209 µs，对照比 25.64/25.85），README/VERSION_NOTES 已同步 |

---

## _PENDING（11 文件 / 1.4 MB）— 待人工确认，未纳入正式结构

| 文件 | 大小 | 来源 | 待确认原因 |
|---|---|---|---|
| `elf_candidates\fir_test_29119d69_boardtest_used.elf` | 369,236 B | `PFB\fir_test.elf` | **10-24 板测实际下载的那一份**（MD5 `29119d69…`） |
| `elf_candidates\fir_test_cfdf7693_backup_perf.elf` | 369,208 B | `BAK\fir_test_perf\Debug\` | 备份区性能工程产物（MD5 `cfdf7693…`） |
| `elf_candidates\fir_test_78b08dac_sdkworkspace.elf` | 369,260 B | `SDK\fir_test\Debug\` | 原 SDK 工作区最新产物（2026-11-01，MD5 `78b08dac…`） |
| `ip_standalone\fir_0\*` | 102 KB（4 文件） | `VIV\...\sources_1\ip\fir_0\` | 独立 FIR IP 实例（xci/xml/veo/vho），**未出现在 BD 中**，疑为早期调试残留 |
| `ip_standalone\fir_1\*` | 102 KB（4 文件） | `VIV\...\sources_1\ip\fir_1\` | 同上，第二个实例 |

> 三个 ELF 由**同一份 `main.c`**（MD5 `51ba9aee…`）在不同构建环境/时间下产生，故不擅自定版。

---

## 附：本次整理**未复制**的内容及理由

| 未复制项 | 原体积 | 理由 |
|---|---|---|
| `fir_zynq_system.cache\` | 29 MB | Vivado 缓存，重开自动重建 |
| `fir_zynq_system.ip_user_files\` | 62 MB | 自动生成（`sim_scripts` 49 MB、`ipstatic` 9.2 MB） |
| `...\bd\fir_system\ipshared\` | 36 MB | IP 的 HDL 副本，由 IP 重新生成 |
| `...\bd\fir_system\ip\*\{*.dcp, *_sim_netlist.*, *_stub.*, synth, sim}\` | ~40 MB | OOC 综合中间产物 |
| `fir_zynq_system.runs\*_synth_1\`（impl_1 除外） | 8 MB | 综合中间结果 |
| `...\impl_1\{*.dcp, *.rpx, *.pb, *.vdi, runme.log, usage_statistics*}\` | ~30 MB | 实现中间产物/统计 |
| `HLS\solution1\{.autopilot, .debug, .tcls, csim\build, syn\{verilog,vhdl,systemc\}}\` | ~28 MB | HLS 生成物（RTL 已由 `ip_export/hdl` 保留） |
| `HLS\.git\` | 4.1 MB | 本地仓库（远端 `github.com/Linghang-zero/zynq7000-fir`，本次**未连接**） |
| `HLS\doc_output\`、`HLS\doc_revision.py` | 3.2 MB | **与本项目无关**（语文作文文档生成物） |
| SDK `.metadata\`、`RemoteSystemsTempFiles\`、`webtalk\`、`SDK.log` | 4 MB | IDE 本地状态，含机器相关路径 |
| `fir_test\Debug\{main.o, *.d, makefile}\` | 400 KB | 编译中间物（ELF 已归入 `_PENDING`） |
| BSP `ps7_cortexa9_0\{lib, libsrc}\` | 3.3 MB | 可由 `system.mss` + 平台重建 |
| `fir_hls_practice\`、`navigater\`、`adder*.cpp`、`vivado_hls.log` | 74 MB | 其他项目/练习，按要求整包排除 |
| `BAK\新建 文本文档.txt` | 0 B | 空文件 |
