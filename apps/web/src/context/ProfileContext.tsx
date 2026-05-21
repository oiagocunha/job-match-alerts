import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  fetchProfile,
  listProfiles,
  type ProfileRead,
  type ProfileSummary,
} from "@/lib/api";

const STORAGE_KEY = "job-match-active-profile-id";

type ProfileContextValue = {
  profiles: ProfileSummary[];
  activeId: number | null;
  activeProfile: ProfileRead | null;
  loading: boolean;
  setActiveId: (id: number | null) => void;
  refreshProfiles: () => Promise<void>;
  refreshActive: () => Promise<void>;
};

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [activeId, setActiveIdState] = useState<number | null>(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const n = Number.parseInt(raw, 10);
    return Number.isNaN(n) ? null : n;
  });
  const [activeProfile, setActiveProfile] = useState<ProfileRead | null>(null);
  const [loading, setLoading] = useState(true);

  const setActiveId = useCallback((id: number | null) => {
    setActiveIdState(id);
    if (id == null) localStorage.removeItem(STORAGE_KEY);
    else localStorage.setItem(STORAGE_KEY, String(id));
  }, []);

  const refreshProfiles = useCallback(async () => {
    const list = await listProfiles();
    setProfiles(list);
    if (list.length === 0) {
      setActiveId(null);
      return;
    }
    const stillExists = activeId != null && list.some((p) => p.id === activeId);
    if (!stillExists) setActiveId(list[0].id);
  }, [activeId, setActiveId]);

  const refreshActive = useCallback(async () => {
    if (activeId == null) {
      setActiveProfile(null);
      return;
    }
    try {
      setActiveProfile(await fetchProfile(activeId));
    } catch {
      setActiveProfile(null);
    }
  }, [activeId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const list = await listProfiles();
        if (cancelled) return;
        setProfiles(list);
        if (list.length === 0) {
          setActiveId(null);
        } else {
          const stored = localStorage.getItem(STORAGE_KEY);
          const storedId = stored ? Number.parseInt(stored, 10) : NaN;
          const valid =
            !Number.isNaN(storedId) && list.some((p) => p.id === storedId);
          const nextId = valid ? storedId : list[0].id;
          setActiveId(nextId);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setActiveId]);

  useEffect(() => {
    if (activeId == null) {
      setActiveProfile(null);
      return;
    }
    let cancelled = false;
    void fetchProfile(activeId).then((p) => {
      if (!cancelled) setActiveProfile(p);
    });
    return () => {
      cancelled = true;
    };
  }, [activeId]);

  const value = useMemo(
    () => ({
      profiles,
      activeId,
      activeProfile,
      loading,
      setActiveId,
      refreshProfiles,
      refreshActive,
    }),
    [profiles, activeId, activeProfile, loading, setActiveId, refreshProfiles, refreshActive],
  );

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfiles() {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error("useProfiles deve ser usado dentro de ProfileProvider");
  return ctx;
}
