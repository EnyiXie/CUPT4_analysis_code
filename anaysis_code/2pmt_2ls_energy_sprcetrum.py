"""
=============================================================================
@file      2pmt_2ls_energy_sprcetrum.py
@brief     用于描绘2ls幅度能谱以及2pmt的幅度与积分能谱
@details   分别统计上下液闪的幅度能谱,默认幅度为mpd-4走过的正值,对于ps则默认为赋值,
            并给予电荷积分与幅度测绘，
=============================================================================
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ROOT 
from tqdm import tqdm # 用于显示进度条

# ================= 配置区域 =================
# 1. 你的 CSV 文件夹路径 (请修改为你的真实路径，注意路径斜杠)
FOLDER_PATH = r"/home/ruler/cupt4/det1/coincidence/data/pmt5-8中心位置"

# 2. 积分窗口设置 (根据示波器 0.32ns 的采样率)
# 塑闪发光快，峰前取 500 个点(160ns)，峰后取 1000 个点(320ns)
PRE_PEAK_POINTS = 500 
POST_PEAK_POINTS = 1000
DT_NS = 0.32 # 采样间隔 0.32 ns (3.2e-10 s)

# ================= 辅助函数 =================
def find_header_line(filepath):
    """
    自动寻找包含 'TIME,CH1,CH2' 的数据起始行，
    避免因为不同示波器设置导致表头行数变化。
    """
    with open(filepath, 'r') as f:
        for i, line in enumerate(f):
            if 'TIME' in line and 'CH1' in line:
                return i
    return 21 # 默认 fallback

# ================= 数据容器 =================
# 液闪 (仅幅度)
ls_ch3_amps = []
ls_ch4_amps = []

# 塑闪 (幅度 + 积分)
ps_ch1_amps = []
ps_ch1_ints = []
ps_ch2_amps = []
ps_ch2_ints = []

# ================= 主循环处理 =================
# 获取所有 csv 文件
file_list = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))
print(f"共找到 {len(file_list)} 个 CSV 文件，开始处理...")

for file in tqdm(file_list, desc="Processing waveforms"):
    try:
        # 1. 读取数据
        header_idx = find_header_line(file)
        # 只读取我们需要的列，提升速度
        df = pd.read_csv(file, skiprows=header_idx, usecols=['TIME', 'CH1', 'CH2', 'CH3', 'CH4'])
        
        # 2. 转换为 numpy 数组提速
        ch1 = df['CH1'].values
        ch2 = df['CH2'].values
        ch3 = df['CH3'].values
        ch4 = df['CH4'].values
        
        # 3. 动态扣除基线 (取前 1000 个纯噪声点算平均)
        # 这一步完美解决了你说的“塑闪基线偏离了 5mV”的问题
        bl_1, bl_2 = np.mean(ch1[:1000]), np.mean(ch2[:1000])
        bl_3, bl_4 = np.mean(ch3[:1000]), np.mean(ch4[:1000])
        
        # 塑闪是原始负脉冲，保留负号翻转为正，方便算面积和找峰
        ch1_sig = -(ch1 - bl_1)
        ch2_sig = -(ch2 - bl_2)
        
        # 液闪走了成形已经是正脉冲了，只扣基线，绝对不能加负号！
        ch3_sig = ch3 - bl_3
        ch4_sig = ch4 - bl_4
        
        # 4. 提取液闪幅度 (单位: V -> mV)
        ls_ch3_amps.append(np.max(ch3_sig) * 1000)
        ls_ch4_amps.append(np.max(ch4_sig) * 1000)
        
        # 5. 提取塑闪幅度和积分
        # CH1
        amp_1 = np.max(ch1_sig)
        ps_ch1_amps.append(amp_1 * 1000) # 转换为 mV
        peak_idx_1 = np.argmax(ch1_sig)
        # 设定积分安全边界，防止峰太靠前或太靠后导致数组越界
        start_1 = max(0, peak_idx_1 - PRE_PEAK_POINTS)
        end_1 = min(len(ch1_sig), peak_idx_1 + POST_PEAK_POINTS)
        # 面积 = sum(V) * dt (单位: V * ns)
        ps_ch1_ints.append(np.sum(ch1_sig[start_1:end_1]) * DT_NS)
        
        # CH2
        amp_2 = np.max(ch2_sig)
        ps_ch2_amps.append(amp_2 * 1000) # 转换为 mV
        peak_idx_2 = np.argmax(ch2_sig)
        start_2 = max(0, peak_idx_2 - PRE_PEAK_POINTS)
        end_2 = min(len(ch2_sig), peak_idx_2 + POST_PEAK_POINTS)
        ps_ch2_ints.append(np.sum(ch2_sig[start_2:end_2]) * DT_NS)
        
    except Exception as e:
        # 如果某个文件损坏或格式不对，跳过并记录
        print(f"\n跳过出错的文件 {file}: {e}")
        continue

# 转换为 numpy 方便画图
# 转换为 numpy 数组
ls_ch3_amps = np.array(ls_ch3_amps)
ls_ch4_amps = np.array(ls_ch4_amps)
ps_ch1_amps = np.array(ps_ch1_amps)
ps_ch1_ints = np.array(ps_ch1_ints)
ps_ch2_amps = np.array(ps_ch2_amps)
ps_ch2_ints = np.array(ps_ch2_ints)

# ================= 异常数据清洗 =================
# 剔除所有的 inf (无穷大) 和 NaN (非数字)
ls_ch3_amps = ls_ch3_amps[np.isfinite(ls_ch3_amps)]
ls_ch4_amps = ls_ch4_amps[np.isfinite(ls_ch4_amps)]

ps_ch1_amps = ps_ch1_amps[np.isfinite(ps_ch1_amps)]
ps_ch1_ints = ps_ch1_ints[np.isfinite(ps_ch1_ints)]

ps_ch2_amps = ps_ch2_amps[np.isfinite(ps_ch2_amps)]
ps_ch2_ints = ps_ch2_ints[np.isfinite(ps_ch2_ints)]

print(f"清洗完毕。有效塑闪CH1幅度数据量: {len(ps_ch1_amps)}")

# ================= 绘图部分 =================
# 注释掉下面两行，避免 Linux 下报字体找不到的错
# plt.rcParams['font.sans-serif'] = ['SimHei'] 
# plt.rcParams['axes.unicode_minus'] = False 

# # --- 图 1：液闪幅度谱 ---
# plt.figure(figsize=(10, 6))
# plt.hist(ls_ch3_amps, bins=250, alpha=0.6, label='LS_CH3', color='blue', histtype='step', linewidth=2.0)
# plt.hist(ls_ch4_amps, bins=250, alpha=0.6, label='LS_CH4', color='red', histtype='step', linewidth=2.0)
# plt.yscale('log')  # <--- 添加这一行，使纵轴变为对数坐标
# plt.title('Liquid Scintillator Amplitude Spectrum')
# plt.xlabel('Amplitude (mV)')
# plt.ylabel('Counts')
# plt.legend()
# plt.grid(True, alpha=0.3)
# plt.tight_layout()
# plt.show()

# # --- 图 2：塑闪幅度谱 ---
# plt.figure(figsize=(10, 6))
# plt.hist(ps_ch1_amps, bins=250, alpha=0.6, label='PS_CH1', color='green', histtype='step', linewidth=2.0)
# plt.hist(ps_ch2_amps, bins=250, alpha=0.6, label='PS_CH2', color='orange', histtype='step', linewidth=2.0)
# plt.yscale('log') 
# plt.title('Plastic Scintillator Amplitude Spectrum')
# plt.xlabel('Amplitude (mV)')
# plt.ylabel('Counts')
# plt.legend()
# plt.grid(True, alpha=0.3)
# plt.tight_layout()
# plt.show()

# #--- 图 3：塑闪积分谱 ---
# plt.figure(figsize=(10, 6))
# plt.hist(ps_ch1_ints, bins=250, alpha=0.6, label='PS_CH1', color='green', histtype='step', linewidth=2.0)
# plt.hist(ps_ch2_ints, bins=250, alpha=0.6, label='PS_CH2', color='orange', histtype='step', linewidth=2.0)
# plt.yscale('log') 
# plt.title('Plastic Scintillator Integral Spectrum')
# plt.xlabel('Integral (V*ns)')
# plt.ylabel('Counts')
# plt.legend()
# plt.grid(True, alpha=0.3)
# plt.tight_layout()
# plt.show()

# ================= 绘图部分 (PyROOT 版) =================
import sys

def draw_root_hist(data_list, labels, colors, title, xtitle, ytitle, filename):
    """
    辅助函数：快速使用 ROOT 绘制对比直方图
    """
    # 1. 创建画布
    ROOT.gStyle.SetOptStat(0)     # 关掉右上角统计框
    ROOT.gStyle.SetPadTickX(1)    # 顶部添加刻度线 (形成封闭边框)
    ROOT.gStyle.SetPadTickY(1)    # 右侧添加刻度线 (形成封闭边框)
    ROOT.gStyle.SetLineWidth(2)   # 刻度线加粗
    ROOT.gStyle.SetFrameLineWidth(2) # 边框加粗
    ROOT.gStyle.SetTextFont(42)   # 标准高清字体
    c = ROOT.TCanvas(f"c_{filename}", title, 800, 600)
    c.SetLogy() # 开启对数坐标
    #c.SetGrid()

    # 2. 计算 X 轴范围
    all_data = np.concatenate(data_list)
    if len(all_data) == 0: return None
    x_min = np.min(all_data) * 0.9
    x_max = np.max(all_data) * 1.1
    
    hists = []
    leg = ROOT.TLegend(0.7, 0.75, 0.9, 0.9)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)

    for i, (data, label, color) in enumerate(zip(data_list, labels, colors)):
        # 创建直方图 (名字不能重复)
        h = ROOT.TH1F(f"h_{filename}_{i}", f"{title};{xtitle};{ytitle}", 700, x_min, x_max)
        # 填充数据
        for val in data:
            h.Fill(val)
        
        # 样式设置
        h.SetLineColor(color)
        h.SetLineWidth(2)
        h.SetStats(0) # 关闭统计框，让图面更整洁
        h.SetMinimum(0.5) # 对数坐标下最小值设为0.5防止绘图错误
        
        # 绘制
        draw_opt = "HIST" if i == 0 else "HIST SAME"
        h.Draw(draw_opt)
        
        leg.AddEntry(h, label, "l")
        hists.append(h) # 保持引用，防止被垃圾回收

    leg.Draw()
    c.Update()
    c.SaveAs(f"{filename}.pdf")
    return c, hists, leg

# --- 开始绘图 ---
# 设置 ROOT 全局样式
ROOT.gStyle.SetOptTitle(1)
ROOT.gStyle.SetTextFont(42)

# 1. 液闪幅度谱
# res1 = draw_root_hist(
#     [ls_ch3_amps, ls_ch4_amps], 
#     ['LS_CH3', 'LS_CH4'], 
#     [ROOT.kBlue, ROOT.kRed],
#     "Liquid Scintillator Amplitude Spectrum", "Amplitude (mV)", "Counts", "ls_amplitude"
# )

# 2. 塑闪幅度谱
res2 = draw_root_hist(
    [ps_ch1_amps, ps_ch2_amps], 
    ['PS_CH1', 'PS_CH2'], 
    [ROOT.kGreen+2, ROOT.kOrange+7],
    "Plastic Scintillator Amplitude Spectrum", "Amplitude (mV)", "Counts", "ps_amplitude"
)

# 3. 塑闪积分谱
res3 = draw_root_hist(
    [ps_ch1_ints, ps_ch2_ints], 
    ['PS_CH1', 'PS_CH2'], 
    [ROOT.kGreen+2, ROOT.kOrange+7],
    "Plastic Scintillator Integral Spectrum", "Integral (V*ns)", "Counts", "ps_integral"
)

print("\n所有图表已生成。")
# 如果是在终端运行，保持窗口开启
if not ROOT.gROOT.IsBatch():
    input("按回车键退出...")