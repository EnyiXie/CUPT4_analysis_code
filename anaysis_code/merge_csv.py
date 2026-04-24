"""
=============================================================================
@file      merge_csv.py
@brief     宇宙射线实验 CSV 波形数据合并脚本 (Data Merger)
@details   将按 Run 分散的波形 CSV 文件，按物理通道 (Channel) 进行纵向合并。
           例如：把 Run0 到 Run11 的 CH0 文件，全部拼接到一个 Merged_CH0.csv 中。
           采用流式读写，内存占用近乎为 0，几百兆文件秒级合并。
=============================================================================
"""

import os

# ==========================================
# ⚙️ 用户灵活配置区 (每次按需修改这里)
# ==========================================
FILE_PREFIX = "test1"       # 文件名前缀
RUN_START   = 0             # 起始 Run 号
RUN_END     = 3           # 结束 Run 号 (包含这一号)

# 你想合并哪些通道？填入列表即可。
# 比如开了5个通道就是 [0, 1, 2, 3, 4]；如果只要通道1和2就是 [1, 2]
CHANNELS_TO_MERGE = [0, 1, 2, 3] 
# ==========================================

print("🚀 开始合并 CSV 数据...\n")

# 外层循环：遍历每一个需要合并的通道
for ch in CHANNELS_TO_MERGE:
    # 拼装合并后的最终文件名 (例如: test1_CH0.csv)
    output_filename = f"{FILE_PREFIX}_CH{ch}.csv"
    
    total_lines_merged = 0  # 统计总共合并了多少个 Event 波形
    files_merged_count = 0  # 统计成功合并了几个文件
    
    # 以 "追加/写入" (w) 模式打开最终的总文件
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        
        # 内层循环：遍历该通道下的所有 Run
        for run in range(RUN_START, RUN_END + 1):
            input_filename = f"{FILE_PREFIX}_Run{run}_CH{ch}.csv"
            
            # 检查这个 Run 文件存不存在 (防止中间某一个Run漏采了导致报错)
            if not os.path.exists(input_filename):
                print(f"  ⚠️ 警告: 找不到 {input_filename}，已自动跳过。")
                continue
            
            # 以只读模式打开碎文件，并将内容流式写入总文件
            with open(input_filename, 'r', encoding='utf-8') as infile:
                for line in infile:
                    outfile.write(line)
                    total_lines_merged += 1
            
            files_merged_count += 1
            
    # 打印单个通道的合并战报
    if files_merged_count > 0:
        print(f"✅ 通道 CH{ch} 合并成功: -> {output_filename}")
        print(f"   (共融合 {files_merged_count} 个文件，总计 {total_lines_merged} 个波形事件)\n")
    else:
        print(f"❌ 通道 CH{ch} 合并失败: 在指定范围内没有找到任何有效文件。\n")
        # 如果生成了空文件，顺手把它删掉保持文件夹干净
        if os.path.exists(output_filename):
            os.remove(output_filename)

print("🎉 所有指定通道的数据合并工作圆满完成！")