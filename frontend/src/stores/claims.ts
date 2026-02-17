import { create } from 'zustand';
import type { ClaimResponse } from '@/types';

interface ClaimsState {
  recommended: ClaimResponse[];
  selected: ClaimResponse[];
  setRecommended: (claims: ClaimResponse[]) => void;
  addSelected: (claim: ClaimResponse) => void;
  removeSelected: (id: string) => void;
  reorderSelected: (ids: string[]) => void;
  clearSelected: () => void;
}

export const useClaimsStore = create<ClaimsState>((set) => ({
  recommended: [],
  selected: [],
  setRecommended: (claims) => set({ recommended: claims }),
  addSelected: (claim) =>
    set((state) => ({
      selected: state.selected.some((c) => c.id === claim.id)
        ? state.selected
        : [...state.selected, claim],
    })),
  removeSelected: (id) =>
    set((state) => ({
      selected: state.selected.filter((c) => c.id !== id),
    })),
  reorderSelected: (ids) =>
    set((state) => {
      const map = new Map(state.selected.map((c) => [c.id, c]));
      return {
        selected: ids
          .map((id) => map.get(id))
          .filter((c): c is ClaimResponse => c !== undefined),
      };
    }),
  clearSelected: () => set({ selected: [] }),
}));
