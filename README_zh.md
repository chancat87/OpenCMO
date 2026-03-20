<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>开源 AI CMO —— 一个工具就是你的整个营销团队。</strong><br/>
  <sub>10 个 AI 专家智能体、实时监控、现代化 Web 仪表盘。</sub>
</p>

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README_zh.md">🇨🇳 中文</a> | <a href="README_ja.md">🇯🇵 日本語</a> | <a href="README_ko.md">🇰🇷 한국어</a> | <a href="README_es.md">🇪🇸 Español</a>
</div>

<div align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/study8677/OpenCMO/stargazers"><img src="https://img.shields.io/github/stars/study8677/OpenCMO?style=flat-square&color=yellow" alt="Stars"></a>
</div>

---

## 🖼️ 界面图集

探索为现代化多智能体营销工作流设计的暗黑风格 React SPA 仪表盘。

<details open>
<summary><b>查看运行截图</b></summary>
<br>

<div align="center">
  <img src="assets/screenshots/dashboard-full.png" alt="OpenCMO 仪表盘" width="800" />
  <br/><sub><b>主仪表盘</b>：实时掌控项目状态，跨越 SEO、GEO AI 可见度与社区互动指标。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/chat-interface.png" alt="智能体对话界面" width="800" />
  <br/><sub><b>专家对话界面</b>：与 10 位 AI 营销专家畅聊。可选定一位专家，或让 CMO 自动为您路由。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/monitors-panel.png" alt="监控列表" width="800" />
  <br/><sub><b>监控与多智能体分析</b>：实时观看 3 位 AI 角色深入探讨策略，为您提取最佳关键词。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/multi-agent-discussion.png" alt="多智能体讨论" width="800" />
  <br/><sub><b>多智能体交互讨论</b>：实时查看不同 AI 角色在互动弹窗中针对产品策略进行辩论的过程。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/settings-panel.png" alt="设置与 API 界面" width="800" />
  <br/><sub><b>配置与设置</b>：提供简洁安全的界面以配置您的 API 供应商（OpenAI，DeepSeek，Ollama 等）。</sub>
</div>

</details>

---

## OpenCMO 是什么？

OpenCMO 是一个**多智能体 AI 营销系统**，专为独立开发者和小团队设计。输入一个 URL，系统会爬取网站、运行多智能体策略讨论，自动设置 SEO、AI 可见度和社区讨论的监控。

### 核心能力

- **10 个 AI 专家智能体** — Twitter/X、Reddit、LinkedIn、Product Hunt、Hacker News、博客/SEO、SEO 审计、GEO（AI 可见度）、社区监控、CMO 总管
- **智能 URL 分析** — 粘贴任意 URL，3 个 AI 角色（产品分析师、SEO 专家、社区运营）进行 3 轮讨论，提取品牌名、分类和监控关键词
- **知识图谱** — 交互式力导向图，可视化品牌、关键词、竞品、社区讨论和搜索排名之间的关系网络
- **实时 Web 仪表盘** — React SPA，暗色侧边栏、项目卡片、趋势图表、中英双语
- **与专家对话** — ChatGPT 风格界面，支持历史记录；选择特定智能体或让 CMO 自动路由
- **持续监控** — 基于 Cron 的定时扫描 SEO、GEO 和社区指标
- **任意 LLM 供应商** — OpenAI、NVIDIA NIM、DeepSeek、Ollama 或任何 OpenAI 兼容 API

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO

# 通过 pip 安装依赖
pip install -e ".[all]"

# 初始化爬虫组件
crawl4ai-setup
```

### 2. 配置

```bash
cp .env.example .env

# 编辑 .env 文件并填入您的 API Key：
# OPENAI_API_KEY=sk-... 
```
*(支持 OpenAI, DeepSeek, NIM, Ollama 等，详情见 `.env.example`)*

### 3. 运行应用程序

启动现代化 Web 仪表盘以访问 UI 界面：

```bash
opencmo-web
```
🚀 **在您的浏览器中打开 [http://localhost:8080/app](http://localhost:8080/app)。**

<details>
<summary><b>命令行模式 (可选)</b></summary>

或者，运行命令行交互界面：
```bash
opencmo
```
</details>

### 4. 如何使用

1. 进入 **监控 (Monitors)** → 粘贴您的 URL → 点击 **开始监控 (Start Monitoring)**
2. 实时观看 AI 多智能体讨论分析您的产品
3. 系统自动提取品牌名、分类和关键词
4. 自动运行全面扫描（SEO + GEO + 社区）
5. 在 **仪表盘 (Dashboard)** 点击对应项目查看结果

## 🤖 10 个 AI 专家智能体

| 智能体 | 功能 |
|--------|------|
| **CMO 总管** | 总体协调，自动路由到合适的专家 |
| **Twitter/X** | 推文、话题串和互动策略 |
| **Reddit** | 真实风格的帖子 + 智能回复现有讨论 |
| **LinkedIn** | 专业的行业领导力内容 |
| **Product Hunt** | 上线文案、标语和制作者评论 |
| **Hacker News** | 技术向的 Show HN 帖子 |
| **博客/SEO** | SEO 优化长文（2000+ 字） |
| **SEO 审计** | 核心 Web 指标、Schema.org、robots/sitemap |
| **GEO** | Perplexity、You.com、ChatGPT、Claude、Gemini 品牌提及 |
| **社区监控** | Reddit、HN、Dev.to 讨论扫描 |

### 🔗 Reddit 集成 (新功能)

- **智能发现** — 扫描 Reddit 上与你的产品品类高度相关的帖子
- **AI 驱动回复** — 为每条讨论生成真实、非推销性的回复
- **人工审核** — 发布前预览 AI 起草的回复；在界面上编辑确认
- **凭证管理** — 直接在设置对话框中配置 Reddit API 密钥
- **自动发布开关** — 一键开启/关闭自动发布

## 🎯 智能 URL 分析

| 轮次 | 内容 |
|------|------|
| **第一轮** | 各角色初步分析（产品定位、SEO 关键词、社区话题） |
| **第二轮** | 基于其他角色的分析完善建议 |
| **第三轮** | 策略总监汇总 → 品牌名 + 分类 + 5-8 个关键词 |

### 🕸️ 知识图谱 (新功能)

- **交互式力导向图** — 在动态力导向可视化中拖拽、缩放、探索品牌、关键词、讨论、搜索排名和竞品之间的关系
- **实时更新** — 图谱每 30 秒自动刷新，随着新扫描数据的到来即时更新
- **6 种节点类型** — 品牌（紫色）、关键词（青色）、社区讨论（琥珀色）、搜索排名（绿色）、竞品（红色）、竞品关键词（橙色）
- **关键词重叠检测** — 自动用红色虚线高亮你和竞品共享的关键词
- **竞品管理** — 添加竞品及其网址和关键词，图谱即时更新以展示竞争关系
- **悬浮详情** — 悬停任意节点查看详细信息（互动分、排名、平台等）

## 🔧 灵活配置

支持 OpenAI、NVIDIA NIM、DeepSeek、Ollama 等任意 OpenAI 兼容 API。详见 `.env.example`。

## 许可证

Apache License 2.0

---

<div align="center">
  <sub>如果 OpenCMO 对你有帮助，给个 ⭐ 吧！</sub>
</div>
