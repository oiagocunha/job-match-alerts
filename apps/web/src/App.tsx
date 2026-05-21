import { FormEvent, useCallback, useEffect, useState } from "react";
import { JobsLab } from "@/components/JobsLab";
import { MatchPanel } from "@/components/MatchPanel";
import { ProfilePanel } from "@/components/ProfilePanel";
import { ProfileSelector } from "@/components/ProfileSelector";
import { ProfileProvider } from "@/context/ProfileContext";
import {
  AlertRule,
  AlertRuleCreate,
  createAlertRule,
  deleteAlertRule,
  fetchAlertRules,
  fetchHealth,
} from "@/lib/api";

type Tab = "perfil" | "vagas" | "ats" | "alertas";

export default function App() {
  const [tab, setTab] = useState<Tab>("perfil");
  const [apiStatus, setApiStatus] = useState<"loading" | "ok" | "error">("loading");
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [keywords, setKeywords] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(true);
  const [minScore, setMinScore] = useState(60);
  const [frequency, setFrequency] = useState<"daily" | "weekly">("weekly");

  const load = useCallback(async () => {
    setError(null);
    try {
      await fetchHealth();
      setApiStatus("ok");
      setRules(await fetchAlertRules());
    } catch (e) {
      setApiStatus("error");
      setError(e instanceof Error ? e.message : "Falha ao conectar na API");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await createAlertRule({
        name: name.trim(),
        keywords: keywords.trim() || null,
        remote_only: remoteOnly,
        min_score: minScore,
        frequency,
      });
      setName("");
      setKeywords("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar regra");
    } finally {
      setSubmitting(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "perfil", label: "Perfil" },
    { id: "vagas", label: "Vagas" },
    { id: "ats", label: "ATS Match" },
    { id: "alertas", label: "Alertas" },
  ];

  return (
    <ProfileProvider>
    <div className="mx-auto max-w-4xl px-4 py-10">
      <header className="mb-8">
        <p className="text-sm font-medium uppercase tracking-wider text-brand-500">
          Job Match Alerts
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight">Score ATS por link de vaga</h1>
        <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-slate-700 px-3 py-1 text-sm">
          <span
            className={`h-2 w-2 rounded-full ${
              apiStatus === "ok"
                ? "bg-emerald-400"
                : apiStatus === "loading"
                  ? "bg-amber-400 animate-pulse"
                  : "bg-red-400"
            }`}
          />
          API {apiStatus === "ok" ? "online" : apiStatus === "loading" ? "…" : "offline"}
        </div>
      </header>

      <nav className="mb-8 flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-lg px-4 py-2 text-sm font-medium ${
              tab === t.id
                ? "bg-brand-600 text-white"
                : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {error && (
        <div
          role="alert"
          className="mb-6 rounded-lg border border-red-800 bg-red-950/50 px-4 py-3 text-red-200"
        >
          {error}
        </div>
      )}

      {(tab === "vagas" || tab === "ats") && (
        <div className="mb-6 rounded-lg border border-slate-800 bg-slate-900/30 px-4 py-3">
          <ProfileSelector />
        </div>
      )}

      {tab === "perfil" && <ProfilePanel />}
      {tab === "vagas" && <JobsLab />}
      {tab === "ats" && <MatchPanel />}
      {tab === "alertas" && (
        <>
          <section className="mb-10 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
            <h2 className="text-lg font-semibold">Nova regra de alerta</h2>
            <form onSubmit={handleSubmit} className="mt-4 space-y-4">
              <label className="block">
                <span className="text-sm text-slate-300">Nome</span>
                <input
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                />
              </label>
              <label className="block">
                <span className="text-sm text-slate-300">Palavras-chave</span>
                <input
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                />
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={remoteOnly}
                  onChange={(e) => setRemoteOnly(e.target.checked)}
                />
                Apenas remoto
              </label>
              <label className="flex items-center gap-2 text-sm">
                Score mínimo ATS
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="w-20 rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
                />
              </label>
              <button
                type="submit"
                disabled={submitting || apiStatus !== "ok"}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                Criar regra
              </button>
            </form>
          </section>
          <section>
            <h2 className="text-lg font-semibold">Regras ativas</h2>
            <ul className="mt-4 space-y-3">
              {rules.map((rule) => (
                <li
                  key={rule.id}
                  className="flex justify-between rounded-xl border border-slate-800 px-4 py-3"
                >
                  <div>
                    <p className="font-medium">{rule.name}</p>
                    <p className="text-sm text-slate-400">
                      {rule.keywords ?? ""} · score ≥ {rule.min_score}
                      {rule.remote_only ? " · remoto" : ""}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => void deleteAlertRule(rule.id).then(load)}
                    className="text-sm text-red-400"
                  >
                    Remover
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
    </ProfileProvider>
  );
}
