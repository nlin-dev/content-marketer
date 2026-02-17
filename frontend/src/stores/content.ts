import { create } from 'zustand';
import type { VersionSummary } from '@/types';

interface ContentState {
  currentHtml: string;
  streaming: boolean;
  versions: VersionSummary[];
  currentVersionId: string | null;
  setCurrentHtml: (html: string) => void;
  appendToken: (token: string) => void;
  setStreaming: (v: boolean) => void;
  setVersions: (v: VersionSummary[]) => void;
  setCurrentVersionId: (id: string | null) => void;
}

export const useContentStore = create<ContentState>((set) => ({
  currentHtml: '',
  streaming: false,
  versions: [],
  currentVersionId: null,
  setCurrentHtml: (html) => set({ currentHtml: html }),
  appendToken: (token) =>
    set((state) => ({ currentHtml: state.currentHtml + token })),
  setStreaming: (v) => set({ streaming: v }),
  setVersions: (v) => set({ versions: v }),
  setCurrentVersionId: (id) => set({ currentVersionId: id }),
}));
