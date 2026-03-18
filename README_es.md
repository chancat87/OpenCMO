<div align="center">
  <img src="assets/logo.png" alt="OpenCMO Logo" width="200" />
</div>

<h1 align="center">OpenCMO</h1>

<div align="center">
  <strong>Tu Director de Marketing con IA — creado para desarrolladores independientes que prefieren programar antes que hacer marketing.</strong>
</div>
<br/>

<div align="center">
  <a href="README.md">🇺🇸 English</a> | <a href="README_zh.md">🇨🇳 中文</a> | <a href="README_ja.md">🇯🇵 日本語</a> | <a href="README_ko.md">🇰🇷 한국어</a> | 🇪🇸 Español
</div>

<div align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/your-username/OpenCMO/stargazers"><img src="https://img.shields.io/github/stars/your-username/OpenCMO?style=flat-square&color=yellow" alt="Stars"></a>
</div>

---

## 🌟 ¿Qué es OpenCMO?

OpenCMO es un sistema multiagente de código abierto que actúa como tu **equipo de marketing con IA**. Dale la URL de tu producto y rastreará tu sitio, extraerá los puntos de venta clave y generará contenido de marketing específico para cada plataforma — todo a través de una simple y elegante interfaz de línea de comandos.

Creado específicamente para **desarrolladores independientes, fundadores en solitario y equipos pequeños** que tienen un gran producto pero no tienen tiempo (ni ganas) de escribir textos de marketing para cada plataforma.

## ✨ Características

- **🐦 Experto en Twitter/X** — Genera variantes de tweets e hilos con ganchos que detienen el scroll.
- **🤖 Experto en Reddit** — Crea publicaciones auténticas e impulsadas por historias adaptadas para r/SideProject y comunidades de nicho.
- **💼 Experto en LinkedIn** — Escribe publicaciones profesionales basadas en datos que no suenan a jerga corporativa.
- **🚀 Experto en Product Hunt** — Crea eslóganes llamativos, descripciones y el importantísimo primer comentario del creador (Maker's comment).
- **📰 Experto en Hacker News** — Produce publicaciones discretas y técnicamente enfocadas de tipo "Show HN".
- **📝 Experto en Blog/SEO** — Elabora esquemas de artículos optimizados para SEO para Medium y Dev.to.

## 🏗️ Arquitectura

```mermaid
graph TD
    User([Usuario]) --> CMO[Agente CMO <br/> Orquestador]
    CMO -- rastrea sitio del producto --> Crawl[Herramienta Crawl <br/> crawl_website]
    
    CMO -- transferencia --> X[Experto en Twitter/X]
    CMO -- transferencia --> Reddit[Experto en Reddit]
    CMO -- transferencia --> LinkedIn[Experto en LinkedIn]
    CMO -- transferencia --> PH[Experto en Product Hunt]
    CMO -- transferencia --> HN[Experto en Hacker News]
    CMO -- transferencia --> Blog[Experto en Blog/SEO]
```

El **Agente CMO** rastrea tu sitio web, extrae una descripción breve, los puntos de venta principales y un perfil de audiencia objetivo. Luego delega de manera inteligente al experto de la plataforma adecuada según tu solicitud.

## 🚀 Inicio Rápido

### 1. Instalar

```bash
pip install -e .
crawl4ai-setup
```

### 2. Configurar

```bash
cp .env.example .env
# Edita .env y agrega tu clave de API de OpenAI
```

### 3. Ejecutar

```bash
opencmo
```

## 💻 Ejemplo de Sesión

```text
============================================================
  🎯 OpenCMO - Tu Director de Marketing con IA
  Escribe la URL de un producto y lo que necesitas, o 'quit' para salir.
============================================================

Tú: Help me write a tweet for https://crawl4ai.com/

El CMO está trabajando... ⚙️

[Experto en Twitter/X] 🐦
Aquí tienes 3 variantes de tweet para Crawl4AI:

1. "Tired of writing web scrapers from scratch?
   Crawl4AI gives you LLM-ready markdown from any URL in one line of Python.
   Open source. Blazing fast. #OpenSource #AI"

2. ...

Tú: Make it more casual and fun

El CMO está trabajando... ⚙️

[Experto en Twitter/X] 🐦
¡Claro! Aquí tienes una versión más informal:
...

Tú: Now write me a Product Hunt launch post

El CMO está trabajando... ⚙️

[Experto en Product Hunt] 🚀
...

Tú: quit
¡Hasta luego! 👋
```

## 🗺️ Hoja de Ruta

- [ ] 🌐 Interfaz web con transmisión en tiempo real
- [ ] ⚡ Modo multicanal: generar contenido para las 6 plataformas con un solo comando
- [ ] 🔗 Publicación automática en plataformas mediante integraciones de API
- [ ] 📅 Calendario de contenido y programación
- [ ] 🧪 Sugerencias de pruebas A/B
- [ ] 🎬 Más expertos de plataforma (YouTube, Instagram, TikTok, etc.)
- [ ] 🎭 Entrenamiento personalizado de voz de marca

## 🤝 Contribuir

¡Las contribuciones siempre son bienvenidas! Así es como puedes ayudar:

1. **Haz un fork** del repositorio
2. **Crea** una rama de funcionalidad (`git checkout -b feature/funcionalidad-increible`)
3. **Haz commit** de tus cambios (`git commit -m 'Agregar funcionalidad increíble'`)
4. **Sube** la rama (`git push origin feature/funcionalidad-increible`)
5. **Abre** un Pull Request

**Ideas para contribuir:**
- Nuevos agentes expertos de plataforma
- Mejoras en los prompts de los agentes existentes
- Interfaz web frontend
- Pruebas y documentación

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia Apache 2.0 — consulta el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">
  Si OpenCMO te resulta útil, ¡darle una <strong>Estrella ⭐</strong> significaría mucho para nosotros!
</div>
