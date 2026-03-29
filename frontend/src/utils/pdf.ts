import html2pdf from "html2pdf.js";

const LOGO_URL = "/logo.png";

/**
 * Convert a logo image URL to a base64 data-URI so it can be
 * embedded reliably in the off-screen PDF container.
 */
async function loadLogoAsDataURI(): Promise<string> {
  try {
    const resp = await fetch(LOGO_URL);
    const blob = await resp.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch {
    return "";
  }
}

/**
 * Inject print-optimised styles into the off-screen container.
 * These override the Tailwind prose defaults so headings, paragraphs,
 * lists and blockquotes render at comfortable reading sizes.
 */
function injectPrintStyles(container: HTMLDivElement) {
  const style = document.createElement("style");
  style.textContent = `
    /* ---- Base typography ---- */
    .pdf-body {
      font-family: 'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
      font-size: 15px;
      line-height: 1.85;
      color: #1e293b;
      word-break: break-word;
    }

    /* ---- Headings ---- */
    .pdf-body h1 {
      font-size: 26px;
      font-weight: 800;
      color: #0f172a;
      margin: 38px 0 16px;
      padding-bottom: 10px;
      border-bottom: 3px solid #6366f1;
      letter-spacing: -0.4px;
      line-height: 1.3;
    }
    .pdf-body h1:first-child {
      margin-top: 0;
    }

    .pdf-body h2 {
      font-size: 20px;
      font-weight: 700;
      color: #1e293b;
      margin: 32px 0 12px;
      padding-bottom: 8px;
      border-bottom: 1.5px solid #e2e8f0;
      line-height: 1.35;
    }

    .pdf-body h3 {
      font-size: 17px;
      font-weight: 700;
      color: #334155;
      margin: 24px 0 10px;
      line-height: 1.4;
    }

    .pdf-body h4 {
      font-size: 15px;
      font-weight: 700;
      color: #475569;
      margin: 20px 0 8px;
    }

    /* ---- Paragraphs ---- */
    .pdf-body p {
      margin: 0 0 14px;
      text-align: justify;
    }

    /* ---- Lists ---- */
    .pdf-body ul, .pdf-body ol {
      margin: 8px 0 16px;
      padding-left: 24px;
    }
    .pdf-body li {
      margin-bottom: 7px;
      line-height: 1.7;
    }
    .pdf-body li::marker {
      color: #6366f1;
      font-weight: 600;
    }

    /* ---- Blockquotes ---- */
    .pdf-body blockquote {
      margin: 16px 0;
      padding: 12px 18px;
      border-left: 4px solid #6366f1;
      background: #f8fafc;
      border-radius: 0 8px 8px 0;
      color: #334155;
      font-style: italic;
    }
    .pdf-body blockquote p {
      margin-bottom: 6px;
    }

    /* ---- Bold / Strong text ---- */
    .pdf-body strong {
      font-weight: 700;
      color: #0f172a;
    }

    /* ---- Code ---- */
    .pdf-body code {
      font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
      font-size: 13px;
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      color: #6366f1;
    }

    .pdf-body pre {
      background: #1e293b;
      color: #e2e8f0;
      padding: 16px;
      border-radius: 10px;
      overflow: auto;
      margin: 12px 0 18px;
      font-size: 13px;
      line-height: 1.6;
    }
    .pdf-body pre code {
      background: none;
      padding: 0;
      color: inherit;
    }

    /* ---- Tables ---- */
    .pdf-body table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      font-size: 14px;
    }
    .pdf-body th {
      background: #f1f5f9;
      font-weight: 700;
      text-align: left;
      padding: 10px 14px;
      border-bottom: 2px solid #cbd5e1;
      color: #334155;
    }
    .pdf-body td {
      padding: 9px 14px;
      border-bottom: 1px solid #e2e8f0;
      color: #475569;
    }

    /* ---- Horizontal rules ---- */
    .pdf-body hr {
      border: none;
      border-top: 1.5px solid #e2e8f0;
      margin: 28px 0;
    }

    /* ---- Page break hints (for html2pdf) ---- */
    .pdf-body h1, .pdf-body h2, .pdf-body h3 {
      page-break-after: avoid;
      break-after: avoid;
    }
    .pdf-body p, .pdf-body li {
      orphans: 3;
      widows: 3;
    }
  `;
  container.appendChild(style);
}

/**
 * Capture a specific DOM element and download it as a beautifully
 * formatted A4 PDF with the OpenCMO logo in the header and a
 * branded footer on every page.
 */
export async function downloadAsPDF({
  elementId,
  filename = "report.pdf",
  title = "AI CMO Report",
  subtitle,
}: {
  elementId: string;
  filename?: string;
  title?: string;
  subtitle?: string;
}) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`[pdf] Element #${elementId} not found.`);
    return;
  }

  const logoDataURI = await loadLogoAsDataURI();

  // ---- build the off-screen container ----
  const container = document.createElement("div");
  Object.assign(container.style, {
    position: "absolute",
    left: "-9999px",
    top: "-9999px",
    width: "750px",
    padding: "48px 44px 36px",
    background: "#ffffff",
  });

  // inject print-quality styles
  injectPrintStyles(container);

  // ---- branded header ----
  const header = document.createElement("div");
  Object.assign(header.style, {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    borderBottom: "3px solid #6366f1",
    paddingBottom: "20px",
    marginBottom: "36px",
  });

  if (logoDataURI) {
    const logo = document.createElement("img");
    logo.src = logoDataURI;
    Object.assign(logo.style, {
      width: "48px",
      height: "48px",
      borderRadius: "12px",
      objectFit: "contain",
    });
    header.appendChild(logo);
  }

  const headerText = document.createElement("div");
  headerText.style.flex = "1";
  headerText.innerHTML = [
    `<div style="font-size:24px;font-weight:800;color:#0f172a;letter-spacing:-0.4px;line-height:1.3">${title}</div>`,
    subtitle
      ? `<div style="margin-top:4px;font-size:13px;color:#64748b">${subtitle}</div>`
      : "",
    `<div style="margin-top:4px;font-size:12px;color:#94a3b8">Generated by OpenCMO · ${new Date().toLocaleDateString("zh-CN")}</div>`,
  ].join("\n");
  header.appendChild(headerText);
  container.appendChild(header);

  // ---- body content ----
  const body = document.createElement("div");
  body.className = "pdf-body";
  body.innerHTML = element.innerHTML;
  container.appendChild(body);

  // ---- footer ----
  const footer = document.createElement("div");
  Object.assign(footer.style, {
    borderTop: "1.5px solid #e2e8f0",
    marginTop: "44px",
    paddingTop: "16px",
    display: "flex",
    justifyContent: "space-between",
    fontSize: "11px",
    color: "#94a3b8",
    fontFamily: "'Helvetica Neue', Helvetica, Arial, 'PingFang SC', sans-serif",
  });
  footer.innerHTML = `
    <span>OpenCMO — AI-Powered Marketing Intelligence</span>
    <span>${new Date().toISOString().slice(0, 10)}</span>
  `;
  container.appendChild(footer);

  document.body.appendChild(container);

  // ---- generate PDF ----
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const opt: any = {
    margin: [14, 10, 14, 10],
    filename,
    image: { type: "jpeg", quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      logging: false,
      letterRendering: true,
    },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    pagebreak: { mode: ["avoid-all", "css", "legacy"] },
  };

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (html2pdf() as any).set(opt).from(container).save();
  } finally {
    document.body.removeChild(container);
  }
}
