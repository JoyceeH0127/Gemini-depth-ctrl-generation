# 协作开发指南

本文档说明如何参与项目优化任务的协作开发，包含任务追踪使用指南和开发规范。

## 📋 目录

- [任务追踪快速开始](#-任务追踪快速开始)
- [详细使用指南](#-详细使用指南)
- [开始一个新任务](#-开始一个新任务)
- [完成任务](#-完成任务)
- [协作流程](#-协作流程)
- [代码规范](#-代码规范)
- [相关文档](#-相关文档)

---

## ⚡ 任务追踪快速开始

### 核心文件

- **`TASKS.md`**: 主任务清单（所有任务详情）
- **`tools/update_task.py`**: 任务状态更新工具

### 常用命令

```bash
# 1. 查看所有任务
python tools/update_task.py --list

# 2. 开始任务（分配给自己）
python tools/update_task.py --task 1 --status in_progress --assignee @your-username

# 3. 完成任务
python tools/update_task.py --task 1 --status completed

# 4. 添加备注
python tools/update_task.py --task 1 --note "已完成图像提取部分"
```

### 快速工作流程示例

**场景：开始 Task #1**

```bash
# 1. 查看任务列表
python tools/update_task.py --list

# 2. 更新任务状态
python tools/update_task.py --task 1 --status in_progress --assignee @alice

# 3. 创建 Git 分支
git checkout -b task/1-extract-image-processing

# 4. 开始开发...
# ... 编写代码 ...

# 5. 完成任务
python tools/update_task.py --task 1 --status completed

# 6. 提交代码
git add .
git commit -m "feat: complete Task #1 - extract image processing logic"
git push origin task/1-extract-image-processing
```

**场景：开始依赖任务（Task #2 依赖 Task #1）**

```bash
# 1. 检查依赖任务状态（查看 TASKS.md，确认 Task #1 状态为 ✅ 已完成）

# 2. 更新任务状态
python tools/update_task.py --task 2 --status in_progress --assignee @bob

# 3. 从主分支合并 Task #1 的更改
git checkout main
git pull
git checkout -b task/2-extract-business-logic

# 4. 开始开发...
```

---

## 📖 详细使用指南

### 任务追踪方式

项目使用以下方式追踪任务进度：

1. **TASKS.md**: 主任务清单，包含所有优化任务的详细信息和状态
2. **GitHub Issues** (可选): 如果使用 GitHub，可以为每个任务创建 Issue
3. **Git 分支**: 每个任务使用独立分支，命名规范：`task/1-refactor-app-py`

### 查看任务列表

```bash
# 使用工具脚本查看
python tools/update_task.py --list

# 或直接查看文件
cat TASKS.md
```

### 任务状态说明

| 状态 | 符号 | 说明 |
|------|------|------|
| 待开始 | ⏳ | 任务尚未开始 |
| 进行中 | 🔄 | 任务正在进行 |
| 暂停 | ⏸️ | 任务暂时暂停 |
| 已完成 | ✅ | 任务已完成 |
| 已取消 | ❌ | 任务已取消 |
| 依赖其他任务 | 🔗 | 等待依赖任务完成 |

### 工具脚本使用

#### 更新任务状态

```bash
# 开始任务
python tools/update_task.py --task 1 --status in_progress --assignee @alice

# 完成任务
python tools/update_task.py --task 1 --status completed

# 暂停任务
python tools/update_task.py --task 1 --status paused --note "等待 API 更新"

# 添加备注
python tools/update_task.py --task 1 --note "已完成图像处理部分"
```

#### 列出所有任务

```bash
python tools/update_task.py --list
```

### 手动更新（如果不用脚本）

如果不想使用脚本，可以直接编辑 `TASKS.md`：

1. 找到对应的任务部分
2. 更新状态、负责人等信息
3. 更新顶部的进度统计

### 进度追踪

#### 自动更新

使用 `update_task.py` 脚本会自动更新总体进度统计。

#### 手动更新

在 `TASKS.md` 顶部更新：

```markdown
- **总任务数**: 8
- **已完成**: 3
- **进行中**: 2
- **待开始**: 3
- **完成率**: 37.5%
```

#### 状态日志

在完成任务时，可以在"任务状态更新日志"部分添加记录：

```markdown
| 2024-12-19 | Task #1 | 开始 | @alice | 开始重构 app.py |
| 2024-12-20 | Task #1 | 完成 | @alice | 已提取图像处理逻辑 |
```

---

## 🚀 开始一个新任务

### 1. 选择任务

查看 `TASKS.md`，选择一个状态为 `⏳ 待开始` 的任务。

### 2. 检查依赖

确保所有依赖任务已完成（状态为 `✅ 已完成`）。

### 3. 更新任务状态

使用工具脚本更新：

```bash
python tools/update_task.py --task 1 --status in_progress --assignee @your-username
```

或手动在 `TASKS.md` 中更新任务信息：

```markdown
### Task #X: [任务名称]
- **状态**: 🔄 进行中
- **负责人**: @your-username
- **开始日期**: 2024-12-19
- **预计完成**: 2024-12-20
```

### 4. 创建分支

```bash
git checkout -b task/X-task-name
```

### 5. 开始开发

按照任务描述和验收标准进行开发。

---

## ✅ 完成任务

### 1. 自检清单

- [ ] 代码符合项目规范
- [ ] 所有验收标准已满足
- [ ] 相关测试通过
- [ ] 文档已更新
- [ ] 代码已通过审查（如果有）

### 2. 更新任务状态

使用工具脚本：

```bash
python tools/update_task.py --task 1 --status completed
```

或手动在 `TASKS.md` 中更新：

```markdown
### Task #X: [任务名称]
- **状态**: ✅ 已完成
- **实际完成**: 2024-12-20
```

### 3. 提交代码

```bash
git add .
git commit -m "feat: complete Task #X - [任务名称]"
git push origin task/X-task-name
```

### 4. 创建 Pull Request (如果使用)

- 标题: `[Task #X] 任务名称`
- 描述: 引用任务编号和验收标准
- 等待代码审查和合并

---

## 🤝 协作流程

### 场景 1: 选择任务

1. 查看 `TASKS.md` 找到 `⏳ 待开始` 的任务
2. 立即更新状态为 `🔄 进行中` 并填写负责人
3. 创建分支开始开发

### 场景 2: 任务冲突

如果多个开发者想选择同一任务：

1. 在 `TASKS.md` 中先更新状态为 `🔄 进行中`
2. 在备注中说明分工
3. 或通过 Issue/讨论协调

### 场景 3: 任务依赖

如果任务 A 依赖任务 B：

1. 等待任务 B 完成（状态为 `✅ 已完成`）
2. 从任务 B 的分支创建新分支
3. 或从主分支合并任务 B 的更改后再开始

### 场景 4: 多人协作同一任务

如果任务较大，可以拆分子任务：

1. 在 `TASKS.md` 中创建子任务
2. 每个开发者负责一个子任务
3. 使用独立分支开发
4. 完成后合并到主任务分支

---

## 📝 代码规范

### 提交信息格式

```
<type>: <subject>

<body>

<footer>
```

**Type 类型**:
- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
refactor: extract image processing logic to utils/image_utils.py

- Move image extraction logic from app.py
- Create utils/image_utils.py module
- Update app.py to use new module

Closes Task #1
```

### Python 代码规范

- 遵循 PEP 8
- 使用类型提示（Python 3.10+）
- 添加必要的文档字符串
- 保持函数简洁（单一职责）

---

## 💡 最佳实践

1. **及时更新**: 任务状态变化时立即更新
2. **清晰备注**: 在备注中说明重要信息
3. **遵循依赖**: 按依赖关系顺序完成任务
4. **代码审查**: 完成任务后进行代码审查
5. **文档同步**: 完成任务后更新相关文档
6. **先到先得**: 看到待开始任务后立即更新状态，避免冲突

---

## 🐛 遇到问题？

1. **任务不清楚**: 在 `TASKS.md` 的备注中提问，或创建 Issue
2. **技术问题**: 在项目讨论区或 Issue 中提问
3. **任务需要调整**: 更新 `TASKS.md` 中的任务描述，并说明原因

---

## 📚 相关文档

- `TASKS.md`: 任务清单
- `PROJECT_ANALYSIS.md`: 项目分析报告
- `README.md`: 项目说明
- `ARCHITECTURE.md`: 架构文档（待创建）

---

**提示**: 如果使用 GitHub，可以为每个任务创建 Issue，并在 PR 中引用 Issue 编号。

**最后更新**: 2024-12-19
