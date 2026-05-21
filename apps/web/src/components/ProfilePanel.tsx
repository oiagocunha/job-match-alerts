import { FormEvent, useCallback, useEffect, useState } from "react";
import { useProfiles } from "@/context/ProfileContext";
import {
  deleteProfile,
  parseResume,
  updateProfile,
  type ProfileRead,
  type ProfileStructured,
} from "@/lib/api";

const SENIORITY_OPTIONS = ["intern", "junior", "mid", "senior", "lead", "unknown"];

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function ProfilePanel() {
  const {
    profiles,
    activeId,
    activeProfile,
    setActiveId,
    refreshProfiles,
    refreshActive,
  } = useProfiles();

  const [label, setLabel] = useState("");
  const [structured, setStructured] = useState<ProfileStructured | null>(null);
  const [skillsText, setSkillsText] = useState("");
  const [showRawText, setShowRawText] = useState(false);
  const [rawText, setRawText] = useState("");
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const syncForm = useCallback((profile: ProfileRead) => {
    setLabel(profile.label);
    setStructured(profile.structured);
    setRawText(profile.raw_text ?? "");
    setSkillsText(profile.structured.skills.join(", "));
    setDirty(false);
    setMessage(null);
  }, []);

  useEffect(() => {
    if (activeProfile) syncForm(activeProfile);
    else {
      setStructured(null);
      setLabel("");
      setRawText("");
      setSkillsText("");
      setDirty(false);
    }
  }, [activeProfile, syncForm]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setLoading("upload");
    setError(null);
    setMessage(null);
    try {
      const created = await parseResume(file, true);
      await refreshProfiles();
      setActiveId(created.id);
      syncForm(created);
      setMessage(`“${created.label}” importado e salvo.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro no upload");
    } finally {
      setLoading(null);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir este currículo?")) return;
    setError(null);
    try {
      await deleteProfile(id);
      await refreshProfiles();
      setMessage("Currículo removido.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir");
    }
  }

  function markDirty() {
    setDirty(true);
    setMessage(null);
  }

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!activeId || !structured) return;
    setLoading("save");
    setError(null);
    try {
      const payload: ProfileStructured = {
        ...structured,
        skills: skillsText
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      };
      const saved = await updateProfile(activeId, {
        label: label.trim() || undefined,
        structured: payload,
        raw_text: rawText,
      });
      await refreshProfiles();
      await refreshActive();
      syncForm(saved);
      setMessage("Alterações salvas.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setLoading(null);
    }
  }

  return (
    <section className="mb-10 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Currículos</h2>
          <p className="mt-1 text-sm text-slate-400">
            Cada PDF vira um perfil salvo. Escolha qual usar no score ATS (abas Vagas e Match).
          </p>
        </div>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium hover:bg-brand-700">
          <input type="file" accept=".pdf" className="hidden" onChange={(e) => void handleUpload(e)} />
          {loading === "upload" ? "Importando…" : "+ Adicionar PDF"}
        </label>
      </div>

      {message && <p className="mt-3 text-sm text-emerald-400">{message}</p>}
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

      <div className="mt-6 grid gap-6 lg:grid-cols-[240px_1fr]">
        <aside className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Salvos ({profiles.length})
          </p>
          {profiles.length === 0 ? (
            <p className="text-sm text-slate-500">Nenhum currículo ainda.</p>
          ) : (
            <ul className="space-y-2">
              {profiles.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => setActiveId(p.id)}
                    className={`w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
                      p.id === activeId
                        ? "border-brand-600 bg-brand-950/40"
                        : "border-slate-700 hover:border-slate-600"
                    }`}
                  >
                    <span className="font-medium">{p.label}</span>
                    <span className="mt-1 block text-xs text-slate-500">
                      {p.skills_count} skills · {p.seniority}
                    </span>
                    <span className="mt-0.5 block text-xs text-slate-600">
                      {formatDate(p.updated_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <div>
          {!activeId || !structured ? (
            <p className="text-sm text-slate-500">
              Adicione um PDF ou selecione um currículo na lista.
            </p>
          ) : (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <p className="text-sm text-slate-400">
                  {dirty ? "Alterações não salvas" : "Salvo"}
                  {activeProfile && !dirty && (
                    <span className="ml-2 text-slate-500">
                      · {formatDate(activeProfile.updated_at)}
                    </span>
                  )}
                </p>
                <button
                  type="button"
                  onClick={() => void handleDelete(activeId)}
                  className="text-sm text-red-400 hover:text-red-300"
                >
                  Excluir
                </button>
              </div>

              <label className="block text-sm">
                Nome do perfil
                <input
                  value={label}
                  onChange={(e) => {
                    setLabel(e.target.value);
                    markDirty();
                  }}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                />
              </label>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm">
                  Nome (currículo)
                  <input
                    value={structured.name ?? ""}
                    onChange={(e) => {
                      setStructured({ ...structured, name: e.target.value });
                      markDirty();
                    }}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                  />
                </label>
                <label className="block text-sm">
                  E-mail
                  <input
                    value={structured.email ?? ""}
                    onChange={(e) => {
                      setStructured({ ...structured, email: e.target.value });
                      markDirty();
                    }}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                  />
                </label>
              </div>

              <label className="block text-sm">
                Headline
                <input
                  value={structured.headline ?? ""}
                  onChange={(e) => {
                    setStructured({ ...structured, headline: e.target.value });
                    markDirty();
                  }}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                />
              </label>

              <label className="block text-sm">
                Skills (separadas por vírgula)
                <textarea
                  value={skillsText}
                  onChange={(e) => {
                    setSkillsText(e.target.value);
                    markDirty();
                  }}
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                />
              </label>

              <label className="block text-sm">
                Senioridade
                <select
                  value={structured.seniority ?? "unknown"}
                  onChange={(e) => {
                    setStructured({ ...structured, seniority: e.target.value });
                    markDirty();
                  }}
                  className="mt-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
                >
                  {SENIORITY_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </label>

              <details
                open={showRawText}
                onToggle={(e) => setShowRawText((e.target as HTMLDetailsElement).open)}
                className="rounded-lg border border-slate-800"
              >
                <summary className="cursor-pointer px-4 py-3 text-sm text-slate-300">
                  Texto completo do PDF ({rawText.length.toLocaleString()} caracteres)
                </summary>
                <textarea
                  value={rawText}
                  onChange={(e) => {
                    setRawText(e.target.value);
                    markDirty();
                  }}
                  rows={10}
                  className="w-full border-t border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs leading-relaxed"
                />
              </details>

              {activeProfile?.source_filename && (
                <p className="text-xs text-slate-500">Arquivo: {activeProfile.source_filename}</p>
              )}

              <button
                type="submit"
                disabled={loading !== null || !dirty}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
              >
                {loading === "save" ? "Salvando…" : "Salvar alterações"}
              </button>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}
