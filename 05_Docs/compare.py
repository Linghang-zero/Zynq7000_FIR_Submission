#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare.py — 独立复算 51 抽头 FIR 的板上输出误差（纯标准库，无需 numpy / Xilinx 工具）

用途
----
1. 从 03_SDK_Software/app/fir_test_inputs.h 解析两组 1000 点输入（SineInput / MixedInput）
2. 从 01_HLS_Accelerator/src/fir.cpp 解析 51 个系数 h[]
3. 按定点量化位宽重算因果 FIR 参考输出（x[n<0] = 0）
4. 读取 04_Test_Evidence/output/*.bin（1000 × float32 小端）逐点比对，
   输出最大绝对误差、平均绝对误差、超限点数
5. 校验 04_Test_Evidence/dumps/*.txt 的 hex 文本与 .bin 是否逐字一致

数据格式依据（已核实，非猜测）
------------------------------
- .bin：4000 字节 = 1000 × 4 字节，小端 IEEE-754 float32。
- dumps/*.txt：1000 行文本，每行 8 位十六进制，表示该样本 32 位字本身
  （例如 "38553880" 对应 .bin 中字节 80 38 55 38）。
- 输入：fir_test_inputs.h 中的 float32 字面量，共 1000 个/组。
- 系数：fir.cpp 的 coeff_t h[51]（ap_fixed<24,2> 量化后的十进制字面量）。

用法
----
    python compare.py            # 在任意目录运行，脚本自动定位提交包根目录
"""

import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

INPUT_H = ROOT / "03_SDK_Software" / "fir_test" / "src" / "fir_test_inputs.h"
FIR_CPP = ROOT / "01_HLS_Accelerator" / "src" / "fir.cpp"
OUT_DIR = ROOT / "04_Test_Evidence" / "output"
DUMP_DIR = ROOT / "04_Test_Evidence" / "dumps"

DAT_FRAC_BITS = 20     # ap_fixed<24,4> -> 20 位小数
COEFF_FRAC_BITS = 22   # ap_fixed<24,2> -> 22 位小数


def f32(v):
    """舍入到 IEEE-754 float32（模拟板上 float 输出）。"""
    return struct.unpack("<f", struct.pack("<f", v))[0]


def _strip_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def parse_inputs(path):
    text = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    arrays = {}
    for name in ("SineInput", "MixedInput"):
        m = re.search(r"static\s+const\s+float\s+" + name + r"\s*\[[^\]]*\]\s*=\s*\{(.*?)\};",
                      text, flags=re.S)
        if not m:
            raise RuntimeError("未在 %s 中找到 %s 数组" % (path.name, name))
        arrays[name] = [f32(float(t.rstrip("fF"))) for t in
                        re.findall(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?f?", m.group(1))]
    return arrays


def parse_coeffs(path):
    text = _strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    m = re.search(r"static\s+const\s+coeff_t\s+h\s*\[[^\]]*\]\s*=\s*\{(.*?)\};", text, flags=re.S)
    if not m:
        raise RuntimeError("未在 %s 中找到系数数组 h[]" % path.name)
    return [float(t) for t in re.findall(r"[-+]?\d+\.?\d*(?:[eE][-+]?\d+)?", m.group(1))]


def quantize(v, frac_bits):
    step = 2.0 ** (-frac_bits)
    # 四舍五入（远离零）到最近量化步长，模拟 ap_fixed 赋值语义
    q = int(abs(v) / step + 0.5)
    return (1.0 if v >= 0 else -1.0) * q * step


def reference_fir(x, h):
    """因果 FIR：y[n] = sum_k h[k] * x[n-k]，n-k < 0 视为 0，输出舍入为 float32。"""
    hq = [quantize(c, COEFF_FRAC_BITS) for c in h]
    xq = [quantize(v, DAT_FRAC_BITS) for v in x]
    n_taps = len(hq)
    y = []
    for n in range(len(xq)):
        acc = 0.0
        for k in range(n_taps):
            idx = n - k
            if idx >= 0:
                acc += hq[k] * xq[idx]
        y.append(f32(acc))
    return y


def read_bin(path):
    raw = path.read_bytes()
    if len(raw) % 4:
        raise RuntimeError("%s 长度 %d 不是 4 的倍数" % (path.name, len(raw)))
    return list(struct.unpack("<%df" % (len(raw) // 4), raw))


def read_dump(path):
    words = [int(ln.strip(), 16) for ln in
             path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
    return list(struct.unpack("<%df" % len(words), struct.pack("<%dI" % len(words), *words)))


def compare_one(label, x, h, bin_path, dump_path=None):
    y_ref = reference_fir(x, h)
    y_hw = read_bin(bin_path)
    n = min(len(y_ref), len(y_hw))
    errs = [abs(y_ref[i] - y_hw[i]) for i in range(n)]
    imax = max(range(n), key=lambda i: errs[i])
    mx, mean = errs[imax], sum(errs) / n

    print("\n[%s]  %s" % (label, bin_path.name))
    print("  样本数        : %d（参考 %d）" % (len(y_hw), len(y_ref)))
    print("  参考模型      : 定点量化（输入 2^-%d / 系数 2^-%d）+ float64 累加 + float32 输出"
          % (DAT_FRAC_BITS, COEFF_FRAC_BITS))
    print("  最大绝对误差  : %.6e  (index %d: ref=%.9f, hw=%.9f)"
          % (mx, imax, y_ref[imax], y_hw[imax]))
    print("  平均绝对误差  : %.6e" % mean)
    print("  误差 > 1e-5   : %d 点" % sum(1 for e in errs if e > 1e-5))
    print("  误差 > 1e-3   : %d 点" % sum(1 for e in errs if e > 1e-3))
    print("  首样本        : hw=%.9f  ref=%.9f" % (y_hw[0], y_ref[0]))

    if dump_path is not None and dump_path.exists():
        y_dump = read_dump(dump_path)
        bit_equal = (len(y_dump) == len(y_hw) and
                     struct.pack("<%df" % len(y_dump), *y_dump) ==
                     struct.pack("<%df" % len(y_hw), *y_hw))
        print("  dump 一致性   : %s 行数=%d -> %s"
              % (dump_path.name, len(y_dump),
                 "与 .bin 逐字一致" if bit_equal else "与 .bin 不一致/长度不同"))
    return mx, mean


def main():
    if not INPUT_H.exists() or not FIR_CPP.exists():
        print("错误：找不到输入或系数源文件，请确认脚本位于提交包 05_Docs/ 下。")
        return 2

    inputs = parse_inputs(INPUT_H)
    h = parse_coeffs(FIR_CPP)

    print("=" * 68)
    print("Zynq-7000 51 抽头 FIR — 板上输出独立复算")
    print("=" * 68)
    for name, arr in inputs.items():
        print("输入 %-11s: %d 点, 峰值 %.6f" % (name, len(arr), max(abs(v) for v in arr)))
    sym = all(abs(h[i] - h[-1 - i]) < 1e-9 for i in range(len(h)))
    print("系数 h[]     : %d 个, 中心 h[%d]=%.8f, 对称性=%s"
          % (len(h), len(h) // 2, h[len(h) // 2], "通过" if sym else "不通过"))
    if len(h) != 51:
        print("警告：系数个数不是 51，与设计声明不符")

    targets = [
        ("正弦 / V1.0 板测", inputs["SineInput"], OUT_DIR / "fir_sine_fpga_1000.bin",
         DUMP_DIR / "sine_dump.txt"),
        ("混频 / V1.0 板测", inputs["MixedInput"], OUT_DIR / "fir_mixed_fpga_1000.bin",
         DUMP_DIR / "mixed_dump.txt"),
        ("正弦 / 性能版", inputs["SineInput"], OUT_DIR / "fir_sine_fpga_perf_1000.bin", None),
        ("混频 / 性能版", inputs["MixedInput"], OUT_DIR / "fir_mixed_fpga_perf_1000.bin",
         DUMP_DIR / "mixed_dump_clean.txt"),
    ]

    results = []
    for label, x, bp, dp in targets:
        if not bp.exists():
            print("\n[%s] 缺失文件 %s，跳过" % (label, bp.name))
            continue
        results.append(compare_one(label, x, h, bp, dp))

    imp = OUT_DIR / "fir_impulse_fpga_1000.bin"
    if imp.exists():
        y_imp = read_bin(imp)
        n = min(len(h), len(y_imp))
        dev = max(abs(y_imp[i] - h[i]) for i in range(n))
        print("\n[冲激响应]  %s" % imp.name)
        print("  前 %d 点与 h[] 最大偏差 : %.6e" % (n, dev))
        print("  说明：单位冲激经 ap_fixed<24,4> 与系数量化后应逼近 h[n]，偏差来自量化")

    print("\n" + "-" * 68)
    if results:
        worst = max(r[0] for r in results)
        print("结论：%d 组比对中最大绝对误差 = %.3e" % (len(results), worst))
        if worst < 5e-6:
            print("      与文档『约 2×10⁻⁶』的表述一致。")
        else:
            print("      与文档『约 2×10⁻⁶』的表述不一致，需更新文档。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
