"""
=============================================================================
@file      mpd-4_coin.py
@brief     宇宙射线符合实验 - 绝对探测效率计算与缪子能谱提取
@details   本程序读取已合并(Merged)的各通道完整 CSV 波形数据。
           1. 离线符合 (Offline Tagging): 利用上下液闪的高阈值条件，彻底过滤
              环境低能伽马本底，精确锁定 100% 真实的穿透高能缪子。
           2. 效率计算 (Efficiency): 统计中间塑闪对真实缪子的响应比例。
           3. 电荷积分 (Charge Integration): 对真实缪子的快波形进行求面积积分，
              绘制纯净、无本底污染的朗道沉积能谱 (Landau Distribution)。
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# =======================================================================
# [1] 文件路径配置区 (对应合并后的 CSV 文件)
# =======================================================================
FILE_PREFIX = "test1"
FILE_LS1 = f"{FILE_PREFIX}_CH0.csv"  # 通道0: 液闪 1 (成形正向信号)
FILE_LS2 = f"{FILE_PREFIX}_CH3.csv"  # 通道3: 液闪 2 (成形正向信号)
FILE_PS  = f"{FILE_PREFIX}_CH2.csv"  # 通道1: 塑闪 1 (原始负向快信号)

# =======================================================================
# [2] 物理逻辑判决参数 (至关重要)
# =======================================================================
# --- 液闪参数 (作为裁判: Tagging) ---
WINDOW_LS = (250, 650)         # MPD-4 液闪脉冲凸起的有效时间窗
ABS_THRESHOLD_LS = 12000       # 绝对极高阈值 (基线约8192)：专抓导致高能饱和的纯缪子！

# --- 塑闪参数 (作为被测设备: Detection) ---
BASELINE_RANGE_PS = (0, 200)   # 采样前 200 个点计算背景基线
WINDOW_PS = (250, 350)         # 塑闪快信号落下的有效时间窗
REL_THRESHOLD_PS = 100         # 相对阈值：脉冲相对于基线往下掉 100 个 ADC 即认为打火成功

# =======================================================================
# [3] 加载大型数据矩阵
# =======================================================================
print(f"⏳ 正在将大体量合并数据载入内存，这可能需要几秒钟...")
if not (os.path.exists(FILE_LS1) and os.path.exists(FILE_LS2) and os.path.exists(FILE_PS)):
    print("❌ 错误: 找不到指定的合并 CSV 文件，请检查文件名拼写！")
    sys.exit()

data_ls1 = np.loadtxt(FILE_LS1, delimiter=',')
data_ls2 = np.loadtxt(FILE_LS2, delimiter=',')
data_ps  = np.loadtxt(FILE_PS,  delimiter=',')

# 确保三个通道的事件总数严格一致
num_events = data_ps.shape[0]
if not (data_ls1.shape[0] == data_ls2.shape[0] == num_events):
    print("❌ 错误: 三个通道的事件数量不一致！数据合并可能出错。")
    sys.exit()

# =======================================================================
# [4] 核心离线逐事例分析 (Event-by-Event Analysis)
# =======================================================================
total_true_muons = 0   # [分母] 满足“两块液闪都出了超大信号”的真实事例数
ps_detected_muons = 0  # [分子] 在真缪子前提下，塑闪有反应的捕获事例数
integral_list = []     # 存放用于绘制能谱的电荷积分面积

print(f"🚀 开始进行离线符合物理分析 (共计解析 {num_events} 个波形事例) ...")

for i in range(num_events):
    
    # ---------------------------------------------------------
    # 步骤 A: 裁判组判决 (Tagging) - 寻找真理缪子
    # ---------------------------------------------------------
    wf_ls1 = data_ls1[i]
    wf_ls2 = data_ls2[i]
    
    # 在 250-650 的窗口里，直接看原始信号有没有超过 12000 的绝对红线
    peak_raw_ls1 = np.max(wf_ls1[WINDOW_LS[0]:WINDOW_LS[1]])
    peak_raw_ls2 = np.max(wf_ls2[WINDOW_LS[0]:WINDOW_LS[1]])
    
    # 【逻辑与 (AND)】 如果上下两个液闪都触发了极高能信号（确认贯穿）：
    if peak_raw_ls1 > ABS_THRESHOLD_LS and peak_raw_ls2 > ABS_THRESHOLD_LS:
        total_true_muons += 1  # 确认发现一颗真实缪子！(分母加1)
        
        # ---------------------------------------------------------
        # 步骤 B: 被测组表现 (Detection) - 考核塑闪探测力
        # ---------------------------------------------------------
        wf_ps = data_ps[i]
        
        # 塑闪是原始负信号，计算前200个点的基线并翻转波形 (让脉冲朝上，正数好算)
        bl_ps = np.mean(wf_ps[BASELINE_RANGE_PS[0]:BASELINE_RANGE_PS[1]])
        wf_ps_pos = bl_ps - wf_ps
        
        # 在 250-350 的塑闪严格时间窗内找最大的突起 (排除暗噪声干扰)
        peak_ps = np.max(wf_ps_pos[WINDOW_PS[0]:WINDOW_PS[1]])
        
        # 如果塑闪成功捕捉到了这颗被裁判组“点名”的缪子：
        if peak_ps > REL_THRESHOLD_PS:
            ps_detected_muons += 1  # 塑闪探测成功！(分子加1)
            
            # ---------------------------------------------------------
            # 步骤 C: 提取沉积能量 (Charge Integration) - 绘制能谱用
            # ---------------------------------------------------------
            # 寻找该波形区间内最顶峰所在的精确索引位置
            peak_idx = WINDOW_PS[0] + np.argmax(wf_ps_pos[WINDOW_PS[0]:WINDOW_PS[1]])
            
            # 积分动态区间：峰值前 10 个点 到 峰值后 30 个点 (包容脉冲长尾)
            int_start = max(0, peak_idx - 10)
            int_end = min(len(wf_ps_pos), peak_idx + 30)
            
            # 对该区间内翻转后的波形求和，得到电荷量 Q (正比于沉积能量 E)
            charge = np.sum(wf_ps_pos[int_start:int_end])
            integral_list.append(charge)

# =======================================================================
# [5] 实验分析报告打印
# =======================================================================
print("\n" + "★"*55)
print(f"  📊 硬件写入 FADC 事件总数 (含低能假符合) : {num_events}")
print(f"  🎯 离线硬件确定的 纯净宇宙缪子数 (分母)   : {total_true_muons}")
print(f"  ✨ 塑料闪烁体实际 捕获反应的次数 (分子)   : {ps_detected_muons}")

eff = 0.0
if total_true_muons > 0:
    eff = (ps_detected_muons / total_true_muons) * 100
    print(f"\n  👉  当前塑闪(CH1) 的绝对探测效率为: {eff:.2f}%  👈")
else:
    print("\n  ⚠️ 警告: 未捕获到任何过阈值的真缪子！")
    print("     可能原因: 液闪阈值(12000)过高，或本次数据样本太少。")
print("★"*55 + "\n")

# =======================================================================
# [6] 高质量学术绘图：纯净的宇宙射线缪子沉积谱 (Landau Spectrum)
# =======================================================================
if len(integral_list) > 0:
    # 设置画板大小及分辨率
    plt.figure(figsize=(10, 6), dpi=100)
    
    # 绘制直方图：140 个 bins 可展现丰富的谱线细节
    counts, bins, patches = plt.hist(
        integral_list, 
        bins=540, 
        color='#2A75D3',       # 沉稳的学术蓝
        alpha=0.85,            # 透明度
        edgecolor='black',     # 给每个柱子加个细致的黑边
        linewidth=0.8
    )
    
    # 图表标题与注释
    plt.title(
        "Cosmic Ray Muon Deposition Energy Spectrum\n" + 
        f"Plastic Scintillator Coincidence Efficiency: {eff:.2f}%", 
        fontsize=16, 
        fontweight='bold', 
        pad=15
    )
    plt.xlabel("Integrated Charge (ADC $\\times$ bins) $\\propto$ Deposited Energy", fontsize=14)
    plt.ylabel("Counts per Bin", fontsize=14)
    
    # 坐标轴美化
    plt.tick_params(axis='both', which='major', labelsize=12)
    plt.grid(True, linestyle='--', alpha=0.6, axis='y') # 只保留水平虚线辅助线
    
    # 显示结果
    plt.tight_layout()
    plt.show()