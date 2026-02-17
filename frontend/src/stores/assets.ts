import { create } from 'zustand';
import type { AssetResponse } from '@/types';

interface AssetsState {
  available: AssetResponse[];
  selected: AssetResponse[];
  setAvailable: (assets: AssetResponse[]) => void;
  addSelected: (asset: AssetResponse) => void;
  removeSelected: (id: string) => void;
  clearSelected: () => void;
  reset: () => void;
}

export const useAssetsStore = create<AssetsState>((set) => ({
  available: [],
  selected: [],
  setAvailable: (assets) => set({ available: assets }),
  addSelected: (asset) =>
    set((state) => ({
      selected: state.selected.some((a) => a.id === asset.id)
        ? state.selected
        : [...state.selected, asset],
    })),
  removeSelected: (id) =>
    set((state) => ({
      selected: state.selected.filter((a) => a.id !== id),
    })),
  clearSelected: () => set({ selected: [] }),
  reset: () => set({ available: [], selected: [] }),
}));
