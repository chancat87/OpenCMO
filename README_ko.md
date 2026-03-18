<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="200" />
</div>

<h1 align="center">OpenCMO</h1>

<div align="center">
  <strong>당신의 AI 최고 마케팅 책임자(CMO) — 마케팅보다 제품 개발에 집중하고 싶은 인디 개발자를 위해 만들어졌습니다.</strong>
</div>
<br/>

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README_zh.md">🇨🇳 中文</a> | <a href="README_ja.md">🇯🇵 日本語</a> | 🇰🇷 한국어 | <a href="README_es.md">🇪🇸 Español</a>
</div>

<div align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/your-username/OpenCMO/stargazers"><img src="https://img.shields.io/github/stars/your-username/OpenCMO?style=flat-square&color=yellow" alt="Stars"></a>
</div>

---

## 🌟 OpenCMO란?

OpenCMO는 **AI 마케팅 팀** 역할을 하는 오픈소스 멀티 에이전트 시스템입니다. 제품 URL을 입력하면 웹사이트를 크롤링하고, 핵심 셀링 포인트를 추출하며, 플랫폼별 맞춤 마케팅 콘텐츠를 생성합니다 — 간단하고 우아한 CLI 하나로 모든 것을 처리합니다.

훌륭한 제품을 가지고 있지만 모든 소셜 채널에 맞는 마케팅 문구를 작성할 시간이 (혹은 의지가) 없는 **인디 개발자, 1인 창업자, 소규모 팀**을 위해 특별히 만들어졌습니다.

## ✨ 주요 기능

- **🐦 Twitter/X 전문가** — 스크롤을 멈추게 하는 후킹 문구와 함께 다양한 트윗 변형 및 스레드를 생성합니다.
- **🤖 Reddit 전문가** — r/SideProject 및 니치 커뮤니티에 적합한 진정성 있는 스토리 기반 게시글을 작성합니다.
- **💼 LinkedIn 전문가** — 딱딱한 기업체 느낌 없이 전문적이고 데이터 중심의 게시글을 작성합니다.
- **🚀 Product Hunt 전문가** — 톡톡 튀는 태그라인, 설명문, 그리고 가장 중요한 메이커의 첫 번째 댓글(Maker's comment)을 생성합니다.
- **📰 Hacker News 전문가** — 절제되고 기술 중심적인 "Show HN" 게시글을 작성합니다.
- **📝 블로그/SEO 전문가** — Medium 및 Dev.to용 SEO 친화적인 글 개요를 작성합니다.

## 🏗️ 아키텍처

```mermaid
graph TD
    User([사용자]) --> CMO[CMO 에이전트 <br/> 오케스트레이터]
    CMO -- 제품 웹사이트 크롤링 --> Crawl[크롤링 도구 <br/> crawl_website]
    
    CMO -- 핸드오프 --> X[Twitter/X 전문가]
    CMO -- 핸드오프 --> Reddit[Reddit 전문가]
    CMO -- 핸드오프 --> LinkedIn[LinkedIn 전문가]
    CMO -- 핸드오프 --> PH[Product Hunt 전문가]
    CMO -- 핸드오프 --> HN[Hacker News 전문가]
    CMO -- 핸드오프 --> Blog[블로그/SEO 전문가]
```

**CMO 에이전트**가 웹사이트를 크롤링하여 한 줄 소개, 핵심 셀링 포인트, 타겟 고객 프로필을 추출합니다. 그 후 사용자의 요청에 따라 가장 적합한 플랫폼 전문가에게 작업을 지능적으로 전달합니다.

## 🚀 빠른 시작

### 1. 설치

```bash
pip install -e .
crawl4ai-setup
```

### 2. 설정

```bash
cp .env.example .env
# .env 파일을 열어 OpenAI API 키를 추가하세요
```

### 3. 실행

```bash
opencmo
```

## 💻 사용 예시

```text
============================================================
  🎯 OpenCMO - Your AI Chief 마케팅 책임자
  Type a product URL and what you need, or 'quit' to exit.
============================================================

You: Help me write a tweet for https://crawl4ai.com/

CMO is working... ⚙️

[Twitter/X Expert] 🐦
Here are 3 tweet variants for Crawl4AI:

1. "Tired of writing web scrapers from scratch?
   Crawl4AI gives you LLM-ready markdown from any URL in one line of Python.
   Open source. Blazing fast. #OpenSource #AI"

2. ...

You: Make it more casual and fun

CMO is working... ⚙️

[Twitter/X Expert] 🐦
Sure! Here's a more casual take:
...

You: Now write me a Product Hunt launch post

CMO is working... ⚙️

[Product Hunt Expert] 🚀
...

You: quit
Goodbye! 👋
```

## 🗺️ 로드맵

- [ ] 🌐 실시간 스트리밍을 지원하는 웹 UI
- [ ] ⚡ 전체 채널 모드: 하나의 명령으로 6개 플랫폼 콘텐츠 일괄 생성
- [ ] 🔗 API 연동을 통한 플랫폼 자동 게시
- [ ] 📅 콘텐츠 캘린더 및 일정 관리
- [ ] 🧪 A/B 테스트 제안
- [ ] 🎬 더 많은 플랫폼 전문가 추가 (YouTube, Instagram, TikTok 등)
- [ ] 🎭 맞춤형 브랜드 보이스 학습

## 🤝 기여하기

기여는 언제나 환영합니다! 다음과 같이 참여할 수 있습니다:

1. 저장소를 **포크**합니다.
2. 기능 브랜치를 **생성**합니다 (`git checkout -b feature/amazing-feature`)
3. 변경 사항을 **커밋**합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 **푸시**합니다 (`git push origin feature/amazing-feature`)
5. **Pull Request**를 생성합니다.

**기여 아이디어:**
- 새로운 플랫폼 전문가 에이전트 개발
- 기존 에이전트의 프롬프트 개선 및 최적화
- 웹 UI 프론트엔드 제작
- 테스트 추가 및 문서화

## 📄 라이선스

이 프로젝트는 Apache License 2.0에 따라 라이선스가 부여됩니다 — 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

<div align="center">
  OpenCMO가 도움이 되셨다면 <strong>별(Star) ⭐</strong>을 눌러주세요. 저희에게 큰 힘이 됩니다!
</div>
