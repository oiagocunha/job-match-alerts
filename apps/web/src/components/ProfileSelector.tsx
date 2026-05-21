import { useProfiles } from "@/context/ProfileContext";

type Props = {
  className?: string;
  hint?: string;
};

export function ProfileSelector({ className = "", hint }: Props) {
  const { profiles, activeId, setActiveId, loading } = useProfiles();

  if (loading && profiles.length === 0) {
    return <p className={`text-sm text-slate-500 ${className}`}>Carregando currículos…</p>;
  }

  if (profiles.length === 0) {
    return (
      <p className={`text-sm text-amber-400 ${className}`}>
        {hint ?? "Cadastre um currículo na aba Perfil para calcular o score ATS."}
      </p>
    );
  }

  const active = profiles.find((p) => p.id === activeId);

  return (
    <label className={`flex flex-wrap items-center gap-2 text-sm ${className}`}>
      <span className="text-slate-400">Currículo para análise</span>
      <select
        value={activeId ?? ""}
        onChange={(e) => setActiveId(Number(e.target.value))}
        className="min-w-[200px] rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
      >
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.label}
            {p.skills_count > 0 ? ` · ${p.skills_count} skills` : ""}
          </option>
        ))}
      </select>
      {active && (
        <span className="text-xs text-slate-500">
          {active.seniority}
          {active.headline ? ` · ${active.headline}` : ""}
        </span>
      )}
    </label>
  );
}
