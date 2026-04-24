"""
=============================================================================
@file      1pmt_2ls_energy_sprcetrum.py
@brief     用于描绘2ls幅度能谱以及1pmt的幅度与积分能谱
@details   分别统计上下液闪的幅度能谱,默认幅度为mpd-4走过的正值,对于ps则默认为赋值,
            并给予电荷积分与幅度测绘，
=============================================================================
"""
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

# ================= 配置区域 =================
# 1. 你的新 CSV 文件夹路径
FOLDER_PATH = r"/home/ruler/cupt4/det1/coincidence/4.9" 

# 2. 积分窗口设置 (根据示波器 0.32ns 的采样率)
PRE_PEAK_POINTS = 500 
POST_PEAK_POINTS = 1000
DT_NS = 0.32 # 采样间隔 0.32 ns (3.2e-10 s)

# ================= 辅助函数 =================
def find_header_line(filepath):
    """自动寻找表头起始行"""
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if 'TIME' in line and 'CH1' in line:
                return i
    return 21 # 默认 fallback

# ================= 数据容器 =================
# 塑闪 CH1 (负脉冲：需翻转算幅度和积分)
ps_ch1_amps = []
ps_ch1_ints = []

# 液闪 CH2, CH3 (正脉冲：成形后只算幅度)
ls_ch2_amps = []
ls_ch3_amps = []

# ================= 主循环处理 =================
file_list = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
print(f"共找到 {len(file_list)} 个 CSV 文件，开始处理...")

for file in tqdm(file_list, desc="Processing waveforms"):
    try:
        header_idx = find_header_line(file)
        # 注意：这里我们移除了 'CH4'，只读取有用的前四列，加快读取速度
        df = pd.read_csv(file, skiprows=header_idx, usecols=['TIME', 'CH1', 'CH2', 'CH3'])
        
        # 转换为 numpy 数组提速
        ch1 = df['CH1'].values
        ch2 = df['CH2'].values
        ch3 = df['CH3'].values
        
        # 动态扣除基线 (取前 1000 个纯噪声点算平均)
        bl_1 = np.mean(ch1[:1000])
        bl_2 = np.mean(ch2[:1000])
        bl_3 = np.mean(ch3[:1000])
        
        # --- 信号极性处理 (核心改动区) ---
        # 塑闪(CH1)是负脉冲，加负号翻转为正
        ch1_sig = -(ch1 - bl_1)
        # 液闪(CH2, CH3)走过成形是正脉冲，绝对不加负号，只扣基线
        ch2_sig = ch2 - bl_2
        ch3_sig = ch3 - bl_3
        
        # --- 提取液闪幅度 (转 mV) ---
        ls_ch2_amps.append(np.max(ch2_sig) * 1000)
        ls_ch3_amps.append(np.max(ch3_sig) * 1000)
        
        # --- 提取塑闪 CH1 幅度与积分 ---
        amp_1 = np.max(ch1_sig)
        ps_ch1_amps.append(amp_1 * 1000) 
        
        peak_idx_1 = np.argmax(ch1_sig)
        start_1 = max(0, peak_idx_1 - PRE_PEAK_POINTS)
        end_1 = min(len(ch1_sig), peak_idx_1 + POST_PEAK_POINTS)
        ps_ch1_ints.append(np.sum(ch1_sig[start_1:end_1]) * DT_NS)
        
    except Exception as e:
        print(f"\n跳过出错的文件 {file}: {e}")
        continue

# ================= 异常数据清洗 =================
# 转换为 numpy 数组
ps_ch1_amps = np.array(ps_ch1_amps)
ps_ch1_ints = np.array(ps_ch1_ints)
ls_ch2_amps = np.array(ls_ch2_amps)
ls_ch3_amps = np.array(ls_ch3_amps)

# 剔除所有的 inf (无穷大) 和 NaN (非数字)
ps_ch1_amps = ps_ch1_amps[np.isfinite(ps_ch1_amps)]
ps_ch1_ints = ps_ch1_ints[np.isfinite(ps_ch1_ints)]
ls_ch2_amps = ls_ch2_amps[np.isfinite(ls_ch2_amps)]
ls_ch3_amps = ls_ch3_amps[np.isfinite(ls_ch3_amps)]

print(f"清洗完毕。有效数据量: {len(ps_ch1_amps)}")

# ================= 绘图部分 =================

# --- 图 1：液闪幅度谱 (CH2 & CH3) ---
plt.figure(figsize=(10, 6))
# 关键改动：histtype 改为 'step'，去掉 alpha 透明度，增加 linewidth 让线条加粗
plt.hist(ls_ch2_amps, bins=300, label='LS_CH2 (Shaped)', color='blue', histtype='step', linewidth=2.0)
plt.hist(ls_ch3_amps, bins=300, label='LS_CH3 (Shaped)', color='red', histtype='step', linewidth=2.0)
plt.yscale('log') 
plt.title('Liquid Scintillator Amplitude Spectrum')
plt.xlabel('Amplitude (mV)')
plt.ylabel('Counts')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# --- 图 2：塑闪幅度谱 (CH1 独苗) ---
plt.figure(figsize=(10, 6))
plt.hist(ps_ch1_amps, bins=300, alpha=0.6, label='PS_CH1', color='green', histtype='step', linewidth=2.0)
plt.yscale('log') 
plt.title('Plastic Scintillator Amplitude Spectrum')
plt.xlabel('Amplitude (mV)')
plt.ylabel('Counts')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# --- 图 3：塑闪积分谱 (CH1 独苗) ---
plt.figure(figsize=(10, 6))
plt.hist(ps_ch1_ints, bins=500, alpha=0.6, label='PS_CH1', color='green', histtype='step', linewidth=2.0)
plt.yscale('log') 
plt.title('Plastic Scintillator Integral Spectrum')
plt.xlabel('Integral (V*ns)')
plt.ylabel('Counts')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()