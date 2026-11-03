本压缩包为模块B Python验证源码，用于Zynq FIR滤波器验证与性能分析，不含Vivado/HLS硬件工程，硬件工程由队友单独提交。

文件清单：
1. signal_generate.ipynb：信号生成模块
生成正弦、混频输入信号，输出统一51抽头FIR滤波器系数、1000点理论参考Golden结果，作为ARM与FPGA的统一输入基准。

2. fir_hw_verify.ipynb：FIR仿真、硬件验证与性能对比主程序
- 实现零填充初始条件的51抽头FIR滤波器，与HLS、ARM C程序规则对齐
- 支持解析AXI DMA输出的float32小端bin文件，逐点计算最大绝对误差、RMSE，绘制波形与误差图
- 包含冲激响应、基础正弦/混频两组原始验证
- 末尾独立Cell：性能测试模块，读取性能测试版本FPGA输出，对照ARM Cortex‑A9（-O0编译）耗时，计算误差与ARM-FPGA耗时对照比，对应作品简介的性能加速对比实验

运行依赖：
环境：Jupyter Notebook，Python库：numpy、matplotlib、struct
运行顺序：先执行导入库、工具函数单元格，再执行对应验证/性能单元格
bin文件：板上导出的FPGA输出bin放在同目录下解析

口径说明：
ARM耗时为FIR纯计算耗时；FPGA耗时为端到端（缓存维护+DMA启动+FIR计算+传输完成），因此指标称为对照比，非严格同口径加速比。

测试结果摘要（性能组）：
正弦激励：对照比25.64，最大误差1.86e-6
混频激励：对照比25.86，最大误差2.09e-6
FPGA输出与Python理论基准高度吻合。