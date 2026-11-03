#!/usr/bin/env python
# coding: utf-8

# In[1]:


# 信号与系数生成
import numpy as np
import matplotlib.pyplot as plt

# ============ 参数 ============
fs = 1000          # 采样率 1000 Hz
T  = 1.0           # 信号时长 1 秒
t  = np.arange(0, T, 1/fs)   # 时间轴

# ============ 三个成分 ============
# 1. 目标信号：5Hz 低频正弦波（后面 FIR 要保住它）
f_target = 5
clean = np.sin(2 * np.pi * f_target * t)

# 2. 高频干扰：50Hz（后面 FIR 要滤掉它）
f_interf = 50
interference = 0.5 * np.sin(2 * np.pi * f_interf * t)

# 3. 高斯白噪声
noise = 0.3 * np.random.randn(len(t))

# ============ 合成最终信号 ============
signal = clean + interference + noise

# 存下来，明天 firwin 那步直接用
np.save('signal.npy', signal)
np.save('t.npy', t)
np.save('clean.npy', clean)

# ============ 画出来 ============
plt.figure(figsize=(12, 4))
plt.plot(t, signal, label='signal (noisy)', alpha=0.6)
plt.plot(t, clean, 'r', label='clean 5Hz', linewidth=2)
plt.xlabel('time (s)')
plt.ylabel('amplitude')
plt.legend()
plt.title('Input signal: 5Hz + 50Hz interference + noise')
plt.show()


# In[ ]:




