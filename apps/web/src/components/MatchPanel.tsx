import { useState } from "react";
import { useProfiles } from "@/context/ProfileContext";
import { fetchMatchRank, type RankedJobMatch } from "@/lib/api";

const SENIORITY = ["any", "intern", "junior", "mid", "senior", "lead"];

export function MatchPanel() {
  const { activeId } = useProfiles();
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [seniority, setSeniority] = useState("any");
  const [minScore, setMinScore] = useState(50);
  const [results, setResults] = useState<RankedJobMatch[]>([]);
  const [profileRequired, setProfileRequired] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRank() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMatchRank({
        profile_id: activeId,
        remote_only: remoteOnly,
        seniority,
        min_score: minScore,
      });
      setResults(data.results);
      setProfileRequired(data.profile_required);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro no ranking");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mb-10 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold">Ranking ATS (Fase 3)</h2>
      <p className="mt-1 text-sm text-slate-400">
        Score explicável vs vagas salvas (skills, senioridade, experiência, semântica).
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={remoteOnly}
            onChange={(e) => setRemoteOnly(e.target.checked)}
          />
          Só remoto
        </label>
        <label className="flex items-center gap-2">
          Senioridade vaga
          <select
            value={seniority}
            onChange={(e) => setSeniority(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
          >
            {SENIORITY.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2">
          Score mín.
          <input
            type="number"
            min={0}
            max={100}
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-16 rounded-lg border border-slate-700 bg-slate-950 px-2 py-1"
          />
        </label>
        <button
          type="button"
          onClick={() => void handleRank()}
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2 font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Calculando…" : "Calcular ranking"}
        </button>
      </div>

      {profileRequired && (
        <p className="mt-4 text-amber-400 text-sm">
          Cadastre seu perfil na aba Perfil antes de ranquear.
        </p>
      )}
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      <ul className="mt-6 space-y-3">
        {results.map((item) => (
          <li key={item.job_id} className="rounded-lg border border-slate-700 p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="font-medium">
                  {item.title}{" "}
                  <span className="text-xs text-slate-500">
                    ({item.source}) {item.is_remote ? "· remoto" : ""}
                  </span>
                </p>
                <p className="text-sm text-slate-400">
                  {item.company ?? ""} · senioridade vaga: {item.seniority ?? "?"}
                </p>
              </div>
              <span className="text-2xl font-bold text-brand-400">{item.match.score}%</span>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400 sm:grid-cols-4">
              <span>Skills: {item.match.breakdown.skills}</span>
              <span>Seniority: {item.match.breakdown.seniority}</span>
              <span>Exp: {item.match.breakdown.experience}</span>
              <span>Semântico: {item.match.breakdown.semantic_match}</span>
            </div>
            {item.match.matched.length > 0 && (
              <p className="mt-2 text-xs text-emerald-400/90">
                ✓ {item.match.matched.join(", ")}
              </p>
            )}
            {item.match.missing.length > 0 && (
              <p className="mt-1 text-xs text-amber-400/90">✗ {item.match.missing.join(", ")}</p>
            )}
            {item.url && (
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-block text-xs text-brand-400 hover:underline"
              >
                Abrir vaga
              </a>
            )}
          </li>
        ))}
      </ul>
      {results.length === 0 && !loading && !profileRequired && !error && (
        <p className="mt-4 text-sm text-slate-500">
          Nenhuma vaga passou nos filtros (score mín., remoto ou senioridade). Tente score mín. 0
          ou sincronize mais vagas na aba Vagas.
        </p>
      )}
    </section>
  );
}
