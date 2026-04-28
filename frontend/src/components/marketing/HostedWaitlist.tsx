import { useState, type FormEvent } from "react";
import { useI18n } from "../../i18n";
import { submitWaitlist, type WaitlistSource } from "../../api/waitlist";

const VARIANT_TO_SOURCE: Record<"inline" | "page", WaitlistSource> = {
  inline: "home_inline",
  page: "hosted_page",
};

// Mirrors backend `_EMAIL_RE` so we don't fire pointless POSTs.
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

type Status = "idle" | "submitting" | "success" | "error";

interface Props {
  variant: "inline" | "page";
}

export function HostedWaitlist({ variant }: Props) {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState<string>("");

  const isInline = variant === "inline";

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim().toLowerCase();
    if (!EMAIL_RE.test(trimmed) || trimmed.length < 5 || trimmed.length > 254) {
      setStatus("error");
      setErrorMsg(t("landing.hosted.errorBadEmail"));
      return;
    }
    setStatus("submitting");
    setErrorMsg("");
    try {
      const res = await submitWaitlist(trimmed, VARIANT_TO_SOURCE[variant]);
      if (res.ok) {
        setStatus("success");
      } else {
        setStatus("error");
        setErrorMsg(t("landing.hosted.errorGeneric"));
      }
    } catch {
      setStatus("error");
      setErrorMsg(t("landing.hosted.errorGeneric"));
    }
  };

  if (status === "success") {
    return (
      <div
        className={
          isInline
            ? "rounded-2xl border border-emerald-200/40 bg-emerald-500/8 px-5 py-4 text-sm text-emerald-100"
            : "mx-auto max-w-md rounded-3xl border border-emerald-200/40 bg-emerald-500/8 px-8 py-6 text-center text-base text-emerald-100"
        }
      >
        {t("landing.hosted.success")}
      </div>
    );
  }

  const wrapperClass = isInline
    ? "rounded-3xl border border-white/10 bg-white/5 p-6 sm:p-8"
    : "mx-auto max-w-xl rounded-3xl border border-white/10 bg-white/5 p-8 sm:p-10";

  return (
    <div className={wrapperClass}>
      <div className={isInline ? "" : "text-center"}>
        <h3
          className={
            isInline
              ? "font-display text-xl font-semibold tracking-tight text-white sm:text-2xl"
              : "font-display text-2xl font-semibold tracking-tight text-white sm:text-3xl"
          }
        >
          {t("landing.hosted.title")}
        </h3>
        <p
          className={
            isInline
              ? "mt-2 text-sm text-white/70"
              : "mt-3 text-base text-white/70"
          }
        >
          {t("landing.hosted.subtitle")}
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className={
          isInline
            ? "mt-4 flex flex-col gap-3 sm:flex-row"
            : "mt-6 flex flex-col gap-3"
        }
      >
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (status === "error") setStatus("idle");
          }}
          placeholder={t("landing.hosted.inputPlaceholder")}
          disabled={status === "submitting"}
          className="flex-1 rounded-full border border-white/15 bg-white/5 px-5 py-3 text-sm text-white placeholder-white/40 outline-none transition-colors focus:border-white/40 disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={status === "submitting"}
          className="inline-flex items-center justify-center rounded-full bg-[#f7ecde] px-6 py-3 text-sm font-semibold text-[#082032] transition-colors hover:bg-white disabled:opacity-60"
        >
          {status === "submitting"
            ? t("landing.hosted.submitting")
            : t("landing.hosted.submitButton")}
        </button>
      </form>

      {status === "error" ? (
        <p className="mt-3 text-xs text-red-300">{errorMsg}</p>
      ) : null}

      <p className={isInline ? "mt-3 text-xs text-white/50" : "mt-4 text-center text-xs text-white/50"}>
        {t("landing.hosted.note")}
      </p>
    </div>
  );
}
