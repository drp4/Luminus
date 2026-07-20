---
version: "alpha"
name: "Children Growth OS"
description: "一个陪伴孩子成长十年的 AI Growth Companion — 视觉设计系统"
colors:
  primary: "#FF9500"
  primaryLight: "#FFB84D"
  primaryDark: "#CC7700"
  secondary: "#34C759"
  secondaryLight: "#6BD98A"
  secondaryDark: "#248A3D"
  accent: "#007AFF"
  accentLight: "#4DA3FF"
  background: "#FFF8F0"
  surface: "#FFFFFF"
  surfaceWarm: "#FFF5E6"
  textPrimary: "#2C1810"
  textSecondary: "#8B7355"
  textOnPrimary: "#FFFFFF"
  success: "#34C759"
  warning: "#FF9500"
  error: "#FF3B30"
  sky: "#87CEEB"
  ocean: "#2196F3"
  forest: "#4CAF50"
  space: "#9C27B0"
  sunshine: "#FFD60A"
  dino: "#8BC34A"
  pink: "#E91E63"
  lavender: "#C9A0DC"
typography:
  display:
    fontFamily: "'Bubblegum Sans', 'Noto Sans SC', cursive"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.2
    description: "页面标题，童趣大字体"
  heading:
    fontFamily: "'Nunito', 'Noto Sans SC', sans-serif"
    fontSize: "22px"
    fontWeight: 700
    lineHeight: 1.3
    description: "卡片标题、章节标题"
  body:
    fontFamily: "'Nunito', 'Noto Sans SC', sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
    description: "正文、聊天内容"
  bodyLarge:
    fontFamily: "'Nunito', 'Noto Sans SC', sans-serif"
    fontSize: "18px"
    fontWeight: 500
    lineHeight: 1.5
    description: "故事正文、强调文本"
  caption:
    fontFamily: "'Nunito', 'Noto Sans SC', sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
    description: "辅助文字、时间戳"
  button:
    fontFamily: "'Nunito', 'Noto Sans SC', sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.2
    description: "按钮文字"
rounded:
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "48px"
components:
  chat-bubble-child:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.textPrimary}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.md}"
    marginBottom: "{spacing.sm}"
    maxWidth: "80%"
    alignSelf: "flex-start"
  chat-bubble-ai:
    backgroundColor: "{colors.primaryLight}"
    textColor: "{colors.textOnPrimary}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.md}"
    marginBottom: "{spacing.sm}"
    maxWidth: "80%"
    alignSelf: "flex-end"
  chat-input:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.primaryLight}"
    borderRadius: "{rounded.xl}"
    padding: "{spacing.md}"
    fontSize: "16px"
    minHeight: "52px"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.textOnPrimary}"
    borderRadius: "{rounded.full}"
    paddingHorizontal: "{spacing.xl}"
    paddingVertical: "{spacing.md}"
    fontSize: "18px"
    fontWeight: 700
    minHeight: "56px"
    shadow: "0 2px 8px rgba(255,149,0,0.3)"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.primary}"
    borderColor: "{colors.primary}"
    borderRadius: "{rounded.full}"
    paddingHorizontal: "{spacing.xl}"
    paddingVertical: "{spacing.md}"
    borderWidth: "2px"
  button-primary-hover:
    backgroundColor: "{colors.primaryDark}"
    shadow: "0 4px 12px rgba(255,149,0,0.4)"
    transform: "scale(1.05)"
  garden-plant-card:
    backgroundColor: "{colors.surface}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.lg}"
    shadow: "0 2px 12px rgba(0,0,0,0.08)"
    minWidth: "140px"
    minHeight: "180px"
  garden-plant-seed:
    icon: "🌱"
    size: "32px"
    opacity: 0.4
  garden-plant-sprout:
    icon: "🌿"
    size: "48px"
    opacity: 0.6
  garden-plant-growing:
    icon: "🪴"
    size: "64px"
    opacity: 0.8
  garden-plant-blooming:
    icon: "🌸"
    size: "80px"
    opacity: 1.0
  story-card:
    backgroundColor: "{colors.surface}"
    borderRadius: "{rounded.lg}"
    padding: "{spacing.lg}"
    shadow: "0 2px 12px rgba(0,0,0,0.08)"
    minHeight: "160px"
  story-choice-button:
    backgroundColor: "{colors.surfaceWarm}"
    textColor: "{colors.textPrimary}"
    borderRadius: "{rounded.md}"
    padding: "{spacing.md}"
    borderColor: "{colors.primaryLight}"
    borderWidth: "1px"
  story-choice-button-hover:
    backgroundColor: "{colors.primaryLight}"
    textColor: "{colors.textOnPrimary}"
    borderColor: "{colors.primary}"
  nav-bar:
    backgroundColor: "{colors.surface}"
    height: "72px"
    iconSize: "28px"
    labelSize: "12px"
    activeColor: "{colors.primary}"
    inactiveColor: "{colors.textSecondary}"
---

# Children Growth OS — Visual Identity

## 1. Overview

**品牌定位**: 温暖的 AI 伙伴，不是冷冰冰的工具。

**设计哲学**: 
- 像一本精美的绘本，不像一个 App
- 颜色是拥抱，不是指令
- 每个元素都让孩子想摸一摸、点一点
- 8-11 岁孩子的手指大小 = 按钮必须够大

**情感调性**: 好奇、温暖、鼓励、有趣、安全。

---

## 2. Colors

### Primary — 活力橙 `#FF9500`
温暖、充满能量，像阳光一样。主按钮、选中状态、强调元素使用。不当严肃的教育工具，而是一个活生生的伙伴。

### Secondary — 成长绿 `#34C759`  
代表成长、生命力。Profile 花园的植物、分数指示器、成功状态使用。

### Background — 暖米白 `#FFF8F0`
不是纯白 — 纯白像试卷。温暖的米白色像绘本纸张，让孩子感到安全放松。

### Surface — 纯白 `#FFFFFF`
卡片、气泡底色。在暖色背景上提供清晰的对比。

### Text — 暖棕 `#2C1810`
不是纯黑。暖棕色更柔和，阅读长文本不累。

### 主题色板
孩子感兴趣的每个主题都有专属颜色 — 恐龙绿、海洋蓝、太空紫、阳光黄。

---

## 3. Typography

### 字体选择
- **英文**: Bubblegum Sans (标题) + Nunito (正文) — 圆润友好
- **中文**: Noto Sans SC — 清晰易读

### 字号层级
所有字号比普通 App 大 2-4px — 孩子的眼睛还在发育。

| Token | Size | 用途 |
|--------|------|------|
| display | 32px | 页面大标题 |
| heading | 22px | 卡片标题 |
| bodyLarge | 18px | 故事正文 |
| body | 16px | 聊天内容 |
| button | 18px | 按钮文字 |
| caption | 13px | 辅助信息 |

### 行高
正文行高 1.6 — 留白更多，降低阅读压力。

---

## 4. Layout & Spacing

### 间距系统
基于 4px 基准，提供充裕的呼吸空间。

### 触控目标
所有可交互元素的最小高度 **56px**（Material 标准 48px + 8px 儿童加成）。

### 最大宽度
聊天内容最大宽度 80% — 窄列阅读更舒适。

---

## 5. Elevation & Depth

阴影柔和。不是 Google Material 的硬阴影，而是**柔光**效果：

- 卡片: `shadow: 0 2px 12px rgba(0,0,0,0.08)` — 轻微浮起
- 主按钮: `shadow: 0 2px 8px rgba(255,149,0,0.3)` — 橙色光晕，吸引点击
- 悬停: 按钮放大 5%，阴影加深 — 给孩子一个明确的"可以点我"信号

---

## 6. Shapes

**圆角系统**:

| Token | Value | 用途 |
|-------|-------|------|
| sm | 8px | 标签、小卡片 |
| md | 16px | 卡片、选项按钮 |
| lg | 24px | 气泡、面板 |
| xl | 32px | 输入框、大卡片 |
| full | 9999px | 主按钮（胶囊形） |

圆角让界面"柔软"而不是"锋利"。

---

## 7. Components

### Chat Bubble
- 孩子消息: 白色气泡，圆角大，左对齐
- AI 伙伴消息: 浅橙色气泡，右对齐，像朋友发来的消息
- 非传统的对话列表，而是更像 **Messenger/微信** 的感觉

### Button
- 主按钮: 胶囊形，橙色，大阴影，点击时放大
- 次要按钮: 橙色描边，白色填充
- 每个按钮都是"邀请"而不是"指令"

### 成长花园植物
- 4 个成长阶段: 🌱 seed → 🌿 sprout → 🪴 growing → 🌸 blooming
- 每个阶段: 更大的图标、更高的透明度
- 点击植物展示"知识卡片"（学到了什么）

### Story Card
- 大卡片，封面图区域（以后放 AI 生成的插图）
- 显示标题、章节数、进度
- 点击进入故事播放

### Navigation Bar
- 72px 高度（比标准 56px 更高）
- 大图标 (28px) + 文字标签
- 3 个 Tab: 🏠 探索 | 📖 故事 | 🌱 花园

---

## 8. Do's and Don'ts

### Do
- ✅ 用温暖的橙/绿/米色
- ✅ 按钮够大 (≥56px)
- ✅ 圆角让界面柔软
- ✅ 卡片用柔阴影，有绘本感
- ✅ 文字留白充裕 (line-height ≥ 1.5)
- ✅ 点击有反馈（放大 + 音效）
- ✅ 加载时显示有趣的动画，不是转圈

### Don't
- ❌ 不用纯黑文字（用暖棕）
- ❌ 不用纯白背景（用暖米白）
- ❌ 不用小按钮 (<48px)
- ❌ 不用直角边框
- ❌ 不用密集排列的信息
- ❌ 不用红色表示"错误"（用橙色温和提示）
- ❌ 不出现"你错了"的视觉暗示
