<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="120" />
</div>

<h1 align="center">OpenCMO</h1>

<p align="center">
  <strong>오픈소스 AI CMO — 하나의 도구로 전체 마케팅 팀을 대체합니다.</strong><br/>
  <sub>10개의 AI 전문가 에이전트, 실시간 모니터링, 모던 웹 대시보드.</sub>
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

## 🖼️ 갤러리 및 인터페이스

현대적인 멀티 에이전트 마케팅 워크플로우를 위해 디자인된 아름다운 다크 테마 React SPA 대시보드를 탐색해 보세요.

<details open>
<summary><b>스크린샷 보기</b></summary>
<br>

<div align="center">
  <img src="assets/screenshots/dashboard-full.png" alt="OpenCMO 대시보드" width="800" />
  <br/><sub><b>메인 대시보드</b>: SEO, GEO AI 가시성 및 커뮤니티 지표 전반에 걸친 실시간 프로젝트 추적.</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/chat-interface.png" alt="채팅 인터페이스" width="800" />
  <br/><sub><b>전문가 채팅 인터페이스</b>: 10명의 AI 마케팅 전문가와 채팅하세요. 특정 에이전트를 선택하거나 CMO가 자동으로 라우팅하도록 합니다.</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/monitors-panel.png" alt="모니터 목록" width="800" />
  <br/><sub><b>모니터 및 멀티 에이전트 분석</b>: 3명의 AI 역할이 전략을 실시간으로 토론하여 최상의 키워드를 추출하는 것을 지켜보세요.</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/multi-agent-discussion.png" alt="멀티 에이전트 토론" width="800" />
  <br/><sub><b>멀티 에이전트 토론</b>: AI 역할들이 대화형 다이얼로그에서 제품 전략에 대해 토론하는 모습을 확인하세요.</sub>
</div>
<br/>

<div align="center">
  <img src="assets/screenshots/settings-panel.png" alt="설정 및 API UI" width="800" />
  <br/><sub><b>설정</b>: 깨끗하고 안전한 UI에서 API 제공업체 (OpenAI, DeepSeek, Ollama 등)를 쉽게 구성합니다.</sub>
</div>

</details>

---

## OpenCMO란?

인디 개발자와 소규모 팀을 위한 **멀티 에이전트 AI 마케팅 시스템**입니다. URL을 입력하면 사이트를 크롤링하고, 멀티 에이전트 전략 토론을 실행하며, SEO·AI 가시성·커뮤니티 모니터링을 자동 설정합니다.

## 🚀 빠른 시작

### 1. 설치

```bash
git clone https://github.com/study8677/OpenCMO.git
cd OpenCMO

# pip를 통해 종속성 설치
pip install -e ".[all]"

# 크롤러 구성 요소 초기화
crawl4ai-setup
```

### 2. 구성

```bash
cp .env.example .env

# .env 파일을 수정하고 API 키를 입력하세요:
# OPENAI_API_KEY=sk-... 
```
*(OpenAI, DeepSeek, NIM, Ollama 등을 지원합니다. 자세한 내용은 `.env.example`을 참조하세요)*

### 3. 애플리케이션 실행

모던 웹 대시보드를 시작하여 UI에 액세스합니다:

```bash
opencmo-web
```
🚀 **웹 브라우저에서 [http://localhost:8080/app](http://localhost:8080/app)을 엽니다.**

<details>
<summary><b>CLI 모드 (선택 사항)</b></summary>

또는 대화형 터미널 인터페이스를 실행할 수 있습니다:
```bash
opencmo
```
</details>

### 4. 사용 방법

1. **Monitors**로 이동합니다 → URL을 붙여넣습니다 → **Start Monitoring**을 클릭합니다
2. AI 멀티 에이전트 토론이 실시간으로 제품을 분석하는 것을 시청합니다
3. 시스템이 브랜드 이름, 카테고리 및 키워드를 자동 추출합니다
4. 전체 스캔이 자동으로 실행됩니다 (SEO + GEO + 커뮤니티)
5. **Dashboard**에서 결과 확인하기

## 🤖 10개의 AI 전문가

| 에이전트 | 기능 |
|---------|------|
| **CMO Agent** | 전체 조율, 적절한 전문가에게 자동 라우팅 |
| **Twitter/X** | 트윗, 스레드 |
| **Reddit** | 진정성 있는 게시글 + 기존 토론에 대한 스마트 답글 |
| **LinkedIn** | 전문 콘텐츠 |
| **Product Hunt** | 런칭 카피 |
| **Hacker News** | Show HN 게시글 |
| **Blog/SEO** | SEO 최적화 글 |
| **SEO 감사** | Core Web Vitals, Schema.org 분석 |
| **GEO** | AI 검색엔진 브랜드 언급 체크 |
| **커뮤니티** | Reddit/HN/Dev.to 토론 스캔 |

### 🔗 Reddit 통합 (새 기능)

- **스마트 발견** — 제품 카테고리와 관련성이 높은 Reddit 게시물을 스캔
- **AI 기반 답글** — 각 토론에 맞춘 자연스럽고 비홍보적인 답글 생성
- **휴먼 인 더 루프** — 게시 전 AI가 작성한 답글을 미리보기, 편집 및 확인
- **자격 증명 관리** — 설정 대화 상자에서 Reddit API 키를 직접 구성
- **자동 게시 토글** — 원클릭으로 자동 게시 켜기/끄기

### 🕸️ 지식 그래프 (새 기능)

- **인터랙티브 포스 그래프** — 브랜드, 키워드, 토론, SERP 순위, 경쟁사 간의 관계를 드래그, 줌, 탐색할 수 있는 동적 포스 다이렉티드 시각화
- **실시간 업데이트** — 새로운 스캔 데이터가 도착할 때마다 30초마다 자동 갱신
- **6가지 노드 유형** — 브랜드(보라), 키워드(시안), 토론(앰버), SERP 순위(초록), 경쟁사(빨강), 경쟁사 키워드(주황)
- **키워드 중복 감지** — 브랜드와 경쟁사가 공유하는 키워드를 빨간 점선으로 자동 강조
- **경쟁사 관리** — 경쟁사의 URL과 키워드를 추가하면 그래프가 즉시 업데이트
- **호버 상세 정보** — 노드에 호버하면 상세 정보 (참여도 점수, 순위, 플랫폼 등) 표시

## 라이선스

Apache License 2.0

---

<div align="center">
  <sub>OpenCMO가 도움이 되셨다면 ⭐ 부탁드립니다!</sub>
</div>
