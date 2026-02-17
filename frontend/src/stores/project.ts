import { create } from 'zustand';
import type { ProjectResponse } from '@/types';

interface ProjectState {
  project: ProjectResponse | null;
  setProject: (project: ProjectResponse | null) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  project: null,
  setProject: (project) => set({ project }),
}));
