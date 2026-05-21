import { FormEvent, useCallback, useEffect, useState } from "react";
import { useProfiles } from "@/context/ProfileContext";
import {
  deleteJob,
  fetchIntegrationsStatus,
  importJobUrl,
  listJobs,
  type IntegrationStatus,
  type JobImportResult,
  type JobRead,
} from "@/lib/api";

export function JobsLab() {
  const { activeId } = useProfiles();
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [importUrl, setImportUrl] = useState("");
  const [lastImport, setLastImport] = useState<JobImportResult | null>(null);
  const [savedJobs, setSavedJobs] = useState<JobRead[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    try {
      setSavedJobs(await listJobs());
    } catch {
      setSavedJobs([]);
    }
  }, []);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  async function handleCheckOpenAI() {
    setLoading("status");
    setError(null);
    try {
      setIntegrations(await fetchIntegrationsStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao testar OpenAI");
    } finally {
      setLoading(null);
    }
  }

  async function handleImport(e: FormEvent) {
    e.preventDefault();
    if (!importUrl.trim()) return;
    setLoading("import");
    setError(null);
    setLastImport(null);
    try {
      const result = await importJobUrl(importUrl.trim(), activeId);
      setLastImport(result);
      setImportUrl("");
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao importar vaga");
    } finally {
      setLoading(null);
    }
  }

  async function handleDelete(id: number) {
    setError(null);
    try {
      await deleteJob(id);
      if (lastImport?.job.id === id) setLastImport(null);
      await loadJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao remover");
    }
  }

  return (
    <section className="mb-10 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <h2 className="text-lg font-semibold">Cadastrar vaga por link</h2>
      <p className="mt-1 text-sm text-slate-400">
        Cole o link da vaga (Gupy, LinkedIn, Inhire ou página com a descrição). A API importa o
        conteúdo, analisa requisitos e calcula seu score ATS na hora.
      </p>

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => void handleCheckOpenAI()}
          disabled={loading !== null}
          className="rounded-lg border border-slate-600 px-3 py-2 text-sm hover:bg-slate-800"
        >
          Testar OpenAI
        </button>
      </div>
      {integrations && (
        <p
          className={`mt-2 text-sm ${integrations.openai.ok ? "text-emerald-400" : "text-red-400"}`}
        >
          OpenAI: {integrations.openai.message}
        </p>
      )}

      <form onSubmit={handleImport} className="mt-6 flex flex-wrap gap-3">
        <input
          required
          value={importUrl}
          onChange={(e) => setImportUrl(e.target.value)}
          placeholder="https://empresa.gupy.io/jobs/..."
          className="min-w-[280px] flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={loading !== null}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
        >
          {loading === "import" ? "Analisando…" : "Importar e ver score"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}

      {lastImport && (
        <div className="mt-6 rounded-lg border border-brand-700/50 bg-brand-950/30 p-4">
          <p className="font-medium">{lastImport.job.title}</p>
          <p className="text-sm text-slate-400">
            {lastImport.job.company ?? ""} · {lastImport.job.source}
            {lastImport.job.is_remote ? " · remoto" : ""} · {lastImport.job.seniority}
          </p>
          {lastImport.profile_required ? (
            <p className="mt-2 text-sm text-amber-400">
              Cadastre seu currículo na aba Perfil para ver o score ATS.
            </p>
          ) : lastImport.match ? (
            <>
              <p className="mt-3 text-3xl font-bold text-brand-400">
                {lastImport.match.score}% <span className="text-base font-normal">fit ATS</span>
              </p>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400 sm:grid-cols-4">
                <span>Skills: {lastImport.match.breakdown.skills}</span>
                <span>Seniority: {lastImport.match.breakdown.seniority}</span>
                <span>Exp: {lastImport.match.breakdown.experience}</span>
                <span>Semântico: {lastImport.match.breakdown.semantic_match}</span>
              </div>
              {lastImport.match.matched.length > 0 && (
                <p className="mt-2 text-xs text-emerald-400">
                  ✓ {lastImport.match.matched.join(", ")}
                </p>
              )}
              {lastImport.match.missing.length > 0 && (
                <p className="mt-1 text-xs text-amber-400">
                  ✗ {lastImport.match.missing.join(", ")}
                </p>
              )}
            </>
          ) : null}
          {lastImport.job.url && (
            <a
              href={lastImport.job.url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-sm text-brand-400 hover:underline"
            >
              Abrir vaga original
            </a>
          )}
        </div>
      )}

      {savedJobs.length > 0 && (
        <div className="mt-8">
          <h3 className="text-sm font-semibold text-slate-300">Vagas cadastradas</h3>
          <ul className="mt-3 space-y-2">
            {savedJobs.map((job) => (
              <li
                key={job.id}
                className="flex items-center justify-between gap-4 rounded-lg border border-slate-700 px-3 py-2 text-sm"
              >
                <span>
                  {job.title}{" "}
                  <span className="text-slate-500">
                    ({job.source}) {job.is_remote ? "· remoto" : ""}
                  </span>
                </span>
                <button
                  type="button"
                  onClick={() => void handleDelete(job.id)}
                  className="text-red-400 hover:text-red-300"
                >
                  Remover
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
