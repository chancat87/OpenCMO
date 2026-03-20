import { useState, useEffect } from "react";
import { X, Key, Check } from "lucide-react";
import { getSettings, saveSettings } from "../../api/settings";
import { useI18n } from "../../i18n";

export function SettingsDialog({ onClose }: { onClose: () => void }) {
  const { t } = useI18n();
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<{
    api_key_set: boolean;
    api_key_masked: string;
    reddit_configured: boolean;
    reddit_username: string;
    auto_publish: boolean;
  } | null>(null);

  // Reddit fields
  const [redditClientId, setRedditClientId] = useState("");
  const [redditClientSecret, setRedditClientSecret] = useState("");
  const [redditUsername, setRedditUsername] = useState("");
  const [redditPassword, setRedditPassword] = useState("");
  const [autoPublish, setAutoPublish] = useState(false);

  useEffect(() => {
    getSettings().then((s) => {
      setCurrentStatus({
        api_key_set: s.api_key_set,
        api_key_masked: s.api_key_masked,
        reddit_configured: s.reddit_configured,
        reddit_username: s.reddit_username,
        auto_publish: s.auto_publish,
      });
      setBaseUrl(s.base_url);
      setModel(s.model);
      setAutoPublish(s.auto_publish);
    });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setSaved(false);
    try {
      await saveSettings({
        OPENAI_API_KEY: apiKey || undefined,
        OPENAI_BASE_URL: baseUrl,
        OPENCMO_MODEL_DEFAULT: model,
        REDDIT_CLIENT_ID: redditClientId || undefined,
        REDDIT_CLIENT_SECRET: redditClientSecret || undefined,
        REDDIT_USERNAME: redditUsername || undefined,
        REDDIT_PASSWORD: redditPassword || undefined,
        OPENCMO_AUTO_PUBLISH: autoPublish ? "1" : "0",
      });
      setSaved(true);
      setApiKey("");
      setRedditClientId("");
      setRedditClientSecret("");
      setRedditUsername("");
      setRedditPassword("");
      const s = await getSettings();
      setCurrentStatus({
        api_key_set: s.api_key_set,
        api_key_masked: s.api_key_masked,
        reddit_configured: s.reddit_configured,
        reddit_username: s.reddit_username,
        auto_publish: s.auto_publish,
      });
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm shadow-sm placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="w-full max-w-md max-h-[85vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{t("settings.title")}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          {/* API Key Status */}
          {currentStatus && (
            <div
              className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium ${
                currentStatus.api_key_set
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-amber-50 text-amber-700"
              }`}
            >
              <Key size={14} />
              {currentStatus.api_key_set
                ? `${t("settings.apiKeySet")} (${currentStatus.api_key_masked})`
                : t("settings.apiKeyNotSet")}
            </div>
          )}

          {/* API Key */}
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {t("settings.apiKey")}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={t("settings.apiKeyPlaceholder")}
              className={inputClass}
            />
            <p className="mt-1 text-[10px] text-slate-400">
              {t("settings.apiKeyHint")}
            </p>
          </div>

          {/* Base URL */}
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {t("settings.baseUrl")}
            </label>
            <input
              type="url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder={t("settings.baseUrlPlaceholder")}
              className={inputClass}
            />
            <p className="mt-1 text-[10px] text-slate-400">
              {t("settings.baseUrlHint")}
            </p>
          </div>

          {/* Model */}
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {t("settings.model")}
            </label>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder={t("settings.modelPlaceholder")}
              className={inputClass}
            />
            <p className="mt-1 text-[10px] text-slate-400">
              {t("settings.modelHint")}
            </p>
          </div>

          {/* ── Reddit Section ── */}
          <div className="border-t border-slate-100 pt-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-800">
              {t("settings.redditSection")}
            </h3>

            {/* Reddit Status */}
            {currentStatus && (
              <div
                className={`mb-3 flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium ${
                  currentStatus.reddit_configured
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-amber-50 text-amber-700"
                }`}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 0-.463.327.327 0 0 0-.231-.094c-.076 0-.14.028-.195.084-.659.659-1.883.915-2.536.915-.653 0-1.89-.256-2.534-.915a.28.28 0 0 0-.195-.084z" />
                </svg>
                {currentStatus.reddit_configured
                  ? `${t("settings.redditConfigured")} (u/${currentStatus.reddit_username})`
                  : t("settings.redditNotConfigured")}
              </div>
            )}

            {/* Reddit Client ID */}
            <div className="mb-3">
              <label className="mb-1 block text-xs font-medium text-slate-600">
                {t("settings.redditClientId")}
              </label>
              <input
                type="text"
                value={redditClientId}
                onChange={(e) => setRedditClientId(e.target.value)}
                placeholder={t("settings.redditClientIdPlaceholder")}
                className={inputClass}
              />
            </div>

            {/* Reddit Client Secret */}
            <div className="mb-3">
              <label className="mb-1 block text-xs font-medium text-slate-600">
                {t("settings.redditClientSecret")}
              </label>
              <input
                type="password"
                value={redditClientSecret}
                onChange={(e) => setRedditClientSecret(e.target.value)}
                placeholder={t("settings.redditClientSecretPlaceholder")}
                className={inputClass}
              />
            </div>

            {/* Reddit Username */}
            <div className="mb-3">
              <label className="mb-1 block text-xs font-medium text-slate-600">
                {t("settings.redditUsername")}
              </label>
              <input
                type="text"
                value={redditUsername}
                onChange={(e) => setRedditUsername(e.target.value)}
                placeholder={t("settings.redditUsernamePlaceholder")}
                className={inputClass}
              />
            </div>

            {/* Reddit Password */}
            <div className="mb-3">
              <label className="mb-1 block text-xs font-medium text-slate-600">
                {t("settings.redditPassword")}
              </label>
              <input
                type="password"
                value={redditPassword}
                onChange={(e) => setRedditPassword(e.target.value)}
                placeholder={t("settings.redditPasswordPlaceholder")}
                className={inputClass}
              />
            </div>

            <p className="mb-3 text-[10px] text-slate-400">
              {t("settings.redditHint")}
            </p>

            {/* Auto Publish Toggle */}
            <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5">
              <div>
                <p className="text-xs font-medium text-slate-700">{t("settings.autoPublish")}</p>
                <p className="text-[10px] text-slate-400">{t("settings.autoPublishHint")}</p>
              </div>
              <button
                type="button"
                onClick={() => setAutoPublish(!autoPublish)}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  autoPublish ? "bg-indigo-600" : "bg-slate-300"
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    autoPublish ? "translate-x-4" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            {t("common.cancel")}
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 disabled:opacity-50"
          >
            {saved ? (
              <>
                <Check size={14} />
                {t("settings.saved")}
              </>
            ) : (
              t("settings.save")
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
