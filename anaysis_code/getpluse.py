import numpy as np
import matplotlib.pyplot as plt

# ================= 修改这里为你真实的液闪通道文件 =================
file_LS1 = "test1_Run0_CH0.csv"  # 假设 CH0 是上液闪
file_LS2 = "test1_Run0_CH3.csv"  # 假设 CH3 是下液闪
file_PS  = "test1_Run0_CH1.csv"  # 塑闪 (作为时间参考)
# ================================================================

print("正在加载数据...")
data_ls1 = np.loadtxt(file_LS1, delimiter=',')
data_ls2 = np.loadtxt(file_LS2, delimiter=',')
data_ps  = np.loadtxt(file_PS, delimiter=',')

# 创建一个包含 3 个子图的画板
fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 画前 15 个事件的波形
num_plot = 35
for i in range(num_plot):
    axs[0].plot(data_ls1[i], alpha=0.6)
    axs[1].plot(data_ls2[i], alpha=0.6)
    axs[2].plot(data_ps[i],  alpha=0.6)

# 设置标题和标签
axs[0].set_title("Liquid Scintillator 1 (MPD-4 Shaped)", fontsize=12, fontweight='bold')
axs[0].set_ylabel("ADC Value")

axs[1].set_title("Liquid Scintillator 2 (MPD-4 Shaped)", fontsize=12, fontweight='bold')
axs[1].set_ylabel("ADC Value")

axs[2].set_title("Plastic Scintillator (Raw PMT)", fontsize=12, fontweight='bold')
axs[2].set_xlabel("Time Bin (2ns/bin)")
axs[2].set_ylabel("ADC Value")

plt.tight_layout()
plt.show()