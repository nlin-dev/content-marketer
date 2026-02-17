import { create } from 'zustand';

interface UiState {
  loadingActions: Record<string, boolean>;
  error: string | null;
  editMode: boolean;
  isDirty: boolean;
  setLoading: (key: string, loading: boolean) => void;
  setError: (error: string | null) => void;
  setEditMode: (v: boolean) => void;
  setIsDirty: (v: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  loadingActions: {},
  error: null,
  editMode: false,
  isDirty: false,
  setLoading: (key, loading) =>
    set((state) => ({
      loadingActions: { ...state.loadingActions, [key]: loading },
    })),
  setError: (error) => set({ error }),
  setEditMode: (v) => set({ editMode: v }),
  setIsDirty: (v) => set({ isDirty: v }),
}));
