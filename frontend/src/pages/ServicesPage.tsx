import { Link } from "react-router";
import { ArrowRight } from "lucide-react";
import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { useI18n } from "../i18n";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { PUBLIC_HOME_NAV, getContactPath } from "../content/marketing";
import { getSeoLocaleFromLocale } from "../utils/publicRoutes";

/**
 * Phase 1 skeleton. Hero + primary CTA + a one-liner placeholder.
 *
 * Phase 2 will expand this into the full 7-section info architecture
 * documented in `new-positioning.md` § 1.2 (pain cards, deliverables,
 * process, pricing, FAQ, etc.).
 */
export function ServicesPage() {
  const { t, locale } = useI18n();
  const seoLocale = getSeoLocaleFromLocale(locale);

  usePublicPageMetadata({
    title: t("service.audit.metaTitle"),
    description: t("service.audit.metaDescription"),
    basePath: "/services",
  });

  return (
    <div className="min-h-screen bg-[#08141f] text-white">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="dark" />

      <main className="mx-auto flex max-w-5xl flex-col items-center px-4 py-24 text-center lg:px-8 lg:py-32">
        <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
          {t("service.audit.heroTitle")}
        </h1>
        <p className="mt-6 max-w-xl text-lg text-white/75">
          {t("service.audit.heroSubtitle")}
        </p>

        <Link
          to={getContactPath(seoLocale)}
          className="mt-10 inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-7 py-4 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
        >
          {t("service.audit.heroCta")}
          <ArrowRight size={16} />
        </Link>

        <p className="mt-12 max-w-md text-sm text-white/55">
          {t("service.audit.placeholderNote")}
        </p>
      </main>

      <SiteFooter />
    </div>
  );
}
