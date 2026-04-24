import os
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm
import ROOT  

# ================= 配置区域 =================
DATA_CONFIG = [
    {
        "folder": r"/home/ruler/cupt4/det3/coincidence/pmt10-12第四象限",
        "ls1_col": "CH3",
        "ls2_col": "CH4"
    },
    {
        "folder": r"/home/ruler/cupt4/det3/coincidence/pmt10-12中心位置",
        "ls1_col": "CH3",
        "ls2_col": "CH4"
    }
]

# ================= 辅助函数 =================
def find_header_line(filepath, col1, col2):
    """
    动态寻找表头行：不再死板地寻找 CH1，而是寻找你配置的 col1 和 col2
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if 'TIME' in line and col1 in line and col2 in line:
                return i
    return 21 # 默认 fallback

# ================= 数据容器 =================
total_ls1_amps = []
total_ls2_amps = []

# ================= 主循环处理 =================
for config in DATA_CONFIG:
    folder_path = config["folder"]
    col_ls1 = config["ls1_col"]
    col_ls2 = config["ls2_col"]
    
    file_list = glob.glob(os.path.join(folder_path, "*.csv"))
    print(f"\n[{folder_path}]")
    
    if len(file_list) == 0:
        print(f"⚠️ 警告：该路径下未找到 CSV 文件，请检查路径拼写！")
        continue
        
    print(f"找到 {len(file_list)} 个文件。提取通道: {col_ls1} 和 {col_ls2}")
    
    for file in tqdm(file_list, desc="Processing"):
        try:
            # 1. 动态寻找表头
            header_idx = find_header_line(file, col_ls1, col_ls2)
            
            # 2. 读取所需列
            df = pd.read_csv(file, skiprows=header_idx, usecols=['TIME', col_ls1, col_ls2])
            
            val_ls1 = df[col_ls1].values
            val_ls2 = df[col_ls2].values
            
            # 3. 计算基线 (前 1000 个点) 并扣除
            bl_ls1 = np.mean(val_ls1[:1000])
            bl_ls2 = np.mean(val_ls2[:1000])
            
            sig_ls1 = val_ls1 - bl_ls1
            sig_ls2 = val_ls2 - bl_ls2
            
            # 4. 获取幅度并转换为 mV
            total_ls1_amps.append(np.max(sig_ls1) * 1000)
            total_ls2_amps.append(np.max(sig_ls2) * 1000)
            
        except Exception as e:
            # 拒绝沉默，打印具体的错误原因
            print(f"\n❌ 处理文件 {os.path.basename(file)} 时出错: {e}")
            continue

# ================= 异常数据清洗 =================
total_ls1_amps = np.array(total_ls1_amps)
total_ls2_amps = np.array(total_ls2_amps)

# 剔除无效值 (inf, nan)
total_ls1_amps = total_ls1_amps[np.isfinite(total_ls1_amps)]
total_ls2_amps = total_ls2_amps[np.isfinite(total_ls2_amps)]

print(f"\n✅ 数据处理完毕！")
print(f"LS1 ({DATA_CONFIG[0]['ls1_col']}) 有效数据量: {len(total_ls1_amps)}")
print(f"LS2 ({DATA_CONFIG[0]['ls2_col']}) 有效数据量: {len(total_ls2_amps)}")

if len(total_ls1_amps) == 0 or len(total_ls2_amps) == 0:
    print("⚠️ 没有足够的数据来绘图，程序退出。")
    exit()

# ================= 绘图部分 (PyROOT) =================
# 全局美化设置 (无网格，带内向刻度线和加粗边框)
ROOT.gStyle.SetOptStat(0)     # 关掉右上角统计框
ROOT.gStyle.SetOptTitle(0)    # <--- 新增：全局关闭顶部的标题显示
ROOT.gStyle.SetPadTickX(1)    # 顶部添加刻度线 (形成封闭边框)
ROOT.gStyle.SetPadTickY(1)    # 右侧添加刻度线 (形成封闭边框)
ROOT.gStyle.SetLineWidth(1)   # 刻度线加粗
ROOT.gStyle.SetFrameLineWidth(2) # 边框加粗
ROOT.gStyle.SetTextFont(42)   # 标准高清字体

# 创建画布
canvas = ROOT.TCanvas("c1", "Canvas", 1000, 600)
canvas.SetLogy() # 设置 Y 轴为对数坐标

# 自动确定 X 轴最大范围，留 5% 余量
max_val = max(np.max(total_ls1_amps), np.max(total_ls2_amps))
x_max = max_val * 1.05 

# 初始化直方图 (移除了分号前面的标题文字)
h1 = ROOT.TH1F("h1", ";Amplitude (mV);Counts", 550, 0, x_max)
h2 = ROOT.TH1F("h2", ";Amplitude (mV);Counts", 550, 0, x_max)

# 填充数据
for val in total_ls1_amps: h1.Fill(val)
for val in total_ls2_amps: h2.Fill(val)

# 样式设置
h1.SetLineColor(ROOT.kBlue)
h1.SetLineWidth(2)
h2.SetLineColor(ROOT.kRed)
h2.SetLineWidth(2)

# 防止对数坐标下极小值显示问题
h1.SetMinimum(0.5)

# 绘制
h1.Draw("HIST")
h2.Draw("HIST SAME")

# 美化 Legend
leg = ROOT.TLegend(0.75, 0.75, 0.88, 0.88)
leg.SetBorderSize(0)      # 透明边框
leg.SetFillStyle(0)       # 透明背景
leg.SetTextFont(42)
leg.SetTextSize(0.04)
# <--- 修改：将图例文字改为固定的 LS1 和 LS2
leg.AddEntry(h1, "LS1", "l") 
leg.AddEntry(h2, "LS2", "l")
leg.Draw()

# 更新并保存
canvas.Update()
# <--- 修改：后缀改为 .pdf
canvas.SaveAs("Liquid_Scintillator_Spectrum.pdf")

# 保持窗口开启
print("\n图表已生成并保存为 Liquid_Scintillator_Spectrum.pdf")
input("按回车键(Enter)退出并关闭图像...")