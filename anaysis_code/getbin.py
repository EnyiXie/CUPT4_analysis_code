"""
=============================================================================
@file      getbin.py
@brief     宇宙线实验幅度分布分析工具 (Get Bin)
@details   获得液闪和塑闪的幅度（最大/最小值）分布直方图，快速看出增益匹配情况和数据质量。
=============================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ================= 全局配置字典 =================
# 将液闪(LS)和塑闪(PS)的参数分别打包，想改什么直接在这里改
CONFIG = {
    "LS": {
        "files": ("test1_CH0.csv", "test1_CH3.csv"),
        "titles": ("Liquid Scintillator 1 (CH0)", "Liquid Scintillator 2 (CH3)"),
        "colors": ("#e74c3c", "#f39c12"), # 红色和橙色系
        "window": (0, None),              # 默认看整个波形 (可以改成具体区间如 (100, 200))
        "operation": "max",               # 液闪原来用的是 max (正脉冲)
        "xlabel": "ADC Maximum Value"
    },
    "PS": {
        "files": ("test1_CH1.csv", "test1_CH2.csv"),
        "titles": ("PMT 6 (CH1) Min Amplitude", "PMT 8 (CH2) Min Amplitude"),
        "colors": ("royalblue", "seagreen"), # 蓝色和绿色系
        "window": (250, 350),             # 塑闪看特定时间窗
        "operation": "min",               # 塑闪找最小值 (负脉冲)
        "xlabel": "ADC Minimum Value"
    }
}

# ================= 核心函数区 =================

def extract_amplitudes(filepath: str, window: tuple, operation: str) -> np.ndarray:
    """
    负责读取文件并提取波形特征（最大值或最小值）。
    采用 Numpy 向量化运算，彻底抛弃 for 循环，速度极快。
    """
    if not os.path.exists(filepath):
        print(f"⚠️ 警告: 找不到文件 {filepath}")
        return np.array([])

    print(f"正在读取并处理数据: {filepath} ...")
    data = np.loadtxt(filepath, delimiter=',')
    
    # 切片获取时间窗内的数据
    start, end = window
    data_windowed = data[:, start:end] if end else data[:, start:]

    # 向量化求极值 (沿着 axis=1 即每一行求极值)
    if operation == "max":
        return np.max(data_windowed, axis=1)
    elif operation == "min":
        return np.min(data_windowed, axis=1)
    else:
        raise ValueError("operation 必须是 'max' 或 'min'")


def plot_dual_histograms(data1: np.ndarray, data2: np.ndarray, config: dict):
    """
    专门负责画两个子图的直方图。
    """
    if len(data1) == 0 or len(data2) == 0:
        print("⚠️ 数据为空，无法绘图。")
        return

    # 创建画布
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # 绘制通道 1 对数坐标 ，如果不要对数把log = True去掉就行
    ax1.hist(data1, bins=100, color=config["colors"][0], alpha=0.7, edgecolor='none', log=True)
    ax1.set_title(config["titles"][0], fontsize=14, pad=15)
    ax1.set_xlabel(config["xlabel"], fontsize=12)
    ax1.set_ylabel("Counts", fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    # 隐藏上方和右方的边框线，让图表看起来更现代
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # 绘制通道 2 对数坐标
    ax2.hist(data2, bins=150, color=config["colors"][1], alpha=0.7, edgecolor='none', log=True)
    ax2.set_title(config["titles"][1], fontsize=14, pad=15)
    ax2.set_xlabel(config["xlabel"], fontsize=12)
    ax2.set_ylabel("Counts", fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.show()


def run_analysis(detector_type: str):
    """
    主控函数：根据传入的探测器类型，统筹数据提取和绘图。
    """
    detector_type = detector_type.upper()
    if detector_type not in CONFIG:
        print(f"❌ 错误: 不支持的探测器类型 '{detector_type}'。请选择 'LS' 或 'PS'。")
        return

    print(f"=== 开始分析 {detector_type} 数据 ===")
    cfg = CONFIG[detector_type]

    # 并行提取两个通道的数据特征
    amps_ch1 = extract_amplitudes(cfg["files"][0], cfg["window"], cfg["operation"])
    amps_ch2 = extract_amplitudes(cfg["files"][1], cfg["window"], cfg["operation"])

    # 绘制图像
    plot_dual_histograms(amps_ch1, amps_ch2, cfg)
    print("=== 分析完成 ===\n")


# ================= 执行区 =================
if __name__ == "__main__":
    # 在这里选择你要画什么！
    # 改成 'LS' 就只画液闪，改成 'PS' 就只画塑闪。
    TARGET_DETECTOR = 'LS'  
    
    run_analysis(TARGET_DETECTOR)

    # 如果你想一次性把两个都画出来，也可以取消下面两行的注释：
    # run_analysis('LS')
    # run_analysis('PS')