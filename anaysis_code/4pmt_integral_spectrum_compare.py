"""
=============================================================================
@file      4pmt_integral_spectrum_compare.py
@brief     对比4个PMT的积分能谱 (适配 MSO44 示波器导出的 CSV 格式)
=============================================================================
"""

import os
import glob
import random
import numpy as np
import pandas as pd
import ROOT 
from tqdm import tqdm

# ================= 配置区域 =================
TARGET_EVENTS = 5000

# 1. 基础路径配置
BASE_DIR = r"/home/ruler/cupt4/det3/coincidence/data"

# 2. 文件夹与通道映射字典 (根据你截图的真实路径配置)
# 键: 文件夹名称， 值: 该文件夹下 CH1 对应的 PMT 名称
FOLDER_MAPPING = {
    os.path.join(BASE_DIR, "pmt9new-10第一象限"): "PMT9new",
    os.path.join(BASE_DIR, "pmt10-11中心位置"): "PMT11",
    os.path.join(BASE_DIR, "pmt10-12中心位置"): "PMT12"
}

# 积分窗口设置 
PRE_PEAK_POINTS = 500 
POST_PEAK_POINTS = 1000
DT_NS = 0.32 

# ================= 数据容器 =================
pmt_integrals = {
    "PMT9new": [],
    "PMT10": [],
    "PMT11": [],
    "PMT12": []
}

# ================= 辅助函数 =================
def find_header_line(filepath):
    """
    精准定位 MSO44 示波器 CSV 的数据表头行
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            # 寻找精确匹配的表头行
            if line.strip().startswith('TIME,CH1,CH2,CH3,CH4'):
                return i
    return 16 # 根据你提供的数据，fallback 到第 17 行 (索引 16)

# ================= 主循环处理 =================
for folder_path, ch1_name in FOLDER_MAPPING.items():
    if not os.path.exists(folder_path):
        print(f"\n❌ 警告: 找不到文件夹 {folder_path}，请检查路径！")
        continue
        
    file_list = glob.glob(os.path.join(folder_path, "*.csv"))
    if not file_list:
        print(f"\n⚠️ 警告: 文件夹 {folder_path} 中没有找到 csv 文件。")
        continue
        
    # 随机打乱文件列表
    random.shuffle(file_list)
    
    print(f"\n开始处理文件夹: {os.path.basename(folder_path)}")
    print(f"通道映射: CH1 -> {ch1_name}, CH2 -> PMT10")
    
    pbar = tqdm(total=TARGET_EVENTS, desc=f"Extracting {ch1_name}")
    
    for file in file_list:
        # 如果当前 CH1 对应的 PMT 抽满了，且 PMT10 也抽满了，就提前结束当前文件夹
        if len(pmt_integrals[ch1_name]) >= TARGET_EVENTS and len(pmt_integrals["PMT10"]) >= TARGET_EVENTS:
            break
            
        try:
            header_idx = find_header_line(file)
            
            # 使用 skiprows 跳过所有元数据，并明确指定只读取我们需要的那两列数据
            # 这样就算后面列有空缺或多了逗号，Pandas 也不会崩溃
            df = pd.read_csv(file, skiprows=header_idx, usecols=['CH1', 'CH2'])
            
            ch1 = df['CH1'].values
            ch2 = df['CH2'].values
            
            # 扣除基线 (前1000个点)
            bl_1, bl_2 = np.mean(ch1[:1000]), np.mean(ch2[:1000])
            
            # 翻转负脉冲
            ch1_sig = -(ch1 - bl_1)
            ch2_sig = -(ch2 - bl_2)
            
            # --- 处理 CH1 (对应 9new, 11, 12) ---
            if len(pmt_integrals[ch1_name]) < TARGET_EVENTS:
                peak_idx_1 = np.argmax(ch1_sig)
                start_1 = max(0, peak_idx_1 - PRE_PEAK_POINTS)
                end_1 = min(len(ch1_sig), peak_idx_1 + POST_PEAK_POINTS)
                int_1 = np.sum(ch1_sig[start_1:end_1]) * DT_NS
                
                if np.isfinite(int_1): 
                    pmt_integrals[ch1_name].append(int_1)
                    pbar.update(1)
            
            # --- 处理 CH2 (统一存放 PMT10) ---
            if len(pmt_integrals["PMT10"]) < TARGET_EVENTS:
                peak_idx_2 = np.argmax(ch2_sig)
                start_2 = max(0, peak_idx_2 - PRE_PEAK_POINTS)
                end_2 = min(len(ch2_sig), peak_idx_2 + POST_PEAK_POINTS)
                int_2 = np.sum(ch2_sig[start_2:end_2]) * DT_NS
                
                if np.isfinite(int_2):
                    pmt_integrals["PMT10"].append(int_2)
                    
        except Exception as e:
            # 静默跳过损坏的波形
            continue
            
    pbar.close()

# 转换为 numpy 数组并打印状态
print("\n================ 数据抽取完毕 ================")
for pmt in pmt_integrals:
    pmt_integrals[pmt] = np.array(pmt_integrals[pmt])
    print(f"{pmt} 有效事件数: {len(pmt_integrals[pmt])}")

# ================= 绘图部分 (PyROOT) =================
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)
ROOT.gStyle.SetLineWidth(2)
ROOT.gStyle.SetFrameLineWidth(2)
ROOT.gStyle.SetTextFont(42)

c = ROOT.TCanvas("c_compare", "4 PMTs Integral Comparison", 1000, 700)
c.SetLogy()

# 计算全局 X 轴范围 (取所有 PMT 数据的最值)
all_integrals = np.concatenate(list(pmt_integrals.values()))
if len(all_integrals) > 0:
    x_min = np.min(all_integrals) * 0.9
    x_max = np.max(all_integrals) * 1.1
else:
    x_min, x_max = 0, 1
# ... 前面的代码保持不变 ...

leg = ROOT.TLegend(0.75, 0.65, 0.9, 0.9)
leg.SetBorderSize(0)
leg.SetFillStyle(0)
leg.SetTextSize(0.03) # 如果觉得图例文字不够大，可以把这个数值调大 (比如 0.05)

colors = {
    "PMT9new": ROOT.kBlue,
    "PMT10": ROOT.kRed,
    "PMT11": ROOT.kGreen+2,
    "PMT12": ROOT.kOrange+7
}

hists = []
is_first = True

for pmt_name, data in pmt_integrals.items():
    if len(data) == 0:
        continue
        
    h = ROOT.TH1F(f"h_{pmt_name}", "4 PMTs Integral Spectrum Comparison;Integral (V*ns);Counts", 650, x_min, x_max)
    
    for val in data:
        h.Fill(val)
        
    h.SetLineColor(colors[pmt_name])
    
    # 【修改点 1】：调整线宽。把原来的 2 改成 3 或 4，图例里的线就会跟着变粗
    h.SetLineWidth(3) 
    
    h.SetMinimum(0.5)
    
    draw_opt = "HIST" if is_first else "HIST SAME"
    h.Draw(draw_opt)
    is_first = False
    
    # 【修改点 2】：自定义图例显示的名称
    # 如果名字是 PMT9new，我们就让它显示为 PMT9，其他的保持原样
    if pmt_name == "PMT9new":
        display_name = "PMT9"
    else:
        display_name = pmt_name
        
    # 将自定义的名字加入图例
    leg.AddEntry(h, display_name, "l")
    hists.append(h)

leg.Draw()
c.Update()
c.SaveAs("4PMT_Integral_Comparison.pdf")

# ... 后面的代码保持不变 ...
print("\n图谱已生成: 4PMT_Integral_Comparison.pdf")

if not ROOT.gROOT.IsBatch():
    input("按回车键退出...")