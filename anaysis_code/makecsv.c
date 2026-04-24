// """
// =============================================================================
// @file      makecsv.c / analysis_raw.cpp
// @brief     宇宙射线符合实验数据解析程序 (FADC Binary to CSV)
// @details   本程序负责读取由 LabView/DAQ 控制的 CAEN V1725 采集卡生成的原始
//            二进制数据文件(.bin)。剥离掉运行头(Run Header)和事件头(Event Header)后，
//            将真实的脉冲波形数据(ADC Values)提取出来，并按不同的物理通道(Channel)
//            分别生成适用于后期离线分析(Python/ROOT)的矩阵式 CSV 文件。
// =============================================================================
// """

#include <iostream>
#include <fstream>
#include <string>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "math.h"

// CERN ROOT 相关头文件 (目前使用 CSV 输出，如需存 ROOT Tree 则备用)
#include "TFile.h"
#include "TTree.h"
#include "TF1.h"
#include "TH1F.h"
#include "TGraph.h"

// 自定义函数库
#include "./misc.h"

using namespace std;

// 主控处理函数
int makeTree(char filename_input[200], unsigned int RUN_Start_NUMBER, unsigned int RUN_End_NUMBER)
{
    // ==========================================
    // 1. 初始化文件前缀与日志信息
    // ==========================================
    char filename_base[200] = "NoName";
    Get_Name(filename_base, filename_input);
    
    char date[16];
    sprintf(date,"%.16s",filename_base);
  
    // ==========================================
    // 2. 核心常量配置区 (必须与实验 DAQ 参数绝对匹配)
    // ==========================================
    const unsigned int EVENT_NUMBER = 500;   // 每次 Run(每个bin文件)记录的事例数(如:500个event)
    const unsigned int MAX_WINDOWS  = 1000;  // 每次触发记录的时间采样点长度(即Time Window)
    const unsigned int MAX_CHANNELS = 16;    // V1725 最大支持 16 个通道(CH0 ~ CH15)
    
    // ==========================================
    // 3. 文件读写指针与容器声明
    // ==========================================
    FILE *stream;                 // 指向 .bin 文件的二进制文件流
    char run_filename[200];       // 待拼接的输入文件名
    
    // 【Run Header - 全局运行头信息】
    Double_t pstt = 0.;           // Program Start Time (DAQ启动时间)
    UInt_t V1725_DAC[16] = {0};   // 16个通道的 DC Offset / DAC 设定值
    UInt_t V1725_twd = 0;         // Time Window (实际采样点数，正常=MAX_WINDOWS)
    UInt_t V1725_pretg = 0;       // Pre-Trigger (触发前采样点保留长度)
    UInt_t V1725_opch = 0;        // Opened Channels (用户在此次实验中实际启用了几个通道)
    Double_t rstt = 0.;           // Run Start Time (该文件开始记录的时间)
    Double_t redt = 0.;           // Run End Time   (该文件结束记录的时间)
    
    // 【Event Header - 单次事件头信息】
    UInt_t Evt_deadtime = 0;      // 系统的死时间
    UInt_t Evt_starttime = 0;     // 事件触发起点时间戳
    UInt_t Evt_endtime = 0;       // 事件记录结束时间戳
    UInt_t V1725_tgno = 0;        // Trigger Number (触发的序号)

    // ==========================================
    // 4. 大型内存块声明
    // ==========================================
    // 单次Event波形缓冲区: 维度为 [允许最大通道数] × [时间窗长度]
    UShort_t V1725_pulse[MAX_CHANNELS][MAX_WINDOWS];
    
    // 整个Run所有波形的数据仓库: 维度为 [通道] × [事例(Event)] × [时间点]
    // 【重点】: 使用 static 修饰可以强行在全局数据区分配内存，避免超过栈(Stack)的容量限制导致溢出崩溃
    static UShort_t y[MAX_CHANNELS][EVENT_NUMBER][MAX_WINDOWS]; 

    // ==========================================
    // 5. 循环处理每一个 RUN 的 .bin 数据文件
    // ==========================================
    for(unsigned int i = RUN_Start_NUMBER; i <= RUN_End_NUMBER; i++) 
    {
        // 5.1 组装完整文件名并以“只读+二进制”(rb) 模式打开
        sprintf(run_filename, "%sFADC_RAW_Data_%d.bin", filename_input, i);
        stream = fopen(run_filename, "rb"); 
        
        // 文件存在性校验 (跳过不存在/漏采的序列)
        if (stream == NULL) {
            printf("⚠️ 警告: 找不到文件 %s, 跳过...\n", run_filename);
            continue; 
        }
        printf("\n========== 正在处理文件: %s ==========\n", run_filename);
    
        // ------------------------------------------
        // [阶段 A] 读取此 Run 的全局 Header
        // ------------------------------------------
        fread(&pstt, sizeof(Double_t), 1, stream);
        for(int r = 0; r < 16; r++) fread(&V1725_DAC[r], sizeof(UInt_t), 1, stream);
        fread(&V1725_twd, sizeof(UInt_t), 1, stream);
        fread(&V1725_pretg, sizeof(UInt_t), 1, stream);
        fread(&V1725_opch, sizeof(UInt_t), 1, stream);
        fread(&rstt, sizeof(Double_t), 1, stream);
        
        printf("📢 检测到实验配置: 启用了 %d 个通道, 波形采集长度为 %d 个点\n", V1725_opch, V1725_twd);
            
        // ------------------------------------------
        // [阶段 B] 深入逐条提取真实的 Event 数据波形
        // ------------------------------------------
        for(unsigned int j = 0; j < EVENT_NUMBER; j++) 
        {
            // 剥开每一层波形外面的时间头(垃圾/对齐信息)
            fread(&Evt_deadtime, sizeof(UInt_t), 1, stream);
            fread(&Evt_starttime, sizeof(UInt_t), 1, stream);
            fread(&Evt_endtime, sizeof(UInt_t), 1, stream);
            fread(&V1725_tgno, sizeof(UInt_t), 1, stream);
        
            // 进入有效波形区：按 "已开启通道号 -> 具体波形点" 顺序抓取
            for(unsigned int k = 0; k < V1725_opch; k++) 
            {
                for(unsigned int l = 0; l < V1725_twd; l++) 
                {
                    // 每次吸取2个字节(UShort_t 16-bit)，获取该时刻真实的 ADC 高低电平电压值
                    fread(&V1725_pulse[k][l], sizeof(UShort_t), 1, stream);
                    
                    // 防御性内存安全判断：确保存入目标矩阵时没有超出行列极限
                    if(j < EVENT_NUMBER && l < MAX_WINDOWS && k < MAX_CHANNELS)
                    {
                        // 妥善保存： [通道序号][事例序号][时间点坐标] = 电压数字信号
                        y[k][j][l] = V1725_pulse[k][l];
                    }
                }
            }
        } // 结束这个文件的所有的 Event 的获取
        
        // 收尾操作: 获取结束时间戳，关闭二进制文件，释放资源
        fread(&redt, sizeof(Double_t), 1, stream);
        fclose(stream); 
        
        // ------------------------------------------
        // [阶段 C] 数据按物理通道分离落盘生成 CSV
        // ------------------------------------------
        for(unsigned int k = 0; k < V1725_opch; k++) 
        {
            char csv_filename[200];
            // 规范命名: test_RunN_CHK.csv  (表示 N 号 Run 文件中通道 K 的波形大集合)
            sprintf(csv_filename, "%s_Run%d_CH%d.csv", filename_input, i, k);
            
            // 使用 C++ iostream 操作输出最终可见的纯文本 CSV 数据文件
            std::ofstream f(csv_filename);
            for(unsigned int a = 0; a < EVENT_NUMBER; a++) 
            {      
                for(unsigned int b = 0; b < V1725_twd; b++) 
                {     
                    // 高亮巧妙的逗号法则三目运算符:
                    //   如果没有达到行尾, 写一个波形数值后就跟上 "," 把同波形隔开进入下一列
                    //   如果是波形的最后一个点 (V1725_twd-1), 就写换行符 "\n" 进行换行！
                    f << y[k][a][b] << (b == V1725_twd-1 ? "\n" : ","); 
                }
            }
            f.close();
            printf("  📁 成功导出: %s (格式: %d 行波形 × %d 个时间点)\n", csv_filename, EVENT_NUMBER, V1725_twd);
        }
    } // Run文件提取结束大循环
    
    // ==========================================
    // 6. 实验数据转换流程完美收官
    // ==========================================
    std::cout << "\n🎉 全部二进制数据包剥离解码完毕！" << std::endl;
    return 0;
}