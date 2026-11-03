# PENDING_ITEMS — 缺失材料与待确认项

> 本文件列出**尚未拿到、需要队友补充**或**必须人工判断**的项。在补齐前，提交包不应宣称"材料完整"。

---

## A. 必须补充的证据材料（缺一项都会影响评审）

### A-1. 性能测试截图 ✅ **已解决（2026-11-03）**

| 项 | 说明 |
|---|---|
| 状态 | 已从技术报告原图提取并入库：`04_Test_Evidence/screenshots/性能测试_SDK_Expressions_20261024.png`（SDK Expressions，8 个计时变量同屏、`test_status=4` 对应那次完整运行）及正弦/混频 Jupyter 对拍图各 1 张 |
| 截图数值 | `hw_sine_us`=96.2880、`hw_mixed_us`=95.5110、`sw_sine_us`=2469.3239、`sw_mixed_us`=2468.7209（与计数值逐位自洽，已核验） |
| 注意事项 | ① 断点/长时间暂停会污染计时窗口，**截图前不要在该组计时区间内停顿**；② 新运行的末几位小数会与 10-24 略有差异（Global Timer 抖动），属正常现象，**不要修改数值去凑历史数据** |

### A-2. `fir_impulse_fpga.csv` ❌

| 项 | 说明 |
|---|---|
| 缺什么 | 冲激响应对应的 CSV（清单中曾列出，实际从未生成） |
| 状态 | 全盘 `find -iname "*.csv"` 结果为空 |
| 补充方式 | 由 `04_Test_Evidence/output/fir_impulse_fpga_1000.bin`（1000×float32 LE）转换，或重新导出 |

### A-3. 项目报告 / 答辩 PPT / 演示视频 ❌

| 项 | 说明 |
|---|---|
| 状态 | 全盘无任何本项目 `.md/.docx/.pdf/.pptx` 文档，也无视频 |
| 需补充 | ① 设计报告（架构、HLS 优化、DMA 通路、实测数据）；② 答辩 PPT；③ 演示视频（可录屏 + 板卡实物） |

### A-4. 误差验证脚本 ✅ **已解决（2026-11-02/03）**

| 项 | 说明 |
|---|---|
| 现状 | 已固化为 `05_Docs/compare.py`（纯标准库，无需 numpy）：解析 `fir_test_inputs.h` 两组输入 + `fir.cpp` 51 系数，按定点位宽重建参考输出，与 `output/*.bin` 逐点比对，并校验 `dumps/*.txt` 与 bin 逐字一致 |
| 复算结果 | 正弦最大绝对误差 **2.194×10⁻⁶**（均值 1.158×10⁻⁶）、混频 **2.980×10⁻⁶**（均值 1.496×10⁻⁶）、冲激响应前 51 点与 h[] 偏差 2.32×10⁻⁷；1000/1000 点误差 < 1e-3 |
| 运行方式 | `python 05_Docs/compare.py` |

---

## B. 待人工确认（本包**未擅自决定**）

### B-1. 三个 `fir_test.elf` 版本 — 需定版

三份 ELF 由**同一份 `main.c`**（MD5 `51ba9aee…`）在不同环境下编译产生，内容不同：

| 候选 | 文件（在 `_PENDING/elf_candidates/`） | 大小 | MD5 | 来源 | 备注 |
|---|---|---|---|---|---|
| ① | `fir_test_29119d69_boardtest_used.elf` | 369,236 B | `29119d69…` | `D:\fp_perf_build\fir_test.elf` | **10-24 板测实际下载运行的那一份**，实测数据由它产生 |
| ② | `fir_test_cfdf7693_backup_perf.elf` | 369,208 B | `cfdf7693…` | `D:\FpGA备份\V1.0成果保存\fir_test_perf\Debug\` | 备份区性能工程产物 |
| ③ | `fir_test_78b08dac_sdkworkspace.elf` | 369,260 B | `78b08dac…` | `sdk_workspace\fir_test\Debug\` | 时间最新（2026-11-01 00:11） |

**建议**：以 ① 为提交版（唯一有板上实测背书的产物），② ③ 仅作留档。
**需确认**：三者差异是否仅来自构建路径/时间戳；若要交付"可重新编译出同一 ELF"的承诺，需在同一环境下重编并比对。

### B-2. 两个独立 FIR IP 实例 — 是否保留

`_PENDING/ip_standalone/fir_0/`、`fir_1/`（各含 `.xci`/`.xml`/`.veo`/`.vho`，共 204 KB）

- 来源：`fir_zynq_system.srcs\sources_1\ip\`
- 状态：**未出现在 Block Design 中**（BD 用的是 `bd\fir_system\ip\fir_system_fir_0_0`，VLNV 同为 `xilinx.com:hls:fir:1.0`）
- 疑为早期单独例化调试时残留
- **需确认**：删除是否影响工程打开？（本次未删、未改，仅原样留档在 `_PENDING`）

### B-3. HLS 工程未提交的改动

原 `fir_hls` 工作区 `git status` 显示 13 项 modified（`fir.cpp`、`fir_test.cpp`、`script.tcl`、`solution1.aps`、`syn/verilog/fir.v` 等），提交包取的是**工作区当前实际版本**而非 `git HEAD`（`d71deb5 ii=25版本`）。
**需确认**：是否需要在提交前把工作区改动 commit 一次，以保证"仓库版本 = 提交包版本"。

### B-4. GitHub 仓库是否作为提交渠道

`fir_hls\.git` 已配置远端 `https://github.com/Linghang-zero/zynq7000-fir.git`（本次**仅读取配置，未连接、未推送**）。
**需确认**：最终以压缩包提交还是以仓库提交；若用仓库，是否要把 Vivado/SDK 也纳入同一仓库（当前只有 HLS 在版本控制下）。

### B-5. 工程绝对路径（复现性问题）

| 文件 | 命中数 | 说明 |
|---|---|---|
| `02_Vivado_Hardware/prj/fir_zynq_system.xpr` | 1 处 `D:/vivado_file/fir_zynq_system/fir_zynq_system.xpr` | 工程自引用路径，直接打开副本时可能回指原工程 |
| `01_HLS_Accelerator/project/.project` | 含 `D:/vivado_file/fir_hls/...` | HLS 工程源文件引用 |
| `03_SDK_Software/*/.cproject|.project` | **0 处** | SDK 侧无绝对路径，可安全迁移 |

**本包未修改这些路径**（改了就与原工程不再一致，且需重跑验证）。
**因此本包不宣称"可一键独立复现"**——它是有来源可溯的源码/成果归档。若需真·可独立打开的工程，需另做一步"副本内重建工程 + 重指源文件 + 重跑 csim/synth"（属新增工作，需你确认是否要做）。

---

## C. 已知但不阻塞提交的问题

| # | 问题 | 影响 | 处理建议 |
|---|---|---|---|
| C-1 | 性能版 `test_status=2` 语义已变为"两组硬件完成" | 与 V1.0 的 `2` 混淆 | 已在 `VERSION_NOTES.md` 说明 |
| C-2 | 带断点的那次运行 `hw_mixed_cycles = 689,253,419`（≈2.07 s）被调试停顿污染 | 该值无效 | 已在日志中标注作废，最终采用 `board_test3.tcl` 干净运行数据 |
| C-3 | 板内无在线误差计算（`max_abs_error` 仅占位） | 误差需离线复算 | 建议补 `compare.py`（见 A-4） |
| C-4 | 软件基准编译选项为 `-O0` | 加速比可能偏高 | 引用时必须注明；如需更严格基线可补 `-O2` 数据（需重测） |
| C-5 | BSP 的 `lib/`、`libsrc/` 未纳入提交包 | 首次编译需先"Generate BSP" | 已在 README 复现步骤说明 |
| C-6 | HLS `cosim_design` 在 `script.tcl` 中被调用，但 `solution1\sim\` 目录不存在 | 无 cosim 证据 | 如需 C/RTL 协同仿真证据，需重跑 cosim |

---

## D. 补齐后的自查清单

- [x] 性能测试截图（Expressions 显示 8 个变量，已入库）
- [x] `compare.py`（误差可复算）
- [ ] `fir_impulse_fpga.csv`
- [ ] 设计报告 ✅（修订版已入 `05_Docs/`）/ 答辩 PPT / 演示视频
- [ ] ELF 定版（三选一，写入 README）
- [ ] 独立 FIR IP 实例去留决策
- [ ] HLS 工作区改动是否 commit
- [ ] 提交渠道（压缩包 / GitHub）确认
- [ ] 是否需要"副本内重建并重跑"以支持独立复现声明
