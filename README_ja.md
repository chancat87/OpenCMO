<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>オープンソース AI CMO — ひとつのツールでマーケティングチーム全体をカバー。</strong><br/>
  <sub>10のAIエキスパートエージェント、リアルタイム監視、モダンなWebダッシュボード。</sub>
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

## 🖼️ ギャラリーとインターフェース

モダンなマルチエージェントマーケティングワークフロー向けにデザインされた、美しいダークテーマのReact SPAダッシュボードをご覧ください。

<details open>
<summary><b>スクリーンショットを表示</b></summary>
<br>

<div align="center">
  <img src="assets/screenshots/dashboard-full.png" alt="OpenCMO ダッシュボード" width="800" />
  <br/><sub><b>メインダッシュボード</b>：SEO、GEO AI可視性、コミュニティ指標全体にわたるリアルタイムのプロジェクト追跡。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/chat-interface.png" alt="チャットインターフェース" width="800" />
  <br/><sub><b>エキスパートチャット</b>：10人のAIマーケティング専門家とチャット。エージェントを選択するか、CMOに自動ルーティングをお任せください。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/monitors-panel.png" alt="モニターリスト" width="800" />
  <br/><sub><b>モニターとマルチエージェント分析</b>：最適なキーワードを抽出するために、3人のAIキャラが戦略をリアルタイムで議論している様子を観察します。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/multi-agent-discussion.png" alt="マルチエージェントディスカッション" width="800" />
  <br/><sub><b>マルチエージェントディスカッション</b>：AIキャラクターたちがインタラクティブなダイアログの中で製品戦略を議論する様子をご覧ください。</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/settings-panel.png" alt="設定とAPIインターフェース" width="800" />
  <br/><sub><b>設定</b>：クリーンなUIでAPIプロバイダー（OpenAI、DeepSeek、Ollamaなど）を安全に設定します。</sub>
</div>

</details>

---

## OpenCMOとは？

インディー開発者や小規模チーム向けの**マルチエージェントAIマーケティングシステム**です。URLを入力するだけで、サイトをクロールし、マルチエージェント戦略議論を実行し、SEO・AI可視性・コミュニティの監視を自動設定します。

## 🚀 クイックスタート

### 1. インストール

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO

# pipによる依存関係のインストール
pip install -e ".[all]"

# クローラー要素の初期化
crawl4ai-setup
```

### 2. 設定

```bash
cp .env.example .env

# .envを編集してAPIキーを入力します：
# OPENAI_API_KEY=sk-... 
```
*(OpenAI, DeepSeek, NIM, Ollama などに対応しています。詳しくは `.env.example` を参照してください)*

### 3. アプリケーションの実行

モダンなWebダッシュボードを起動してUIにアクセスします：

```bash
opencmo-web
```
🚀 **Webブラウザで [http://localhost:8080/app](http://localhost:8080/app) を開きます。**

<details>
<summary><b>CLIモード (オプション)</b></summary>

または、インタラクティブなターミナルインターフェースを実行します：
```bash
opencmo
```
</details>

### 4. 使い方

1. **Monitors** に移動します → URLを貼り付けます → **Start Monitoring** をクリックします
2. AIマルチエージェントの議論がリアルタイムで製品を分析するのを見守ります
3. システムはブランド名、カテゴリ、およびキーワードを自動抽出します
4. フル・スキャンが自動で実行されます（SEO + GEO + コミュニティ）
5. **Dashboard** で結果を確認します

## 🤖 10のAIエキスパート

| エージェント | 機能 |
|------------|------|
| **CMO Agent** | 全体統括、適切なエキスパートに自動ルーティング |
| **Twitter/X** | ツイート、スレッド |
| **Reddit** | 本格的な投稿 + 既存ディスカッションへのスマートリプライ |
| **LinkedIn** | プロフェッショナルコンテンツ |
| **Product Hunt** | ローンチコピー |
| **Hacker News** | Show HN投稿 |
| **Blog/SEO** | SEO最適化記事 |
| **SEO監査** | Core Web Vitals、Schema.org分析 |
| **GEO** | AI検索エンジンでのブランド言及チェック |
| **コミュニティ** | Reddit/HN/Dev.toの議論スキャン |

### 🔗 Reddit統合（新機能）

- **スマートディスカバリー** — 製品カテゴリに関連性の高いReddit投稿をスキャン
- **AIパワードリプライ** — 各ディスカッションに合わせた自然なリプライを生成
- **ヒューマン・イン・ザ・ループ** — 公開前にAIが作成したリプライをプレビュー・編集・確認
- **クレデンシャル管理** — 設定画面からReddit APIキーを直接設定
- **自動公開トグル** — ワンクリックで自動投稿のオン/オフ切り替え

### 🕸️ ナレッジグラフ（新機能）

- **インタラクティブフォースグラフ** — ブランド、キーワード、ディスカッション、SERP ランキング、競合他社の関係をドラッグ・ズーム・探索できるダイナミックな力指向グラフ
- **リアルタイム更新** — 新しいスキャンデータが到着するたび、30秒ごとに自動更新
- **6種類のノード** — ブランド（紫）、キーワード（シアン）、ディスカッション（アンバー）、SERP（緑）、競合（赤）、競合キーワード（オレンジ）
- **キーワード重複検出** — ブランドと競合が共有するキーワードを赤い破線で自動ハイライト
- **競合管理** — 競合のURL・キーワードを追加すると、グラフが即座に更新
- **ホバー詳細** — ノードにホバーすると詳細情報（エンゲージメントスコア、ランキング、プラットフォームなど）を表示

## ライセンス

Apache License 2.0

---

<div align="center">
  <sub>OpenCMOが役立ったら ⭐ をお願いします！</sub>
</div>
