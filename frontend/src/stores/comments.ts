import { create } from 'zustand';
import type { CommentResponse } from '@/types';

interface CommentsState {
  comments: CommentResponse[];
  setComments: (comments: CommentResponse[]) => void;
  addComment: (comment: CommentResponse) => void;
  resolveComment: (id: string, resolved: boolean) => void;
}

export const useCommentsStore = create<CommentsState>((set) => ({
  comments: [],
  setComments: (comments) => set({ comments }),
  addComment: (comment) =>
    set((state) => ({ comments: [...state.comments, comment] })),
  resolveComment: (id, resolved) =>
    set((state) => ({
      comments: state.comments.map((c) =>
        c.id === id ? { ...c, resolved } : c,
      ),
    })),
}));
