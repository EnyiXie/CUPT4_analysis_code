"""
=============================================================================
@file      check_liquid.py
@brief     暴躁老哥专用：液闪增益不匹配排查工具
@details   分别统计上下液闪单通道超过绝对阈值的 Event 数量，并绘制幅度分布对比图，
           一眼看出哪个通道拉了胯！
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# ================= 配置区 =================
FILE_PREFIX =  r"/home/ruler/cupt4/det3/coincidence/4.10_pmt9-10"
FILE_LS_UP   = f"{FILE_PREFIX}_CH0.csv"  # 你的第一个液闪 (假设是 CH0)
FILE_LS_DOWN = f"{FILE_PREFIX}_CH3.csv"  # 你的第二个液闪 (你刚才说是 CH3，请确认)

# 你的终极审判红线
THRESHOLD = 12000  

# 液闪 MPD-4 信号凸起的有效时间窗
WINDOW_LS = (250, 650)
# ==========================================

print("⏳ 正在把这两个倒霉液闪的数据拉进内存...")
if not (os.path.exists(FILE_LS_UP) and os.path.exists(FILE_LS_DOWN)):
    print("❌ 错误: 找不到文件，检查一下名字！")
    sys.exit()

data_up   = np.loadtxt(FILE_LS_UP, delimiter=',')
data_down = np.loadtxt(FILE_LS_DOWN, delimiter=',')
num_events = data_up.shape[0]

# 计数器
count_up_pass = 0
count_down_pass = 0

# 存放所有的峰值，用于画对比图
peaks_up = []
peaks_down = []

print(f"🚀 开始审问这 {num_events} 个 Event...")

for i in range(num_events):
    wf_up   = data_up[i]
    wf_down = data_down[i]
    
    # 找出这个时间窗内的最高点 (直接找原始值)
    peak_up   = np.max(wf_up[WINDOW_LS[0]:WINDOW_LS[1]])
    peak_down = np.max(wf_down[WINDOW_LS[0]:WINDOW_LS[1]])
    
    peaks_up.append(peak_up)
    peaks_down.append(peak_down)
    
    if peak_up > THRESHOLD:
        count_up_pass += 1
        
    if peak_down > THRESHOLD:
        count_down_pass += 1

# ================= 审判结果输出 =================
print("\n" + "🔥"*25)
print(f"  总 Event 数: {num_events}")
print("-" * 50)
print(f"  👆 液闪 A (CH0) 大于 {THRESHOLD} 的数量: {count_up_pass} 个")
print(f"  👇 液闪 B (CH3) 大于 {THRESHOLD} 的数量: {count_down_pass} 个")
print("-" * 50)

# 计算落差比例
diff_ratio = abs(count_up_pass - count_down_pass) / max(count_up_pass, count_down_pass, 1) * 100
if diff_ratio > 20:
    print(f"  🤬 妈的，这两个通道差了 {diff_ratio:.1f}%，绝对有一个增益或者高压给错了！")
else:
    print("  🤔 诶？这两个通道数量差不多啊，难道问题出在别的地方？")
print("🔥"*25 + "\n")

# ================= 画图：让增益差距现原形 =================
plt.figure(figsize=(12, 6), dpi=100)

# 用透明度叠加画两个液闪的峰值分布
plt.hist(peaks_up,   bins=100, range=(8000, 16500), color='red',  alpha=0.6, label='Liquid Scintillator A (CH0)', edgecolor='black', linewidth=0.5)
plt.hist(peaks_down, bins=100, range=(8000, 16500), color='blue', alpha=0.6, label='Liquid Scintillator B (CH3)', edgecolor='black', linewidth=0.5)

# 画那条 12000 的生死线
plt.axvline(x=THRESHOLD, color='green', linestyle='dashed', linewidth=2, label=f'Threshold: {THRESHOLD}')

plt.title("Peak Value Distribution of Two Liquid Scintillators\n(Looking for Gain Mismatch)", fontsize=16, fontweight='bold')
plt.xlabel("Raw ADC Peak Value (Baseline ~8192, Saturation ~16383)", fontsize=14)
plt.ylabel("Counts", fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()