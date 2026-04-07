# 太阳能电池实验数据处理

## 1. 这份文档适合谁
1. 人类用户：想快速运行程序并拿到图像与结果。
2. AI 代理：想按固定输入输出协议自动执行、核验并继续加工结果。

## 2. 程序做什么
入口文件：main.py

程序会完成以下任务：
1. 读取 data1_U-I-ln(I).csv，绘制 I-U 曲线和 ln(I)-U 曲线。
2. 对 ln(I)-U 做线性回归，得到方程 ln(I)=kU+b，并计算拟合优度 R2。
3. 读取 data2_Rx-U-I_100Ω步长.csv 与 data3_Rx-U-I_10Ω步长.csv，绘制合并 P-Rx 曲线。
4. 若 data2/data3 缺少第 4 行功率，自动按 P=U*I 回填到原 CSV。
5. 将 data2+data3 合并后计算填充因子 FF。
6. 将线性回归结果和 FF 统一写入 result.txt。

## 3. 数据格式（必须）

### 3.1 data1_U-I-ln(I).csv
按行存储：
1. 第1行：U（V）
2. 第2行：I（mA）
3. 第3行：ln(I)

### 3.2 data2_Rx-U-I_100Ω步长.csv 与 data3_Rx-U-I_10Ω步长.csv
按行存储：
1. 第1行：Rx（ohm）
2. 第2行：U（V）
3. 第3行：I（mA）
4. 第4行：P（mW，可选）

说明：
1. 如果第4行不存在，程序会自动补齐并覆盖写回原文件。
2. data2 最后一列是极大电阻测点，绘图时忽略，但不会从源数据删除。

## 4. 计算公式
1. 功率：P = U * I（单位自然为 mW，因为 V * mA = mW）。
2. 填充因子：FF = Pmax / (Voc * Isc)。
3. 线性回归：ln(I) = kU + b。
4. 拟合优度：R2 = 1 - SSres / SStot。

## 5. 输出文件
每次运行后会生成或更新：
1. I-U_curve.png
2. lnI-U_curve.png
3. P-Rx_curve.png
4. result.txt

result.txt 结构：
1. ln(I)-U linear regression
2. k
3. b
4. equation
5. R2
6. Fill factor result
7. Pmax(mW)
8. Voc(V)
9. Isc(mA)
10. FF

## 6. 快速使用（给人）

### 6.1 安装依赖
```powershell
"C:/Program Files/Python310/python.exe" -m pip install pandas matplotlib numpy
```

### 6.2 运行
```powershell
"C:/Program Files/Python310/python.exe" d:/Datas/Desktop/大学物理实验数据处理/太阳能电池实验/main.py
```

### 6.3 无界面批处理运行
```powershell
$env:MPLBACKEND='Agg'; "C:/Program Files/Python310/python.exe" d:/Datas/Desktop/大学物理实验数据处理/太阳能电池实验/main.py
```

## 7. 自动化使用（给 AI）

### 7.1 最小执行协议
1. 确认 3 个 CSV 文件存在且在 main.py 同目录。
2. 执行 main.py。
3. 校验 result.txt 存在，且至少包含键：k, b, equation, R2, FF。
4. 校验 3 张 png 图存在。

### 7.2 推荐机器可读结果（从 result.txt 提取）
```json
{
  "linear_regression": {
    "model": "ln(I)=k*U+b",
    "k": "float",
    "b": "float",
    "equation": "string",
    "R2": "float"
  },
  "fill_factor": {
    "Pmax_mW": "float",
    "Voc_V": "float",
    "Isc_mA": "float",
    "FF": "float"
  }
}
```

## 8. 常见问题
1. FileNotFoundError：确认 CSV 文件名与路径完全一致。
2. FigureCanvasAgg non-interactive：仅是非交互后端提示，不影响图像和结果文件。
3. R2 异常：检查 data1 第3行是否确为 ln(I) 且与 U 一一对应。

## 9. 当前代码对应关系
1. 数据读取：read_data1、read_power_dataset
2. FF 计算：compute_fill_factor
3. 主流程与输出：main
