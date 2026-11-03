#!/usr/bin/env python
# coding: utf-8

# In[1]:


#【滤波器设计与初步仿真调试代码】
# 加载前期生成的测试信号，完成51抽头FIR低通滤波器设计、频响分析，
# 先用scipy自带lfilter做快速滤波预览，观察滤波效果、误差。
# 注意：本处lfilter初始状态和HLS零填充规则不一致，仅用于前期设计调试、看频响和定性效果，
# 不作为和FPGA硬件比对的Golden参考基准，硬件比对使用单独实现的零填充FIR版本。
# 参数：51抽头，截止频率20Hz，采样率1000Hz，目标保留5Hz信号、抑制50Hz干扰。
# 输出：滤波器系数文件fir_coeff.npy/fir_coeff.txt，频响图、时域滤波对比图、误差统计。

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import firwin, lfilter, freqz

# 加载昨天存的信号
signal = np.load('signal.npy')
t      = np.load('t.npy')
clean  = np.load('clean.npy')
fs = 1000

# ============ 1. 设计 FIR 低通滤波器 ============
numtaps = 51        # 阶数（奇数，越大越陡）
cutoff  = 20        # 截止 20Hz：5Hz 通过，50Hz 挡掉

h = firwin(numtaps, cutoff, fs=fs, window='hamming')

# 存系数，给队友 C 用
np.save('fir_coeff.npy', h)
np.savetxt('fir_coeff.txt', h, fmt='%.8f')
print(f"滤波器阶数: {numtaps}, 截止: {cutoff}Hz")
print(f"系数已存到 fir_coeff.txt，长度 {len(h)}")

# ============ 2. 频率响应（看滤波器长什么样）============
w, H = freqz(h, fs=fs)
plt.figure(figsize=(12, 4))
plt.plot(w, 20*np.log10(np.abs(H)))
plt.axvline(5,  color='g', ls='--', label='5Hz (signal)')
plt.axvline(50, color='r', ls='--', label='50Hz (interference)')
plt.axvline(cutoff, color='gray', ls=':', label=f'cutoff {cutoff}Hz')
plt.xlabel('frequency (Hz)'); plt.ylabel('magnitude (dB)')
plt.title('Filter frequency response'); plt.legend(); plt.grid(True)
plt.show()

# ============ 3. 滤波 ============
filtered = lfilter(h, 1.0, signal)

# ============ 4. 画对比 ============
plt.figure(figsize=(12, 8))
plt.subplot(3,1,1)
plt.plot(t, signal); plt.title('Noisy input'); plt.grid(True)
plt.subplot(3,1,2)
plt.plot(t, filtered, 'b', label='filtered')
plt.plot(t, clean, 'r--', label='clean 5Hz')
plt.title('Filtered vs clean'); plt.legend(); plt.grid(True)
plt.subplot(3,1,3)
plt.plot(t, filtered - clean)
plt.title('Error (filtered - clean)'); plt.xlabel('time (s)'); plt.grid(True)
plt.tight_layout(); plt.show()

# ============ 5. 量化误差 ============
print(f"最大误差: {np.max(np.abs(filtered - clean)):.4f}")
print(f"RMS 误差: {np.sqrt(np.mean((filtered - clean)**2)):.4f}")


# In[2]:


#【FIR滤波时延对齐代码】
#FIR线性相位滤波器固有群延迟 = 抽头数//2 = 25个采样点，
#将滤波输出裁剪25点，和原始干净信号做时间对齐，消除相位偏移带来的观察误差。
#仅用于直观对比波形，不是我们HLS硬件的输出规则：硬件保留全部1000点、不做裁剪。
#计算对齐之后波形的最大误差、RMS误差，方便评估滤波效果。

delay = numtaps // 2   # = 25
filtered_aligned = filtered[delay:]
clean_aligned    = clean[:-delay]

plt.figure(figsize=(12,4))
plt.plot(t[delay:], filtered_aligned, 'b', label='filtered (aligned)')
plt.plot(t[delay:], clean_aligned, 'r--', label='clean')
plt.title('After delay alignment'); plt.legend(); plt.grid(True)
plt.show()

print(f"对齐后最大误差: {np.max(np.abs(filtered_aligned - clean_aligned)):.4f}")
print(f"对齐后 RMS 误差: {np.sqrt(np.mean((filtered_aligned - clean_aligned)**2)):.4f}")


# In[3]:


#【频谱分析代码】
#对输入含噪信号、滤波后信号做FFT，画出单边幅度频谱，直观观察滤波效果：
#看5Hz有用分量是否保留、50Hz干扰分量是否被衰减。
#横坐标限定0~100Hz，聚焦关心频段。
#属于辅助观测代码，仅用于定性分析频域效果，不参与硬件结果比对。

import numpy as np
import matplotlib.pyplot as plt

# 要是变量不在了就取消下面两行的注释重新加载
# signal = np.load('signal.npy')
# h = np.load('fir_coeff.npy')
# filtered = np.convolve(signal, h, mode='same')

def plot_spectrum(x, fs, title):
    N = len(x)
    fft   = np.fft.fft(x)
    freqs = np.fft.fftfreq(N, 1/fs)
    mask  = freqs >= 0                     # 只画正频率
    mag   = np.abs(fft[mask]) * 2 / N      # 单边幅度谱
    plt.plot(freqs[mask], mag)
    plt.xlabel('frequency (Hz)')
    plt.ylabel('amplitude')
    plt.title(title)
    plt.grid(True)
    plt.xlim(0, 100)                       # 只看 0-100Hz

plt.figure(figsize=(12, 8))

plt.subplot(2,1,1)
plot_spectrum(signal, fs, 'Spectrum: noisy input')
plt.axvline(5,  color='g', ls='--', label='5Hz signal')
plt.axvline(50, color='r', ls='--', label='50Hz interference')
plt.legend()

plt.subplot(2,1,2)
plot_spectrum(filtered, fs, 'Spectrum: filtered output')
plt.axvline(5,  color='g', ls='--', label='5Hz signal')
plt.axvline(50, color='r', ls='--', label='50Hz interference')
plt.legend()

plt.tight_layout()
plt.show()


# In[4]:


#【导出文本参考数据代码】
#将输入信号、滤波参考结果保存为csv文本文件，提供给硬件端队友使用，
#方便HLS仿真时加载测试数据，做初步对照。
#注意：此处filtered是lfilter得到的结果，和我们约定的零填充初始条件版本不一致，
#仅作为早期参考，正式硬件比对采用单独实现的零填充FIR golden数据。
import numpy as np

# 把输入信号和滤波结果存成 CSV（每行一个数，文本格式）
np.savetxt('input_signal.csv', signal,    fmt='%.8f')
np.savetxt('expected_output.csv', filtered, fmt='%.8f')

print("已生成：")
print("  input_signal.csv     - 给队友的输入（1000 个数）")
print("  expected_output.csv  - 队友 C 代码应该输出的结果（参考值）")
print("  fir_coeff.txt       - 滤波器系数（51 个）")


# In[5]:


#【分层接口封装代码：软件FIR模拟器，面向PYNQ软硬件统一调用框架】
#设计统一filter()接口，上层业务代码无需改动，支持无缝切换：
#当前：FIRFilterSoftware（scipy lfilter软件实现，用来调试整体数据流框架）
#后续：替换为FIRFilterPL（PYNQ调用FPGA硬件IP，DMA传输）
#完整模拟Zynq的PS-PL数据流流程：准备输入数据 → DMA下发 → FIR计算 → DMA回读结果
#注意：底层依然是lfilter，初始条件和HLS零填充版本不一致，仅用于框架调试，不作为硬件最终比对基准。
#输出：output_software.csv

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import lfilter

# ============================================================
# 统一接口：FIR Filter
#   - 现在：FIRFilterSoftware  （用 scipy lfilter 模拟 PL）
#   - 将来：FIRFilterPL        （PYNQ Overlay 调硬件）
# 上层代码只调 fir.filter(x)，不关心底下是谁在算
# ============================================================

class FIRFilterSoftware:
    """软件版 FIR，模拟 PL 行为（现在用）"""
    def __init__(self, coeffs):
        self.coeffs = coeffs

    def filter(self, x):
        # 这一行将来换成 PL 调用
        return lfilter(self.coeffs, 1.0, x)


# ============ 主流程 ============
# 1. 生成输入信号
fs = 1000
t = np.arange(0, 1.0, 1/fs)
clean = np.sin(2*np.pi*5*t)
interference = 0.5*np.sin(2*np.pi*50*t)
noise = 0.3*np.random.randn(len(t))
signal = clean + interference + noise

# 2. 加载滤波器系数
h = np.loadtxt('fir_coeff.txt')

# 3. 打包数据（模拟 DMA 传输）
#    将来这里就是：把 signal 数组放进 PS 内存的一块 buffer，
#    然后启动 DMA 把它喂给 PL
print(f"输入数据打包: {len(signal)} 个采样点, dtype={signal.dtype}")
print(f"滤波器系数:   {len(h)} 个")

# 4. 调 FIR（现在软件版，将来 PL）
fir = FIRFilterSoftware(h)
output = fir.filter(signal)

# 5. 收输出（模拟 DMA 把结果从 PL 搬回 PS 内存）
print(f"输出数据:     {len(output)} 个采样点")

# 6. 画图验证
plt.figure(figsize=(12, 6))
plt.subplot(2,1,1)
plt.plot(t, signal, label='input (noisy)')
plt.plot(t, clean, 'r--', label='clean 5Hz')
plt.legend(); plt.grid(True); plt.title('Input')

plt.subplot(2,1,2)
plt.plot(t, output, 'b', label='FIR output')
plt.plot(t, clean, 'r--', label='clean 5Hz')
plt.legend(); plt.grid(True); plt.xlabel('time (s)'); plt.title('Output')
plt.tight_layout()
plt.show()

# 7. 保存最终输出，将来跟 PL 输出对
np.savetxt('output_software.csv', output, fmt='%.8f')
print("\n流程跑通。output_software.csv 已保存。")


# In[6]:


#【最终对齐HLS规则的Golden参考与AXI数据流打包代码】
# 核心：从零手写零填充FIR，和队友HLS的初始条件完全一致，作为硬件结果比对的标准基准。
# 功能包含：
# 1.提供两种测试信号生成函数：单频正弦信号、混频信号；
# 2.零填充FIR实现：输入历史不足时补0，输出保留全部1000点，不做延迟裁剪；
# 3.文本导出：生成txt/csv文件供给硬件端仿真对照；
# 4.字节打包/解包函数：实现32bit float小端字节转换，适配AXI4-Stream TDATA；
# 5.波形绘图、误差计算函数；
# 6.预留PYNQ DMA上板代码框架（注释占位，等待bit文件后启用）。
# ！！重点：本版本是正式硬件比对基准，和前面lfilter版本初始条件不同，以此为准。
# 参数固定：51抽头，1000采样点，float32小端。

import numpy as np
import matplotlib.pyplot as plt
import struct

# ===================== 配置参数（和A对齐，不要改） =====================
TAP_NUM = 51
SAMPLE_NUM = 1000
# 示例FIR系数，你可以替换成你们HLS里实际的51个系数
coeffs = np.array([
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
], dtype=np.float32)

# ===================== 1. 生成测试信号（正弦 / 混频） =====================
def gen_sine_signal(n, fs=1000, f=50):
    t = np.arange(n) / fs
    sig = np.sin(2 * np.pi * f * t)
    return sig.astype(np.float32)

def gen_mixed_signal(n, fs=1000):
    t = np.arange(n) / fs
    sig = np.sin(2 * np.pi * 30 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)
    return sig.astype(np.float32)

# 选一组测试，也可以两组都跑
input_sig = gen_mixed_signal(SAMPLE_NUM)
# input_sig = gen_sine_signal(SAMPLE_NUM)

# ===================== 2. 零填充FIR（和HLS行为严格对齐） =====================
def fir_zeropad(x, h):
    N = len(x)
    M = len(h)
    y = np.zeros(N, dtype=np.float32)
    for n in range(N):
        acc = 0.0
        for k in range(M):
            idx = n - k
            if idx >= 0:
                acc += x[idx] * h[k]
            # idx<0 自动补0，和A的零填充初始条件一致
        y[n] = acc
    return y

ref_output = fir_zeropad(input_sig, coeffs)

# ===================== 3. 文件导出：txt给A上板，csv用于本地比对 =====================
# 导出输入txt，一行一个float，A直接读
np.savetxt("input_mixed.txt", input_sig, fmt="%.8f")
# 导出软件参考输出csv
np.savetxt("ref_mixed.csv", ref_output, fmt="%.8f")

# ===================== 4. float32 <-> 字节打包（AXI4-Stream TDATA，32bit） =====================
def float_to_bytes(arr):
    b = b""
    for f in arr:
        b += struct.pack("<f", f) # 小端，和Zynq常用一致，和A确认字节序
    return b

def bytes_to_float(bs, n):
    fmt = "<" + "f"*n
    return np.array(struct.unpack(fmt, bs), dtype=np.float32)

# 打包示例，后面DMA传输直接复用
tx_bytes = float_to_bytes(input_sig)
# rx_float = bytes_to_float(rx_bytes, SAMPLE_NUM)

# ===================== 5. 绘图比对 =====================
plt.figure(figsize=(12,5))
plt.subplot(2,1,1)
plt.plot(input_sig, label="Input")
plt.title("Input Signal")
plt.legend()
plt.grid(True)
plt.subplot(2,1,2)
plt.plot(ref_output, label="FIR Software Output (zero-pad)", color="orange")
plt.title("Software Reference FIR Output")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# ===================== 6. 【预留硬件占位代码】等拿到.xsa和地址表再启用 =====================
"""
from pynq import Overlay, Allocate
# ol = Overlay("design_1.bit")
# dma = ol.axi_dma_0
# tx_buf = Allocate(shape=(SAMPLE_NUM,), dtype=np.float32)
# rx_buf = Allocate(shape=(SAMPLE_NUM,), dtype=np.float32)
# tx_buf[:] = input_sig[:]
# dma.sendchannel.transfer(tx_buf)
# dma.recvchannel.transfer(rx_buf)
# dma.sendchannel.wait()
# dma.recvchannel.wait()
# hw_output = np.array(rx_buf)
# 之后：hw_output 和 ref_output 做误差对比
"""

# ===================== 误差计算函数（等拿到硬件数据直接调用） =====================
def calc_error(ref, hw):
    err = np.abs(ref - hw)
    max_err = np.max(err)
    rmse = np.sqrt(np.mean(err**2))
    print(f"Max Absolute Error: {max_err:.8e}")
    print(f"RMSE: {rmse:.8e}")
    return err


# In[7]:


#【FPGA冲激响应离线比对代码】
#专门读取硬件输出的bin文件（小端32bit float），转为csv，
#使用和HLS对齐的零填充FIR计算理论冲激响应，和FPGA结果做对比。
#测试激励：冲激信号（首点为1，其余为0）
#输出：全局误差指标（最大误差、RMSE）
#绘制两张图：全部1000点总波形 + 前51点局部放大波形
#用于验证FIR滤波器的系数是否正确、硬件通路是否正常。
#这是上板实测后的验证代码，是硬件实测结果核对环节。

import numpy as np
import matplotlib.pyplot as plt
import struct

# ===================== 配置区 =====================
TAP_NUM = 51
SAMPLE_NUM = 1000
coeffs = np.array([ 0.00000000, 0.00016465, 0.00038504, 0.00070848,
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
    0.00038504, 0.00016465, 0.00000000], dtype=np.float32)

# ===================== 1. 小端float32 bin文件转csv（精度改成%.9g） =====================
def bin_to_float_csv(bin_path, out_csv_path, n_sample):
    with open(bin_path, "rb") as f:
        bs = f.read()
    data = np.array(struct.unpack("<" + "f"*n_sample, bs), dtype=np.float32)
    np.savetxt(out_csv_path, data, fmt="%.9g")
    return data

# ===================== 2. 零填充FIR（和HLS对齐） =====================
def fir_zeropad(x, h):
    N = len(x)
    M = len(h)
    y = np.zeros(N, dtype=np.float32)
    for n in range(N):
        acc = 0.0
        for k in range(M):
            idx = n - k
            if idx >= 0:
                acc += x[idx] * h[k]
        y[n] = acc
    return y

# 冲激输入：第一个点为1，其余0
impulse_in = np.zeros(SAMPLE_NUM, dtype=np.float32)
impulse_in[0] = 1.0

# ===================== 3. 执行解析、理论计算 =====================
fpga_out = bin_to_float_csv("fir_impulse_fpga_1000.bin", "fir_impulse_fpga.csv", SAMPLE_NUM)
theory_out = fir_zeropad(impulse_in, coeffs)
err = np.abs(theory_out - fpga_out)
max_err = np.max(err)
rmse = np.sqrt(np.mean(err**2))
print(f"最大绝对误差：{max_err:.8e}")
print(f"RMSE：{rmse:.8e}")

# ===================== 图1：完整1000点总图 =====================
plt.rcParams['figure.dpi'] = 300
plt.figure(figsize=(12, 5))
plt.subplot(2,1,1)
plt.plot(theory_out, label="Python Theory", linewidth=1.2)
plt.plot(fpga_out, label="FPGA Measured", linestyle="--", linewidth=1.2)
plt.title("Impulse Response: Theory vs FPGA (Full 1000 Samples)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.subplot(2,1,2)
plt.plot(err, color="#c82423", linewidth=1)
plt.title("Absolute Error (Full 1000 Samples)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# ===================== 图2：前51点局部放大图 =====================
plt.figure(figsize=(10, 5))
plt.subplot(2,1,1)
plt.plot(theory_out[:51], label="Python Theory", linewidth=1.3, marker='.')
plt.plot(fpga_out[:51], label="FPGA Measured", linestyle="--", linewidth=1.3, marker='.')
plt.title("Impulse Response: Theory vs FPGA (Zoom in First 51 Samples)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.subplot(2,1,2)
plt.plot(err[:51], color="#c82423", linewidth=1.2, marker='.')
plt.title("Absolute Error (Zoom in First 51 Samples)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


# In[8]:


#【正弦、混频信号FPGA实测比对代码】
#读取两组不同激励对应的FPGA输出bin文件，转换成csv；
#加载预先计算好的Golden参考数据，分别计算误差指标；
#封装通用绘图函数，输出完整波形图与前51点局部放大对比图。
#测试激励：单频正弦信号、混频信号，用于多场景验证FIR硬件功能。
#依赖：ref_sine.csv、ref_mixed.csv（零填充FIR基准输出）

import numpy as np
import matplotlib.pyplot as plt
import struct

# ===================== 配置区 =====================
TAP_NUM = 51
SAMPLE_NUM = 1000

# ===================== 工具函数 =====================
def bin_to_float_csv(bin_path, out_csv_path, n_sample):
    with open(bin_path, "rb") as f:
        bs = f.read()
    data = np.array(struct.unpack("<" + "f"*n_sample, bs), dtype=np.float32)
    np.savetxt(out_csv_path, data, fmt="%.9g")
    return data

def fir_zeropad(x, h):
    N = len(x)
    M = len(h)
    y = np.zeros(N, dtype=np.float32)
    for n in range(N):
        acc = 0.0
        for k in range(M):
            idx = n - k
            if idx >= 0:
                acc += x[idx] * h[k]
        y[n] = acc
    return y

# ---------------------- 2. 正弦信号 ----------------------
fpga_sine = bin_to_float_csv("fir_sine_fpga_1000.bin", "fir_sine_fpga.csv", SAMPLE_NUM)
theory_sine = np.loadtxt("ref_sine.csv", dtype=np.float32)
err_sine = np.abs(theory_sine - fpga_sine)
max_err_sine = np.max(err_sine)
rmse_sine = np.sqrt(np.mean(err_sine**2))
print("===== 正弦信号 =====")
print(f"最大绝对误差：{max_err_sine:.8e}")
print(f"RMSE：{rmse_sine:.8e}")

# ---------------------- 3. 混频信号 ----------------------
fpga_mixed = bin_to_float_csv("fir_mixed_fpga_1000.bin", "fir_mixed_fpga.csv", SAMPLE_NUM)
theory_mixed = np.loadtxt("ref_mixed.csv", dtype=np.float32)
err_mixed = np.abs(theory_mixed - fpga_mixed)
max_err_mixed = np.max(err_mixed)
rmse_mixed = np.sqrt(np.mean(err_mixed**2))
print("\n===== 混频信号 =====")
print(f"最大绝对误差：{max_err_mixed:.8e}")
print(f"RMSE：{rmse_mixed:.8e}")

# ===================== 绘图函数 =====================
def plot_compare(theory, fpga, err, title_name):
    plt.rcParams['figure.dpi'] = 300
    # 总图 1000点
    plt.figure(figsize=(12,5))
    plt.subplot(2,1,1)
    plt.plot(theory, label="Python Theory", linewidth=1.2)
    plt.plot(fpga, label="FPGA Measured", linestyle="--", linewidth=1.2)
    plt.title(f"{title_name} (Full 1000 Samples)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.subplot(2,1,2)
    plt.plot(err, color="#c82423", linewidth=1)
    plt.title("Absolute Error")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    # 前51点放大
    plt.figure(figsize=(10,5))
    plt.subplot(2,1,1)
    plt.plot(theory[:51], label="Python Theory", linewidth=1.3, marker='.')
    plt.plot(fpga[:51], label="FPGA Measured", linestyle="--", linewidth=1.3, marker='.')
    plt.title(f"{title_name} (Zoom in First 51 Samples)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.subplot(2,1,2)
    plt.plot(err[:51], color="#c82423", linewidth=1.2, marker='.')
    plt.title("Absolute Error (Zoom in First 51 Samples)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# 只绘制正弦、混频
plot_compare(theory_sine, fpga_sine, err_sine, "Sine Wave Response")
plot_compare(theory_mixed, fpga_mixed, err_mixed, "Mixed-Frequency Response")


# In[9]:


#【性能测试组FPGA结果复核】
#对应文件：fir_sine_fpga_perf_1000.bin、fir_mixed_fpga_perf_1000.bin
#激励：正弦 / 混频，1000点，float32小端
#对照口径：
#ARM（-O0编译）：仅FIR纯计算耗时
#FPGA：端到端（缓存+DMA+FIR计算+传输）
#→ 指标称为对照比，不是严格同口径加速比

import numpy as np
import matplotlib.pyplot as plt
import struct

TAP_NUM = 51
SAMPLE_NUM = 1000

def bin_to_float_csv(bin_path, out_csv_path, n_sample):
    with open(bin_path, "rb") as f:
        bs = f.read()
    data = np.array(struct.unpack("<" + "f"*n_sample, bs), dtype=np.float32)
    np.savetxt(out_csv_path, data, fmt="%.9g")
    return data

def plot_compare(theory, fpga, err, title_name):
    plt.rcParams['figure.dpi'] = 300
    plt.figure(figsize=(12,5))
    plt.subplot(2,1,1)
    plt.plot(theory, label="Python Theory", linewidth=1.2)
    plt.plot(fpga, label="FPGA Measured", linestyle="--", linewidth=1.2)
    plt.title(f"{title_name} (Full 1000 Samples)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.subplot(2,1,2)
    plt.plot(err, color="#c82423", linewidth=1)
    plt.title("Absolute Error")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    plt.figure(figsize=(10,5))
    plt.subplot(2,1,1)
    plt.plot(theory[:51], label="Python Theory", linewidth=1.3, marker='.')
    plt.plot(fpga[:51], label="FPGA Measured", linestyle="--", linewidth=1.3, marker='.')
    plt.title(f"{title_name} (Zoom in First 51 Samples)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.subplot(2,1,2)
    plt.plot(err[:51], color="#c82423", linewidth=1.2, marker='.')
    plt.title("Absolute Error (Zoom in First 51 Samples)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# 实测耗时
# 数据来源：2026-10-24 最终板测记录（SDK Expressions 同屏截图，即技术报告图12 那一次运行）
#   计数口径：COUNTS_PER_SECOND = 333,333,343（Global Timer = CPU 666.67 MHz / 2）
#   正弦：hw 32,096 计数 -> 96.2880 us ；sw 823,108 计数 -> 2469.3239 us
#   混频：hw 31,837 计数 -> 95.5110 us ；sw 822,907 计数 -> 2468.7209 us
#   对照比（ARM 纯计算 ÷ FPGA 端到端）：正弦 25.65、混频 25.85
# 说明：同一组数据必须取自同一次运行，不可跨运行取用（早期版本曾混用另一次运行的
#       96.3210/95.4480 与 2468.6969，导致比值分别偏成 25.64/25.86）。
time_arm_sine = 2469.3239
time_fpga_sine = 96.2880
time_arm_mixed = 2468.7209
time_fpga_mixed = 95.5110

# 加载理论golden基准
golden_sine = np.loadtxt("ref_sine.csv", dtype=np.float32)
golden_mixed = np.loadtxt("ref_mixed.csv", dtype=np.float32)

# 解析新增性能测试bin
fpga_sine_perf = bin_to_float_csv("fir_sine_fpga_perf_1000.bin", "fir_sine_fpga_perf.csv", SAMPLE_NUM)
fpga_mixed_perf = bin_to_float_csv("fir_mixed_fpga_perf_1000.bin", "fir_mixed_fpga_perf.csv", SAMPLE_NUM)

# 误差计算
err_sine_perf = np.abs(golden_sine - fpga_sine_perf)
err_mixed_perf = np.abs(golden_mixed - fpga_mixed_perf)

max_err_sine = np.max(err_sine_perf)
rmse_sine = np.sqrt(np.mean(err_sine_perf**2))
max_err_mixed = np.max(err_mixed_perf)
rmse_mixed = np.sqrt(np.mean(err_mixed_perf**2))

# 计算对照比
ratio_sine = time_arm_sine / time_fpga_sine
ratio_mixed = time_arm_mixed / time_fpga_mixed

print("======= 正弦激励（性能测试版本） =======")
print(f"ARM纯计算耗时：{time_arm_sine:.4f} μs")
print(f"FPGA端到端耗时：{time_fpga_sine:.4f} μs")
print(f"对照比：{ratio_sine:.2f}")
print(f"最大绝对误差：{max_err_sine:.8e}")
print(f"RMSE：{rmse_sine:.8e}")

print("\n======= 混频激励（性能测试版本） =======")
print(f"ARM纯计算耗时：{time_arm_mixed:.4f} μs")
print(f"FPGA端到端耗时：{time_fpga_mixed:.4f} μs")
print(f"对照比：{ratio_mixed:.2f}")
print(f"最大绝对误差：{max_err_mixed:.8e}")
print(f"RMSE：{rmse_mixed:.8e}")

# 复用绘图函数画图
plot_compare(golden_sine, fpga_sine_perf, err_sine_perf, "Sine Wave (Performance Test)")
plot_compare(golden_mixed, fpga_mixed_perf, err_mixed_perf, "Mixed-Frequency (Performance Test)")







