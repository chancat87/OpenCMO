import { useCallback, useEffect, useId, useState } from "react";
import { Sparkles, X } from "lucide-react";
import { useI18n } from "../i18n";

const QR_ASSET = "/contact-qr.png";

interface UnlockCustomPlanCTAProps {
  /** "card" renders a tile that sits alongside dashboard usage cards. "inline" renders a compact text-link, suitable for header rows. */
  variant?: "card" | "inline";
}

export function UnlockCustomPlanCTA({ variant = "card" }: UnlockCustomPlanCTAProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState<boolean>(false);

  const handleOpen = useCallback(() => setOpen(true), []);
  const handleClose = useCallback(() => setOpen(false), []);

  if (variant === "inline") {
    return (
      <>
        <button
          type="button"
          onClick={handleOpen}
          className="inline-flex items-center gap-1.5 rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700 shadow-sm transition-colors hover:bg-amber-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-1"
        >
          <Sparkles size={14} aria-hidden="true" />
          <span>{t("unlock.cta")}</span>
        </button>
        {open && <UnlockModal onClose={handleClose} />}
      </>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={handleOpen}
        className="group flex h-full w-full flex-col items-start gap-2 rounded-lg border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-4 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-amber-300 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-1"
      >
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase text-amber-600">
          <Sparkles size={14} aria-hidden="true" />
          {t("unlock.cardLabel")}
        </span>
        <span className="text-base font-semibold text-slate-900">{t("unlock.cta")}</span>
        <span className="text-xs text-slate-600">{t("unlock.cardHint")}</span>
      </button>
      {open && <UnlockModal onClose={handleClose} />}
    </>
  );
}

interface UnlockModalProps {
  onClose: () => void;
}

function UnlockModal({ onClose }: UnlockModalProps) {
  const { t } = useI18n();
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      aria-describedby={descId}
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 px-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label={t("unlock.close")}
          className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-300"
        >
          <X size={16} aria-hidden="true" />
        </button>

        <div className="flex flex-col items-center text-center">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-600">
            <Sparkles size={18} aria-hidden="true" />
          </span>
          <h3 id={titleId} className="mt-3 text-lg font-semibold text-slate-900">
            {t("unlock.title")}
          </h3>
          <p id={descId} className="mt-1.5 text-sm leading-relaxed text-slate-600">
            {t("unlock.subtitle")}
          </p>

          <div className="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-slate-50 p-3">
            <img
              src={QR_ASSET}
              alt={t("unlock.qrAlt")}
              width={256}
              height={256}
              loading="lazy"
              className="block h-56 w-56 rounded-lg sm:h-64 sm:w-64"
            />
          </div>

          <p className="mt-4 text-xs text-slate-500">{t("unlock.footer")}</p>

          <button
            type="button"
            onClick={onClose}
            className="mt-5 inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-300"
          >
            {t("unlock.close")}
          </button>
        </div>
      </div>
    </div>
  );
}
