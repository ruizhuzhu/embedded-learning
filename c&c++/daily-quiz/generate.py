#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
嵌入式 C/C++ 每日练习题目生成器
================================
每天自动生成 3-5 道嵌入式 C/C++ 题目，涵盖面试题和实际应用题。
题目包括选择题、简答题、代码分析题、编程题。

用法:
    python generate.py                    # 生成今天的题目 (默认 4 题)
    python generate.py --count 5         # 生成 5 题
    python generate.py --date 2026-06-15 # 生成指定日期的题目
    python generate.py --stats           # 查看题库使用统计
    python generate.py --categories      # 查看分类覆盖情况
"""

import json
import os
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = Path(__file__).resolve().parent
BANK_FILE = SCRIPT_DIR / "question_bank.json"
TRACKING_FILE = SCRIPT_DIR / "tracking.json"
OUTPUT_DIR = SCRIPT_DIR / "output"
QUESTIONS_DIR = OUTPUT_DIR / "questions"
ANSWERS_DIR = OUTPUT_DIR / "answers"

REPEAT_WINDOW_DAYS = 90  # 90 天内不重复
DEFAULT_DAILY_COUNT = 4  # 每天默认 4 题 (范围 3-5)

# 分类轮转表：每天一个主分类（2 题），其余从次要分类出
# 标准轮转（含 C++）
CATEGORY_ROTATION = [
    {"primary": "c_language",       "secondary": ["cpp_embedded", "embedded_core"]},
    {"primary": "cpp_embedded",     "secondary": ["peripherals", "debugging"]},
    {"primary": "embedded_core",    "secondary": ["data_structures", "coding_problems"]},
    {"primary": "peripherals",      "secondary": ["c_language", "cpp_embedded"]},
    {"primary": "data_structures",  "secondary": ["embedded_core", "peripherals"]},
    {"primary": "debugging",        "secondary": ["coding_problems", "c_language"]},
    {"primary": "coding_problems",  "secondary": ["cpp_embedded", "data_structures"]},
]

# 入门轮转（不含 C++，偏基础）
BEGINNER_ROTATION = [
    {"primary": "c_language",       "secondary": ["embedded_core", "peripherals"]},
    {"primary": "embedded_core",    "secondary": ["c_language", "data_structures"]},
    {"primary": "peripherals",      "secondary": ["c_language", "coding_problems"]},
    {"primary": "data_structures",  "secondary": ["embedded_core", "c_language"]},
    {"primary": "coding_problems",  "secondary": ["peripherals", "debugging"]},
    {"primary": "c_language",       "secondary": ["debugging", "peripherals"]},
    {"primary": "embedded_core",    "secondary": ["coding_problems", "peripherals"]},
]

CATEGORY_NAMES = {
    "c_language": "C 语言核心",
    "cpp_embedded": "C++ 嵌入式编程",
    "embedded_core": "嵌入式系统核心",
    "peripherals": "外设与通信协议",
    "data_structures": "数据结构与算法",
    "debugging": "调试与工具",
    "coding_problems": "实战编程题",
}

TYPE_NAMES = {
    "multiple_choice": "选择题",
    "short_answer": "简答题",
    "code_analysis": "代码分析",
    "coding_problem": "编程题",
}

DIFFICULTY_NAMES = {
    "easy": "简单",
    "medium": "中等",
    "hard": "困难",
}

DIFFICULTY_STARS = {
    "easy": "★☆☆",
    "medium": "★★☆",
    "hard": "★★★",
}


# ============================================================
# 题库加载
# ============================================================
def load_bank():
    """加载题库 JSON 文件"""
    if not BANK_FILE.exists():
        print(f"[ERROR] 题库文件不存在: {BANK_FILE}")
        return None
    with open(BANK_FILE, "r", encoding="utf-8") as f:
        bank = json.load(f)
    questions = bank.get("questions", [])
    if not questions:
        print("[ERROR] 题库为空！")
        return None
    return bank


def index_questions(bank):
    """按分类索引题目，方便快速查找"""
    index = defaultdict(list)
    for q in bank["questions"]:
        index[q["category"]].append(q)
    return index


# ============================================================
# 追踪管理
# ============================================================
def load_tracking():
    """加载使用追踪文件，不存在则创建"""
    if TRACKING_FILE.exists():
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "metadata": {
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": "",
            "total_days_generated": 0,
            "repeat_window_days": REPEAT_WINDOW_DAYS,
        },
        "usage": {},          # question_id -> {dates: [...], times_served: N}
        "daily_log": {},      # "YYYY-MM-DD" -> {question_ids: [...], primary_category: ...}
        "rotation_state": {
            "current_index": 0,  # 当前轮转位置
        },
    }


def save_tracking(tracking):
    """保存追踪文件"""
    tracking["metadata"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(tracking, f, ensure_ascii=False, indent=2)


# ============================================================
# 选题算法
# ============================================================
def get_recently_used(tracking, window_days=REPEAT_WINDOW_DAYS):
    """获取最近 N 天内已使用的题目 ID 集合"""
    cutoff = datetime.now() - timedelta(days=window_days)
    recent = set()
    for qid, info in tracking.get("usage", {}).items():
        for date_str in info.get("dates", []):
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d")
                if d >= cutoff:
                    recent.add(qid)
                    break
            except ValueError:
                continue
    return recent


def build_candidate_pool(bank, tracking, target_date_str, exclude_cats=None):
    """构建候选题目池（排除最近用过的 + 当天已生成的 + 指定分类）"""
    recent = get_recently_used(tracking)
    today_log = tracking.get("daily_log", {}).get(target_date_str, {})
    today_used = set(today_log.get("question_ids", []))
    excluded = recent | today_used
    exclude_cats = exclude_cats or []

    candidates = []
    for q in bank["questions"]:
        if q["id"] not in excluded and q["category"] not in exclude_cats:
            candidates.append(q)
    return candidates


def get_rotation_slots(rotation_index, daily_count, no_cpp=True):
    """根据轮转位置分配每日各分类的题目配额"""
    table = BEGINNER_ROTATION if no_cpp else CATEGORY_ROTATION
    rotation = table[rotation_index % len(table)]
    slots = []

    # 主分类：2 题（如果 daily_count >= 3）
    primary_count = min(2, daily_count)
    for _ in range(primary_count):
        slots.append(rotation["primary"])

    # 次要分类：各 1 题
    remaining = daily_count - primary_count
    secondaries = rotation["secondary"]
    for i in range(remaining):
        slots.append(secondaries[i % len(secondaries)])

    return slots, rotation["primary"]


def score_question(q, tracking, beginner_mode=False):
    """
    给题目打分（越高越优先被选中）
    - 越久没被使用，分数越高
    - 被使用次数越少，分数越高
    - 加上一点随机抖动
    """
    usage = tracking.get("usage", {}).get(q["id"], {})
    times_served = usage.get("times_served", 0)
    dates = usage.get("dates", [])

    # 距离上次使用的天数（越久分数越高）
    days_since_last = REPEAT_WINDOW_DAYS + 1
    if dates:
        try:
            last_date = datetime.strptime(dates[-1], "%Y-%m-%d")
            days_since_last = (datetime.now() - last_date).days
        except ValueError:
            pass

    recency_score = min(days_since_last / REPEAT_WINDOW_DAYS, 1.0) * 0.5
    frequency_score = max(0, 1.0 - times_served / 5) * 0.3

    # 难度加权：入门模式偏好简单，普通模式偏好中等
    if beginner_mode:
        difficulty_weight = {"easy": 0.30, "medium": 0.15, "hard": 0.02}
    else:
        difficulty_weight = {"easy": 0.15, "medium": 0.25, "hard": 0.10}
    diff_score = difficulty_weight.get(q.get("difficulty", "medium"), 0.15)

    # 随机抖动
    jitter = random.random() * 0.1

    return recency_score + frequency_score + diff_score + jitter


def select_questions(bank, tracking, target_date_str, daily_count, no_cpp=True):
    """核心选题算法"""
    # 排除的分类
    exclude_cats = []
    if no_cpp:
        exclude_cats = ["cpp_embedded"]

    # 获取候选池
    candidates = build_candidate_pool(bank, tracking, target_date_str, exclude_cats)
    index = index_questions({"questions": candidates})

    # 获取轮转位置
    rotation_idx = tracking["rotation_state"]["current_index"]
    rotation_table = BEGINNER_ROTATION if no_cpp else CATEGORY_ROTATION
    rotation_idx = rotation_idx % len(rotation_table)
    slots, primary_cat = get_rotation_slots(rotation_idx, daily_count, no_cpp)

    selected = []
    used_ids = set()

    for slot_cat in slots:
        # 从对应分类中获取候选题目
        cat_candidates = index.get(slot_cat, [])
        # 如果该分类不够，从所有分类补充
        if not cat_candidates:
            cat_candidates = candidates

        # 排除已选中的
        cat_candidates = [q for q in cat_candidates if q["id"] not in used_ids]

        if not cat_candidates:
            continue

        # 按分数排序，选最高的
        scored = [(q, score_question(q, tracking, no_cpp)) for q in cat_candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        chosen = scored[0][0]
        selected.append(chosen)
        used_ids.add(chosen["id"])

    # 确保类型多样性（至少 1 道编程/分析题）
    types = [q["type"] for q in selected]
    if "coding_problem" not in types and "code_analysis" not in types:
        # 尝试将最后一题换成编程/分析题
        for i in range(len(selected) - 1, -1, -1):
            alt_candidates = [
                q for q in candidates
                if q["id"] not in used_ids
                and q["type"] in ("coding_problem", "code_analysis")
                and q["category"] == selected[i]["category"]
            ]
            if alt_candidates:
                scored = [(q, score_question(q, tracking, no_cpp)) for q in alt_candidates]
                scored.sort(key=lambda x: x[1], reverse=True)
                replaced = selected[i]
                selected[i] = scored[0][0]
                used_ids.discard(replaced["id"])
                used_ids.add(selected[i]["id"])
                break

    # 确保难度混合
    difficulties = [q["difficulty"] for q in selected]
    # 如果全是 easy，尝试加一个 medium
    if all(d == "easy" for d in difficulties) and daily_count >= 3:
        for i, q in enumerate(selected):
            alt = [
                x for x in candidates
                if x["id"] not in used_ids
                and x["category"] == q["category"]
                and x["difficulty"] in ("medium", "hard")
            ]
            if alt:
                scored = [(x, score_question(x, tracking)) for x in alt]
                scored.sort(key=lambda x: x[1], reverse=True)
                selected[i] = scored[0][0]
                used_ids.add(selected[i]["id"])
                break

    return selected, primary_cat


# ============================================================
# Markdown 渲染
# ============================================================
def render_questions_md(selected, target_date, primary_cat, rotation_index, no_cpp=True):
    """渲染题目 Markdown（不含答案）"""
    rotation_table = BEGINNER_ROTATION if no_cpp else CATEGORY_ROTATION
    rotation = rotation_table[rotation_index % len(rotation_table)]
    primary_name = CATEGORY_NAMES.get(primary_cat, primary_cat)
    secondary_names = [CATEGORY_NAMES.get(c, c) for c in rotation["secondary"]]

    difficulties = [q["difficulty"] for q in selected]
    diff_summary = ", ".join(
        f"{DIFFICULTY_NAMES[d]} {DIFFICULTY_STARS[d]}"
        for d in difficulties
    )

    total_minutes = sum(q.get("estimated_minutes", 8) for q in selected)

    lines = []
    lines.append(f"# 嵌入式 C/C++ 每日练习 — {target_date}")
    lines.append("")
    lines.append(f"**今日焦点：** {primary_name}")
    lines.append(f"**次要分类：** {', '.join(secondary_names)}")
    lines.append(f"**难度分布：** {diff_summary}")
    lines.append(f"**预计用时：** {total_minutes} 分钟")
    lines.append(f"**题目数量：** {len(selected)} 题")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, q in enumerate(selected, 1):
        cat_name = CATEGORY_NAMES.get(q["category"], q["category"])
        type_name = TYPE_NAMES.get(q["type"], q["type"])
        diff_star = DIFFICULTY_STARS.get(q["difficulty"], "")
        tags_str = " ".join(f"`{t}`" for t in q.get("tags", []))

        lines.append(f"## 第 {i} 题 — {type_name} — {diff_star}")
        lines.append(f"**分类：** {cat_name} / {q.get('subcategory', '')}")
        if tags_str:
            lines.append(f"**标签：** {tags_str}")
        lines.append("")

        # 题目内容
        lines.append(q["question"].strip())
        lines.append("")

        # 选择题选项
        if q["type"] == "multiple_choice" and "options" in q:
            for opt in q["options"]:
                lines.append(f"{opt}")
            lines.append("")

        # 代码模板
        if q["type"] == "coding_problem" and "code_template" in q:
            template = q["code_template"].strip()
            if template:
                lines.append("```c")
                lines.append(template)
                lines.append("```")
                lines.append("")

        # 有 bug 的代码
        if q["type"] == "code_analysis" and "buggy_code" in q:
            buggy = q["buggy_code"].strip()
            if buggy:
                lines.append("```c")
                lines.append(buggy)
                lines.append("```")
                lines.append("")

        lines.append("---")
        lines.append("")

    lines.append(f"*生成于 {target_date} | 题库 ID: {', '.join(q['id'] for q in selected)}*")
    lines.append("")
    return "\n".join(lines)


def render_answers_md(selected, target_date):
    """渲染答案 Markdown"""
    lines = []
    lines.append(f"# 嵌入式 C/C++ 每日答案 — {target_date}")
    lines.append("")
    lines.append("> ⚠️ 请先独立完成题目，再查看答案！")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, q in enumerate(selected, 1):
        type_name = TYPE_NAMES.get(q["type"], q["type"])
        diff_star = DIFFICULTY_STARS.get(q["difficulty"], "")

        lines.append(f"## 第 {i} 题答案 — {type_name} — {diff_star}")
        lines.append("")

        # 选择题：显示正确答案
        if q["type"] == "multiple_choice":
            lines.append(f"**正确答案：{q.get('answer', '')}**")
            lines.append("")

        # 简答题 / 短答案
        if q["type"] == "short_answer":
            lines.append("**参考答案：**")
            lines.append("")
            lines.append(q.get("answer", "").strip())
            lines.append("")

        # 代码分析题
        if q["type"] == "code_analysis":
            lines.append("**问题分析与修复：**")
            lines.append("")
            lines.append(q.get("answer", "").strip())
            lines.append("")
            if "fixed_code" in q:
                lines.append("**修复后的代码：**")
                lines.append("")
                lines.append("```c")
                lines.append(q["fixed_code"].strip())
                lines.append("```")
                lines.append("")

        # 编程题
        if q["type"] == "coding_problem":
            lines.append("**参考实现：**")
            lines.append("")
            if "code_solution" in q:
                lines.append("```c")
                lines.append(q["code_solution"].strip())
                lines.append("```")
                lines.append("")
            if q.get("answer"):
                lines.append(q["answer"].strip())
                lines.append("")

        # 解析
        if q.get("explanation"):
            lines.append("**详细解析：**")
            lines.append("")
            lines.append(q["explanation"].strip())
            lines.append("")

        if q.get("source_reference"):
            lines.append(f"**参考：** {q['source_reference']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append(f"*答案对应日期：{target_date}*")
    lines.append("")
    return "\n".join(lines)


# ============================================================
# 追踪更新
# ============================================================
def update_tracking(tracking, selected, target_date, primary_cat, rotation_idx):
    """更新追踪数据"""
    target_date_str = target_date.strftime("%Y-%m-%d")

    # 更新每题的使用记录
    for q in selected:
        qid = q["id"]
        if qid not in tracking["usage"]:
            tracking["usage"][qid] = {
                "first_served": target_date_str,
                "times_served": 0,
                "dates": [],
                "category": q["category"],
                "difficulty": q["difficulty"],
            }
        tracking["usage"][qid]["times_served"] += 1
        if target_date_str not in tracking["usage"][qid]["dates"]:
            tracking["usage"][qid]["dates"].append(target_date_str)

    # 更新每日记录
    tracking["daily_log"][target_date_str] = {
        "primary_category": primary_cat,
        "question_ids": [q["id"] for q in selected],
        "types": [q["type"] for q in selected],
        "difficulties": [q["difficulty"] for q in selected],
    }

    # 更新轮转状态（rotation_idx 已经是下一个索引）
    tracking["rotation_state"]["current_index"] = rotation_idx
    tracking["metadata"]["total_days_generated"] = len(tracking["daily_log"])


# ============================================================
# 统计功能
# ============================================================
def show_stats(bank, tracking):
    """显示题库使用统计"""
    total_questions = len(bank["questions"])
    usage = tracking.get("usage", {})
    used_ids = set(usage.keys())
    never_used = total_questions - len(used_ids)

    print("=" * 60)
    print("  嵌入式每日题目生成器 — 题库统计")
    print("=" * 60)
    print(f"  题库总题目数：{total_questions}")
    print(f"  已使用题目数：{len(used_ids)}")
    print(f"  未使用题目数：{never_used}")
    print(f"  累计生成天数：{tracking['metadata']['total_days_generated']}")
    print(f"  重复窗口天数：{REPEAT_WINDOW_DAYS}")
    print("=" * 60)

    # 分类统计
    print("\n  分类覆盖情况：")
    print(f"  {'分类':<20} {'总数':>5} {'已用':>5} {'未用':>5} {'使用率':>8}")
    print("  " + "-" * 48)
    cat_counts = defaultdict(lambda: {"total": 0, "used": 0})
    for q in bank["questions"]:
        cat_counts[q["category"]]["total"] += 1
        if q["id"] in used_ids:
            cat_counts[q["category"]]["used"] += 1
    for cat, counts in cat_counts.items():
        name = CATEGORY_NAMES.get(cat, cat)
        rate = counts["used"] / counts["total"] * 100 if counts["total"] > 0 else 0
        print(f"  {name:<18} {counts['total']:>5} {counts['used']:>5} "
              f"{counts['total'] - counts['used']:>5} {rate:>7.1f}%")

    # 难度统计
    print(f"\n  难度分布：")
    diff_counts = defaultdict(int)
    for q in bank["questions"]:
        diff_counts[q["difficulty"]] += 1
    for diff, count in diff_counts.items():
        name = DIFFICULTY_NAMES.get(diff, diff)
        bar = "█" * (count // 2)
        print(f"  {name:<4}: {count:>4} {bar}")

    # 题型统计
    print(f"\n  题型分布：")
    type_counts = defaultdict(int)
    for q in bank["questions"]:
        type_counts[q["type"]] += 1
    for t, count in type_counts.items():
        name = TYPE_NAMES.get(t, t)
        print(f"  {name:<6}: {count:>4}")

    print()


def show_categories(bank):
    """显示分类详情"""
    index = index_questions(bank)
    print("\n  题库分类与子分类：")
    print("=" * 60)
    for cat, name in CATEGORY_NAMES.items():
        questions = index.get(cat, [])
        subcats = defaultdict(int)
        for q in questions:
            subcats[q.get("subcategory", "other")] += 1
        print(f"\n  【{name}】共 {len(questions)} 题")
        for sub, count in sorted(subcats.items()):
            print(f"    - {sub}: {count} 题")
    print()


# ============================================================
# 生成主流程
# ============================================================
def generate_daily(target_date=None, daily_count=DEFAULT_DAILY_COUNT, no_cpp=True):
    """生成每日题目的主流程"""
    # 参数校验
    if daily_count < 3:
        daily_count = 3
    if daily_count > 8:
        daily_count = 8

    # 加载题库
    bank = load_bank()
    if not bank:
        return False

    # 加载追踪
    tracking = load_tracking()

    # 确定日期
    if target_date is None:
        target_date = datetime.now()
    elif isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d")

    target_date_str = target_date.strftime("%Y-%m-%d")

    # 检查是否已生成
    if target_date_str in tracking.get("daily_log", {}):
        print(f"[提示] {target_date_str} 的题目已生成，将覆盖更新。")
        del tracking["daily_log"][target_date_str]

    # 选题
    rotation_table = BEGINNER_ROTATION if no_cpp else CATEGORY_ROTATION
    rotation_idx = tracking["rotation_state"]["current_index"] % len(rotation_table)
    selected, primary_cat = select_questions(bank, tracking, target_date_str, daily_count, no_cpp)

    if len(selected) < daily_count:
        exclude_cats = ["cpp_embedded"] if no_cpp else []
        pool_size = len(build_candidate_pool(bank, tracking, target_date_str, exclude_cats))
        print(f"[警告] 候选题目不足，仅选出 {len(selected)}/{daily_count} 题。")
        print(f"       当前候选池大小：{pool_size}")

    if not selected:
        print("[ERROR] 未能选出任何题目，请检查题库或追踪文件。")
        return False

    # 渲染题目
    questions_md = render_questions_md(selected, target_date_str, primary_cat, rotation_idx, no_cpp)
    answers_md = render_answers_md(selected, target_date_str)

    # 确保输出目录存在
    QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    ANSWERS_DIR.mkdir(parents=True, exist_ok=True)

    # 写入文件
    q_file = QUESTIONS_DIR / f"{target_date_str}.md"
    a_file = ANSWERS_DIR / f"{target_date_str}.md"

    with open(q_file, "w", encoding="utf-8") as f:
        f.write(questions_md)
    with open(a_file, "w", encoding="utf-8") as f:
        f.write(answers_md)

    # 更新追踪（旋转到下一个位置）
    next_idx = (rotation_idx + 1) % len(rotation_table)
    update_tracking(tracking, selected, target_date, primary_cat, next_idx)
    save_tracking(tracking)

    # 输出摘要
    mode_tag = "[入门模式-纯C]" if no_cpp else "[全模式]"
    print(f"[OK] {mode_tag} 已生成 {target_date_str} 的每日题目！")
    print(f"   题目文件：{q_file}")
    print(f"   答案文件：{a_file}")
    print(f"   题目数：{len(selected)}")
    print(f"   主分类：{CATEGORY_NAMES.get(primary_cat, primary_cat)}")
    print(f"   题目 ID：{', '.join(q['id'] for q in selected)}")

    return True


# ============================================================
# 命令行接口
# ============================================================
def main():
    # 修复 Windows 终端编码问题
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="嵌入式 C/C++ 每日练习题目生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate.py                        # 入门模式（纯C，默认）
  python generate.py --cpp                  # 全模式（含C++）
  python generate.py --count 5              # 生成 5 题
  python generate.py --date 2026-06-15      # 指定日期
  python generate.py --stats                # 查看统计
  python generate.py --categories           # 查看分类
        """,
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        help="生成日期 (YYYY-MM-DD)，默认今天",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=DEFAULT_DAILY_COUNT,
        help=f"每日题目数 (3-8)，默认 {DEFAULT_DAILY_COUNT}",
    )
    parser.add_argument(
        "--cpp",
        action="store_true",
        help="全模式：包含 C++ 题目（默认入门模式不含 C++）",
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="显示题库使用统计",
    )
    parser.add_argument(
        "--categories",
        action="store_true",
        help="显示分类覆盖情况",
    )
    parser.add_argument(
        "--week", "-w",
        action="store_true",
        help="一次性生成接下来 7 天的题目",
    )

    args = parser.parse_args()
    no_cpp = not args.cpp  # 默认入门模式（不含 C++）

    # 统计模式
    if args.stats:
        bank = load_bank()
        if bank:
            tracking = load_tracking()
            show_stats(bank, tracking)
        return

    # 分类模式
    if args.categories:
        bank = load_bank()
        if bank:
            show_categories(bank)
        return

    # 生成一周
    if args.week:
        start = datetime.now()
        success = 0
        for i in range(7):
            d = start + timedelta(days=i)
            print(f"\n--- {d.strftime('%Y-%m-%d')} ---")
            if generate_daily(target_date=d, daily_count=args.count, no_cpp=no_cpp):
                success += 1
        print(f"\n[Done] 完成！成功生成 {success}/7 天的题目。")
        return

    # 生成单日
    generate_daily(target_date=args.date, daily_count=args.count, no_cpp=no_cpp)


if __name__ == "__main__":
    main()
