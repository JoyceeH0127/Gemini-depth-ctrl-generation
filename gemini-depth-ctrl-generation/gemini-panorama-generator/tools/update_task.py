#!/usr/bin/env python3
"""
任务状态更新工具

用法:
    python tools/update_task.py --task 1 --status in_progress --assignee @username
    python tools/update_task.py --task 1 --status completed
    python tools/update_task.py --list  # 列出所有任务
"""

import re
import argparse
import sys
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TASKS_FILE = PROJECT_ROOT / "TASKS.md"

# 状态映射
STATUS_MAP = {
    "pending": "⏳ 待开始",
    "in_progress": "🔄 进行中",
    "paused": "⏸️ 暂停",
    "completed": "✅ 已完成",
    "cancelled": "❌ 已取消",
    "blocked": "🔗 依赖其他任务",
}

STATUS_EMOJI = {
    "⏳ 待开始": "pending",
    "🔄 进行中": "in_progress",
    "⏸️ 暂停": "paused",
    "✅ 已完成": "completed",
    "❌ 已取消": "cancelled",
    "🔗 依赖其他任务": "blocked",
}


def read_tasks_file():
    """读取 TASKS.md 文件"""
    if not TASKS_FILE.exists():
        print(f"错误: 找不到 {TASKS_FILE}")
        sys.exit(1)
    return TASKS_FILE.read_text(encoding="utf-8")


def write_tasks_file(content):
    """写入 TASKS.md 文件"""
    TASKS_FILE.write_text(content, encoding="utf-8")


def find_task_section(content, task_num):
    """查找任务部分"""
    pattern = rf"### Task #{task_num}:"
    match = re.search(pattern, content)
    if not match:
        return None, None, None
    
    start = match.start()
    # 查找下一个任务或章节的开始
    next_task = re.search(rf"### Task #{task_num + 1}:", content[start:])
    if next_task:
        end = start + next_task.start()
    else:
        # 查找下一个优先级章节
        next_section = re.search(r"## 🟡|## 🟢|## 📝", content[start:])
        if next_section:
            end = start + next_section.start()
        else:
            end = len(content)
    
    return start, end, content[start:end]


def update_task_status(content, task_num, status, assignee=None, note=None):
    """更新任务状态"""
    start, end, task_section = find_task_section(content, task_num)
    if task_section is None:
        print(f"错误: 找不到 Task #{task_num}")
        return None
    
    # 更新状态
    status_text = STATUS_MAP.get(status, status)
    task_section = re.sub(
        r"- \*\*状态\*\*: .*",
        f"- **状态**: {status_text}",
        task_section
    )
    
    # 更新负责人
    if assignee:
        if re.search(r"- \*\*负责人\*\*:", task_section):
            task_section = re.sub(
                r"- \*\*负责人\*\*: .*",
                f"- **负责人**: {assignee}",
                task_section
            )
        else:
            # 在状态后添加负责人行
            task_section = re.sub(
                r"- \*\*状态\*\*: .*",
                f"- **状态**: {status_text}\n- **负责人**: {assignee}",
                task_section
            )
    
    # 添加日期
    today = datetime.now().strftime("%Y-%m-%d")
    if status == "in_progress":
        if not re.search(r"- \*\*开始日期\*\*:", task_section):
            task_section = re.sub(
                r"- \*\*负责人\*\*: .*",
                f"- **负责人**: {assignee or '_待分配_'}\n- **开始日期**: {today}",
                task_section
            )
    elif status == "completed":
        if re.search(r"- \*\*实际完成\*\*:", task_section):
            task_section = re.sub(
                r"- \*\*实际完成\*\*: .*",
                f"- **实际完成**: {today}",
                task_section
            )
        else:
            # 在预计完成日期后添加实际完成日期
            task_section = re.sub(
                r"- \*\*预计完成\*\*: .*",
                f"- **预计完成**: _待更新_\n- **实际完成**: {today}",
                task_section
            )
    
    # 添加备注
    if note:
        if re.search(r"- \*\*备注\*\*:", task_section):
            task_section = re.sub(
                r"- \*\*备注\*\*: .*",
                f"- **备注**: {note}",
                task_section
            )
        else:
            task_section = task_section.rstrip() + f"\n- **备注**: {note}\n"
    
    # 替换原内容
    new_content = content[:start] + task_section + content[end:]
    return new_content


def update_progress_stats(content):
    """更新总体进度统计"""
    # 统计任务状态
    total = len(re.findall(r"### Task #\d+:", content))
    completed = len(re.findall(r"- \*\*状态\*\*: ✅ 已完成", content))
    in_progress = len(re.findall(r"- \*\*状态\*\*: 🔄 进行中", content))
    pending = len(re.findall(r"- \*\*状态\*\*: ⏳ 待开始", content))
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    # 更新统计部分
    stats_pattern = r"- \*\*总任务数\*\*: \d+\n- \*\*已完成\*\*: \d+\n- \*\*进行中\*\*: \d+\n- \*\*待开始\*\*: \d+\n- \*\*完成率\*\*: [\d.]+%"
    stats_replacement = (
        f"- **总任务数**: {total}\n"
        f"- **已完成**: {completed}\n"
        f"- **进行中**: {in_progress}\n"
        f"- **待开始**: {pending}\n"
        f"- **完成率**: {completion_rate:.1f}%"
    )
    
    content = re.sub(stats_pattern, stats_replacement, content)
    return content


def list_tasks(content):
    """列出所有任务"""
    tasks = re.findall(
        r"### Task #(\d+): (.+?)\n- \*\*状态\*\*: (.+?)\n- \*\*优先级\*\*: (.+?)\n- \*\*负责人\*\*: (.+?)\n",
        content,
        re.DOTALL
    )
    
    if not tasks:
        print("未找到任务")
        return
    
    print("\n📋 任务列表:\n")
    print(f"{'ID':<6} {'状态':<12} {'优先级':<8} {'负责人':<15} {'任务名称'}")
    print("-" * 80)
    
    for task_num, name, status, priority, assignee in tasks:
        name = name.strip()
        status = status.strip()
        priority = priority.strip()
        assignee = assignee.strip()
        print(f"#{task_num:<5} {status:<12} {priority:<8} {assignee:<15} {name[:40]}")


def main():
    parser = argparse.ArgumentParser(description="更新任务状态")
    parser.add_argument("--task", type=int, help="任务编号")
    parser.add_argument(
        "--status",
        choices=["pending", "in_progress", "paused", "completed", "cancelled", "blocked"],
        help="任务状态"
    )
    parser.add_argument("--assignee", help="负责人 (@username)")
    parser.add_argument("--note", help="备注")
    parser.add_argument("--list", action="store_true", help="列出所有任务")
    
    args = parser.parse_args()
    
    if args.list:
        content = read_tasks_file()
        list_tasks(content)
        return
    
    if not args.task:
        parser.print_help()
        sys.exit(1)
    
    if not args.status:
        print("错误: 必须指定 --status")
        sys.exit(1)
    
    content = read_tasks_file()
    new_content = update_task_status(
        content,
        args.task,
        args.status,
        args.assignee,
        args.note
    )
    
    if new_content:
        new_content = update_progress_stats(new_content)
        write_tasks_file(new_content)
        print(f"✅ 已更新 Task #{args.task} 状态为: {STATUS_MAP[args.status]}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
