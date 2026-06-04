# 嵌入式 C/C++ 每日练习题目生成器

每天自动生成 **3-5 道** 嵌入式 C/C++ 练习题，涵盖面试题和实际应用题。

## 功能特点

- 🎯 **7 大分类**：C 语言、C++ 嵌入式、嵌入式系统核心、外设协议、数据结构、调试工具、实战编程
- 📝 **4 种题型**：选择题、简答题、代码分析（找 Bug）、编程题
- 🔄 **智能轮转**：按分类轮转确保全面覆盖，90 天内不重复
- 📊 **难度混合**：简单/中等/困难合理搭配
- 📁 **双文件输出**：题目和答案分开，先做后看

## 快速开始

### 1. 生成今天的题目

```bash
cd daily-quiz
python generate.py
```

输出：
```
output/
├── questions/
│   └── 2026-06-04.md    # 只有题目
└── answers/
    └── 2026-06-04.md    # 答案和详解
```

### 2. 自定义参数

```bash
# 生成 5 道题
python generate.py --count 5

# 生成指定日期（补过去的）
python generate.py --date 2026-06-01

# 一次性生成接下来 7 天
python generate.py --week

# 查看题库统计
python generate.py --stats

# 查看分类覆盖
python generate.py --categories
```

### 3. 设置每日自动运行（Windows）

以**管理员身份**运行 PowerShell：

```powershell
cd daily-quiz
powershell -ExecutionPolicy Bypass -File schedule_windows.ps1
```

这会创建一个每天早上 7:00 自动运行的计划任务。

### 4. 设置每日自动运行（Linux / WSL / Git Bash）

```bash
# 编辑 crontab
crontab -e

# 添加一行（每天早上 7:00 运行）
0 7 * * * cd /d/嵌入式学习/c\&c++/daily-quiz && python generate.py
```
### 5.关闭每日自动运行
  方式一：命令行（推荐，最快）

  管理员 PowerShell 中执行：

  Unregister-ScheduledTask -TaskName "EmbeddedDailyQuiz" -Confirm:$false

  一条命令直接删掉，不会再自动生成。

  方式二：图形界面

  1. Win + R → 输入 taskschd.msc → 回车
  2. 左侧点「任务计划程序库」
  3. 找到 EmbeddedDailyQuiz → 右键 → 禁用（暂停但不删除）或 删除（彻底移除）
## 题库分类

| 分类 | 说明 | 典型考点 |
|------|------|----------|
| **C 语言核心** | 指针、内存、关键字 | volatile、const、static、位运算、函数指针、大小端、宏 |
| **C++ 嵌入式** | C++ 在嵌入式中的应用 | RAII、placement new、constexpr、模板、虚函数开销 |
| **嵌入式系统核心** | RTOS、中断、启动 | 中断/ISR、DMA、信号量、优先级反转、Bootloader、看门狗 |
| **外设与通信协议** | 硬件接口 | GPIO、SPI、I2C、UART、CAN、ADC/DAC、PWM、定时器 |
| **数据结构与算法** | 嵌入式常用结构 | 环形缓冲、链表、状态机、CRC、PID、FIR 滤波 |
| **调试与工具** | 排查技巧 | HardFault 分析、栈溢出检测、GDB 远程调试、Watchpoint |
| **实战编程题** | 动手写代码 | 消抖、协议解析、内存池、大小端转换、中断安全日志 |

## 扩充题库

直接编辑 `question_bank.json`，在 `"questions"` 数组中按格式添加新题：

```json
{
  "id": "c_021",
  "category": "c_language",
  "subcategory": "volatile",
  "type": "multiple_choice",
  "difficulty": "medium",
  "tags": ["volatile", "isr"],
  "question": "题目内容...",
  "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
  "answer": "B",
  "explanation": "解析..."
}
```

ID 命名规范：`分类缩写_序号`（如 `c_021`、`embed_015`、`periph_010`）。

## 文件结构

```
daily-quiz/
├── generate.py              # 主脚本
├── question_bank.json       # 题库（200+ 题）
├── tracking.json            # 使用追踪（自动生成）
├── schedule_windows.ps1     # Windows 定时任务脚本
├── README.md                # 本文件
└── output/
    ├── questions/           # 每日题目（无答案）
    └── answers/             # 每日答案（含解析）
```
