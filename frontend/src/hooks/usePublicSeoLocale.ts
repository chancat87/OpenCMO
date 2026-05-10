import { useLocation } from "react-router";
import { stripPublicLocalePrefix, type SeoLocale } from "../utils/publicRoutes";

export function usePublicSeoLocale(): SeoLocale {
  const location = useLocation();
  const { routeLocale } = stripPublicLocalePrefix(location.pathname);
  return routeLocale ?? "en";
}
