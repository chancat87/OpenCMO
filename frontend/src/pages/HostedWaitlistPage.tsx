import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { HostedWaitlist } from "../components/marketing/HostedWaitlist";
import { useI18n } from "../i18n";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { PUBLIC_HOME_NAV } from "../content/marketing";

/**
 * Standalone /hosted page for the hosted OpenCMO waitlist.
 */
export function HostedWaitlistPage() {
  const { t } = useI18n();

  usePublicPageMetadata({
    title: t("landing.hosted.title"),
    description: t("landing.hosted.subtitle"),
    basePath: "/hosted",
  });

  return (
    <div className="min-h-screen bg-[#08141f] text-white">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="dark" />

      <main className="mx-auto max-w-5xl px-4 py-24 lg:px-8 lg:py-32">
        <div className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-white/55">
            {t("landing.pathDeployedTitle")}
          </p>
        </div>

        <div className="mt-5">
          <HostedWaitlist variant="page" />
        </div>
      </main>

      <SiteFooter variant="public" />
    </div>
  );
}
