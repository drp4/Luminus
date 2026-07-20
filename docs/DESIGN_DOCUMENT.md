# Children Growth OS — 设计文档

> 基于 2026-07-18 Grilling Session 决策汇总
>
> 参考：[PROJECT_VISION.md](PROJECT_VISION.md) | [os.txt](../os.txt)

---

# 1. 领域模型

## 1.1 核心实体

MVP 阶段确定 5 个核心领域实体：

```
Child ──1:N── Memory ──N:N── Agent
  │
  └──1:1── GrowthProfile
              │
              ├──1:N── ProfileSnapshot
              └──1:N── InterestModel
              │
              ▼
         Profile Engine  ← 计算层，生成 Human Block

Agent ──N:N── Persona
Agent ──N:N── Capability
  │
  └── Capability ──1:N── Tool
```

### Child（孩子）

MVP 轻量设计，不做完整用户系统。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 唯一标识 |
| `nickname` | string | 孩子自己起的名字 |
| `age` | int | 8-11 |
| `grade` | string | 3-5 年级 |
| `avatar_seed` | string | 头像种子值 |
| `created_at` | datetime | 注册时间 |

刻意不放：真实姓名、性别、手机号、密码、家长信息（MVP 不需要，后续版本可扩展）。

身份持久化：设备 ID + 本地存储，不建复杂认证体系。

### Persona（AI 伙伴人格）

Companion 不独立建表，而是 Persona 配置 + Agent + Memory 的组合投影。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 唯一标识 |
| `name` | string | 伙伴名字（如「小阳」「星星」） |
| `personality` | string | 性格描述，注入 system prompt |
| `speaking_style` | string | 说话风格，同龄人语气 |
| `age_feel` | string | 年龄感（同龄/稍大/温和长辈） |
| `is_default` | bool | 是否默认人格 |

孩子从系统预设中选择一个伙伴人格。运行时 Agent 加载对应 persona 到 system prompt。

### Agent（智能体）

配置驱动，运行时由 LangGraph 动态创建。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 唯一标识 |
| `name` | string | Agent 名称 |
| `type` | enum | conversation / teacher / memory / story / planner / emotion / game / parent / safety / reflection |
| `system_prompt_template` | text | System prompt 模板，含 {persona} {human_block} 占位符 |
| `loop_config` | jsonb | Loop 策略配置（触发条件、频率、反馈指标） |
| `is_active` | bool | 是否启用 |

Agent-Persona 多对多绑定。

### Capability（能力）

Tool 不直接绑定 Agent。通过 Capability 分组：

```
Agent ──N:N── Capability ──1:N── Tool
```

| 层级 | 说明 | 示例 |
|------|------|------|
| **Capability** | 一组相关能力的逻辑分组 | Memory Capability、Story Capability、Image Capability |
| **Tool** | 具体函数 | search_memory()、save_memory()、summarize_memory() |

MVP 阶段 Tool 数量少，代码里预留 Capability 分组接口。后续 MCP 或第三方 API 接入时，Capability 可以是本地实现、MCP Server 或外部 API —— Agent 不需要知道。

Tool 表定义：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 唯一标识 |
| `capability_id` | UUID | 所属 Capability 分组 |
| `name` | string | 工具名称 |
| `description` | string | 功能描述（给 LLM 看的） |
| `schema` | jsonb | 参数 JSON Schema |

### Memory（记忆）

五层记忆模型，混合存储架构。

| 记忆层 | 生命周期 | 存储位置 | 说明 |
|--------|----------|----------|------|
| **Short Memory** | 单次会话 | LangGraph state + Redis | 当前对话上下文 |
| **Working Memory** | 单次探索 | LangGraph 工作流状态 | 当前任务步骤 |
| **Long Memory** | 跨会话 | pgvector（自托管） | 自然语言语义记忆，按 child_id 分区 |
| **Growth Memory** | 永久 | PostgreSQL 结构化表 | 成长画像、兴趣向量、能力曲线 |
| **World Memory** | 静态+更新 | PostgreSQL | 场景知识库，属于 Content 服务 |

Memory 存储选型：**pgvector 替代 Mem0**。

理由：
- 儿童对话数据隐私敏感，不能上云
- 支持数据删除（GDPR/COPPA「被遗忘权」）
- 零额外依赖，PostgreSQL 已在使用
- Mem0 ADD-only 设计对儿童场景不利
- Mem0 默认走 OpenAI 云端做 memory extraction

借鉴 Letta Memory Blocks 模式，新增两个上下文 Block：

| Block | 内容 | 注入方式 |
|-------|------|----------|
| **Persona Block** | Agent 人格描述 | 直接注入 system prompt |
| **Human Block** | 孩子的简明状态摘要 | 直接注入 system prompt |

### GrowthProfile（成长画像）

两层建模，是系统的核心资产。

**层 1：Profile Snapshot（快照表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `child_id` | UUID | 外键 |
| `recorded_at` | datetime | 快照时间 |
| `vocabulary_level` | enum | simple / moderate / advanced |
| `interests` | jsonb | 兴趣标签 + 权重 |
| `curiosity_score` | float 0-1 | 好奇心指数 |
| `expression_score` | float 0-1 | 表达能力指数 |
| `reading_score` | float 0-1 | 阅读能力指数 |
| `thinking_score` | float 0-1 | 思考能力指数 |
| `active_question_count` | int | 主动提问次数 |
| `avg_session_minutes` | float | 平均会话时长 |
| `emotion_trend` | jsonb | 情绪趋势分布 |
| `learning_style` | enum | visual / storytelling / hands_on / questioning |

**层 2：Interest Model（兴趣模型表）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `child_id` | UUID | 外键 |
| `topic` | string | 兴趣主题 |
| `weight` | float 0-1 | 当前兴趣强度 |
| `first_seen_at` | datetime | 首次表现兴趣 |
| `last_seen_at` | datetime | 最近涉及 |
| `trend` | enum | rising / stable / declining |
| `source` | enum | explicit_statement / implicit_clue / story_choice |

更新策略：
- Snapshot 由 Growth Loop 每周生成，形成时间序列
- Interest Model 由 Reflection Loop 每次会话后增量更新
- 数据不直接暴露给孩子，通过 Human Block 摘要注入 Agent prompt

### Profile Engine（成长画像引擎）

GrowthProfile 是原始数据。Agent 不应该直接读数据库，应该读**经过分析后的孩子模型**。

```
GrowthProfile 表
      │
      ▼
Profile Engine  ← 计算层
      │
      ├── 兴趣融合（多个 interest topic → 综合兴趣画像）
      ├── 能力评分（vocabulary + expression + reading + thinking → 综合能力指数）
      ├── 学习风格推断（从交互模式推测 visual/storytelling/hands_on/questioning）
      ├── 情绪趋势分析（emotion_trend 时间序列 → 当前情绪状态）
      ├── Human Block 生成（上述分析 → 简明自然语言摘要）
      └── Prompt Summary（给不同 Agent 裁剪不同版本的摘要）
      │
      ▼
Human Block → Agent Prompt
```

设计原则：
- 后续新增指标（社交能力、专注力、创造力）只需修改 Profile Engine，Agent 不改
- Human Block 长度卡上限（~500 chars），确保不撑爆 context window
- 不同 Agent 拿不同版本的摘要：Conversation Agent 要温暖版本，Teacher Agent 要能力评估版本

---

# 2. Agent 架构

## 2.1 MVP Agent 列表

| Agent | 类型 | Persona | 面对用户 | 说明 |
|-------|------|---------|----------|------|
| **Conversation Agent** | conversation | 温暖的朋友 | 是 | 日常聊天，记忆感知 |
| **Teacher Agent** | teacher | 好奇的引导者 | 是 | 苏格拉底式提问，隐藏式学习 |
| **Memory Agent** | memory | 无 | 否 | 后台 Agent，Reflection + Growth Loop |

## 2.2 Agent 能力定义

```
Conversation Agent:
  ├── Persona: "温暖的朋友，同龄人语气"
  ├── Tools: [search_memory, save_memory, get_child_info]
  └── Guardrails: [不过度教育, 不评判, 不直接给答案, 内容安全过滤]

Teacher Agent:
  ├── Persona: "好奇的引导者，苏格拉底式提问"
  ├── Tools: [search_memory, search_world_knowledge, get_growth_profile]
  └── Guardrails: [永不说'你错了', 引导不直接告诉, 难度自适应]

Memory Agent:
  ├── 类型: 后台 Agent，不直接面对孩子
  ├── Triggers: [会话结束事件, 每N次会话, 每日定时]
  └── Tasks: [提炼 Long Memory → pgvector, 更新 Interest Model, 生成 Profile Snapshot, 生成 Human Block 摘要]
```

后续版本逐步增加：Story、Planner、Emotion、Game、Parent、Safety、Reflection

## 2.3 Agent Runtime（AOS 内核）

Runtime 是整个系统的调度中心，包在 LangGraph StateGraph 外层。

```
Gateway
   │
   ▼
Runtime  ← 系统唯一入口
   │
   ├── Context 管理（组装 Persona Block + Human Block + 对话历史）
   ├── Persona 注入（从配置加载 → 注入 system prompt）
   ├── Human Block 注入（调用 Profile Engine → 注入 system prompt）
   ├── Tool Registry（Agent 需要哪些 Tool → 注入 function definitions）
   ├── Agent 生命周期（创建 → 运行 → 销毁）
   ├── Loop 调度（Interaction / Reflection / Growth 触发与流转）
   ├── Event 分发（会话事件 → 触发 Reflection/Growth）
   ├── Guardrails（输入/输出安全过滤，装饰器模式）
   ├── Logging & Telemetry（全链路追踪）
   │
   ▼
StateGraph（LangGraph）
   │
   ▼
Agent
```

Runtime 的定位：**AOS（Agent Operating System）的内核**。所有 Agent 全部通过 Runtime 调度，不直接暴露给 Gateway。

## 2.4 Loop Engineering + Event Bus

三层 Loop + Event 驱动，形成混合架构。

### 三层 Loop

| Loop | 频率 | 职责 | 执行者 |
|------|------|------|--------|
| **Interaction Loop** | 实时（每次对话） | 感知→决策→行动→观察→调整 | Conversation / Teacher Agent |
| **Reflection Loop** | 准实时（会话结束） | 提炼记忆→更新 Human Block →下次更个性化 | Memory Agent |
| **Growth Loop** | 低频（每日/每周） | 分析兴趣变化→更新 Growth Profile →调整内容策略 | Memory Agent |

### Event Bus

MVP 使用 Python 内置轻量 pub/sub（`asyncio.Event` 或简单 EventEmitter），后续可升级到 Redis Stream / RabbitMQ / Kafka。

事件契约：

```
conversation.turn.added   → 每次对话轮次完成
conversation.ended        → 会话结束 → 触发 Reflection Loop
reflection.completed      → Reflection 完成 → 触发 Growth 检查
interest.changed          → 兴趣变化 → 重新生成 Human Block
growth.snapshot.created   → 新快照生成 → 通知 Teacher Agent 调整策略
```

核心原则：Loop 之间不直接互相调用，全部通过 Event Bus 分发。这样后续新增能力（成就系统、故事解锁、家长通知）只需订阅对应事件，不改现有代码。

LoopOrchestrator 收敛到 Runtime 内部，作为 Runtime 的 Loop 调度模块。

---

# 3. Agent StateGraph 设计

参考：LangGraph `create_react_agent` 模式 + NirDiamant/GenAI_Agents 的 n-Node Workflow with Validation Loops 实践。

StateGraph 运行在 Runtime 内部，Runtime 负责组装 Context 和注入 Prompt 后再进入图。

## 3.1 完整请求链路

```
Gateway
   │
   ▼
Runtime
   ├── 1. 加载 Persona → Persona Block
   ├── 2. 调用 Profile Engine → Human Block
   ├── 3. 组装 Context（messages + blocks + state）
   ├── 4. 通过 Guardrails 输入过滤
   ├── 5. 注入 Tool Registry → function definitions
   │
   ▼
StateGraph（LangGraph）
   │
   ├── Intent Router → Chat / Teacher Agent ⇄ Tool Executor
   │
   ▼
Runtime
   ├── 6. Guardrails 输出过滤
   ├── 7. SSE Stream → 前端
   ├── 8. 发射 conversation.turn.added 事件
   └── 9. 会话结束 → 发射 conversation.ended 事件 → Memory Agent
```

## 3.2 图结构

```
                    ┌──────────────────────────────────────┐
                    │         LangGraph StateGraph          │
                    │                                       │
    START ──────────► [Intent Router]                       │
                         │                                  │
                    ┌────┴────┐                             │
                    ▼         ▼                             │
            [Chat Agent]  [Teacher Agent]                   │
                    │         │                             │
                    └────┬────┘                             │
                         ▼                                  │
                    [Tool Executor]                         │
                         │                                  │
                    ┌────┴────┐                             │
                    ▼         ▼                             │
              (有结果)    (该回复了)                           │
                    │         │                             │
                    └────┬────┘                             │
                         ▼                                  │
                      [END]                                 │
                                                           │
  ┌──────────────────────────────────────────────────────┐ │
  │  异步层（Event Bus 驱动，不阻塞对话）                     │ │
  │  conversation.ended → Memory Agent: Reflection Loop    │ │
  │  reflection.completed → Growth 检查                     │ │
  │  interest.changed → Profile Engine: 重新生成 Human Block│ │
  └──────────────────────────────────────────────────────┘ │
```

## 3.3 节点说明

| 节点 | 类型 | 说明 |
|------|------|------|
| **Intent Router** | 确定性路由（不调 LLM） | 关键词/场景匹配，决定 Chat 还是 Teacher。原则：能不用 LLM 就不用 |
| **Chat Agent** | LLM + Tool Calling | 日常聊天，记忆感知，ReAct 循环 |
| **Teacher Agent** | LLM + Tool Calling | 教育场景，苏格拉底引导，知识隐藏在对话中 |
| **Tool Executor** | 确定性执行 | 统一工具调用层，执行 search_memory / get_child_info 等 |

循环逻辑：Agent 节点可多次调用工具（Agent → Tool Executor → Agent → ...），直到决定回复，才走向 END。

## 3.4 State 定义

```python
from typing import TypedDict

class ConversationState(TypedDict):
    child_id: str
    persona_block: str        # 注入 prompt 的人格摘要
    human_block: str          # 注入 prompt 的孩子摘要
    messages: list[dict]      # 对话历史（当前会话）
    agent_type: str           # chat / teacher
    tool_results: list[dict]  # 工具调用结果
    should_reflect: bool      # 会话结束后是否触发 Reflection
```

使用 TypedDict（LangGraph 社区标准）。

## 3.5 安全策略

不在 StateGraph 内建安全节点。改为外层 Middleware/装饰器模式：

```python
# 参考 GenAI_Agents 的 AgentContract 模式
@enforce(load_contract("child-safety.contract.yaml"))
async def process_message(state: ConversationState) -> ConversationState:
    ...
```

具体规则：
- 敏感词过滤（输入 + 输出双向）
- 年龄适配（内容不过于成熟）
- 不收集 PII（个人身份信息）
- 永远不评判孩子

## 3.6 流式输出

SSE (Server-Sent Events)，每个 token 逐字返回前端。

---

# 4. 技术架构

## 4.1 技术栈

```
Flutter (Mobile)
      │
      ▼
FastAPI (Gateway)
      │
      ▼
Agent Runtime (AOS Kernel)
      │
      ├── Context 管理
      ├── Profile Engine
      ├── Guardrails
      ├── Event Bus
      ├── Tool Registry
      └── Loop 调度
      │
      ▼
LangGraph (Agent StateGraph)
      │
      ├── OpenAI (LLM)
      ├── pgvector (Long Memory)
      ├── PostgreSQL (Structured Data)
      ├── Redis (Session Cache)
      └── MinIO (Static Assets)
```

Java / Python 分工：

| Java（未来） | Python（当前） |
|-------------|---------------|
| 支付、登录、权限 | Agent、Memory、RAG |
| 运营后台、统计 | Workflow、LLM、Reasoning |

## 4.2 MVP 目录结构

```
children-growth-os/
│
├── docs/
│   ├── PROJECT_VISION.md
│   ├── DESIGN_DOCUMENT.md        ← 本文档
│   └── ...
│
├── services/
│   ├── gateway/         ← FastAPI 入口，MVP 需要
│   ├── runtime/         ← Agent Runtime（AOS 内核），MVP 需要
│   │   ├── context/     ← Context 组装（Persona + Human Block + History）
│   │   ├── registry/    ← Tool Registry + Capability Registry
│   │   ├── guardrails/  ← 输入/输出安全过滤
│   │   ├── events/      ← Event Bus（轻量 pub/sub）
│   │   └── loops/       ← Loop 调度（Interaction/Reflection/Growth）
│   ├── agent/           ← LangGraph StateGraph + Agent 定义，MVP 需要
│   ├── memory/          ← pgvector + Memory Agent + Profile Engine，MVP 需要
│   ├── story/           ← 先空着
│   ├── profile/         ← GrowthProfile 表 + API，MVP 需要（轻量）
│   └── content/         ← 先空着
│
├── apps/
│   ├── mobile/          ← 先空着
│   └── admin/           ← 先空着
│
├── prompts/
├── stories/
├── datasets/
└── infra/
```

---

# 5. Story 架构（AI 互动故事）

## 5.1 数据模型

```
Story
 ├── 基本信息 (title, theme, target_age, difficulty_level)
 ├── Characters[] (角色名, 性格, visual_seed)
 ├── Chapters[]
 │    └── Scenes[]
 │         ├── text (场景叙述, 200-400字)
 │         ├── image_prompt (画面描述)
 │         ├── choices[] (2-3个分支选项)
 │         └── knowledge_points[] (隐藏知识点)
 └── StorySession (跨会话进度)
```

7 张表：`stories`, `story_chapters`, `story_scenes`, `story_choices`, `story_knowledge_points`, `story_characters`, `story_sessions`

## 5.2 Story Agent 三阶段流水线

借鉴 `AI-agent-story-teller` 的多 Agent + LLM Judge 模式：

```
Stage 1: Story Planner (temperature=0.6)
  输入: 孩子兴趣 + 年龄 + 学习风格
  输出: 故事大纲 (标题/主题/角色/章节概要)

Stage 2: Scene Generator (temperature=0.8)
  输入: 故事信息 + 章节上下文 + 前一场景
  输出: 场景文本 + 分支选项 + 隐藏知识点

Stage 3: Story Judge (temperature=0.2)
  评分: 趣味性/教育价值/年龄适配/选择质量 (各1-10分)
  阈值: total >= 7.0 通过, 否则重写 (最多2次)
```

## 5.3 核心特色

| 特色 | 实现 |
|------|------|
| **兴趣驱动** | 故事主题从 Interest Model 自动匹配 |
| **难度自适应** | 根据 Growth Profile 调整语言复杂度 |
| **知识隐藏** | 每个场景嵌入 knowledge_points (学科/概念/词汇) |
| **选择分支** | 每场景 2-3 个选项，影响故事走向 |
| **跨会话续写** | StorySession 保存进度，可随时恢复 |
| **三阶段质控** | Story Judge 自动评分，不通过则重写 |

## 5.4 API

| 端点 | 说明 |
|------|------|
| `POST /api/v1/stories` | 创建故事 (Stage 1: Plan) |
| `GET /api/v1/stories?child_id=` | 列出孩子的所有故事 |
| `GET /api/v1/stories/{id}` | 获取故事详情 (含所有场景) |
| `POST /api/v1/stories/{id}/scene` | 生成下一场景 (Stage 2+3) |
| `POST /api/v1/stories/{id}/choose` | 做选择并生成后续场景 |

---

# 6. MVP 范围

## 6.1 MVP 切片

选择 **聊天链路** 作为端到端切片：

> 孩子打开 App → 和 AI 聊天 → Memory Agent 记住 → 下次对话引用

理由：最小闭环，不依赖内容库，直接验证 Day-7 Retention。

## 6.2 MVP 三页面

| 页面 | 功能 |
|------|------|
| **Home** | 「今天去哪探险？」— 每日入口 |
| **Story** | AI 互动故事 | ✅ 已实现 |
| **Profile** | 成长花园 | ✅ 已实现 |

## 6.3 MVP 一定做
- AI 聊天
- AI 互动故事 (三阶段流水线 + LLM 质检)
- 隐藏式学习
- 长期记忆
- 成长花园
- 每日探索

## 6.4 MVP 坚决不做

英语课程、数学课程、家长后台、支付、商城、会员、MCP、复杂 Agent、RAG、知识图谱、视频、语音、多模态

---

# 7. 成功指标

| 优先级 | 指标 | 说明 |
|--------|------|------|
| P0 | Day-7 Retention | 第一指标 |
| P1 | Average Session Time | 孩子愿意待多久 |
| P2 | 孩子主动提问次数 | 好奇心驱动 |

不是 DAU、Token 消耗、收入。

---

# 8. Roadmap

```
V1: 故事陪伴 ──→ V2: 兴趣发现 ──→ V3: 成长画像
                                      │
                                      ▼
                              V5: 真正因材施教 ←── V4: 长期规划
```

---

# 9. 未决事项（待后续讨论）

1. Flutter 移动端具体 UI 设计
2. 世界观内容（World Memory）的具体场景和知识点
3. Persona 的具体性格描述文案
4. 安全合约（child-safety.contract.yaml）的具体规则
5. 数据库表结构 DDL
6. API 接口设计

---

# 10. 文档结构演进

当前文档章节：

```
领域模型 → Agent → StateGraph → 技术架构
```

建议未来文档重组为：

```
1. Vision（愿景）
2. Runtime（内核）
3. Agent（智能体层）
4. Capability（能力层）
5. Cognition（认知层）
6. Memory（记忆层）
7. Growth Engine（成长引擎）
8. Applications（应用层）
9. Infrastructure（基础设施）
```

体现 AOS（Agent Operating System）定位，而不是聊天机器人。

---

# 11. 后续演进方向

审查建议中标注为「后续再做」的能力，待 MVP 验证后逐步建设：

| 优先级 | 能力 | 说明 |
|--------|------|------|
| P0（MVP） | Agent Runtime、Profile Engine、Event Bus | 已纳入本文档 |
| P1 | Capability Registry | Capability 注册与发现 |
| P2 | Memory → Cognition 重构 | 目录拆分，职责分离 |
| P3 | Telemetry & Observability | 全链路追踪 |
| P4 | Agent Marketplace | 第三方 Agent/Capability 接入 |
