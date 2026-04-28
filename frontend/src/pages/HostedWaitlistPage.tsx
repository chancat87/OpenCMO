import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { HostedWaitlist } from "../components/marketing/HostedWaitlist";
import { useI18n } from "../i18n";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { PUBLIC_HOME_NAV } from "../content/marketing";

/**
 * Standalone /hosted page for the OpenCMO managed-version waitlist.
 *
 * Same component as the inline one on the home page, but with
 * variant="page" — bigger heading, centered, more whitespace.
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
        <HostedWaitlist variant="page" />
      </main>

      <SiteFooter />
    </div>
  );
}
