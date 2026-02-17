'use client';

import { useCallback, useEffect, useState } from 'react';
import { useCommentsStore } from '@/stores/comments';
import { useContentStore } from '@/stores/content';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import * as api from '@/lib/api';
import { formatRelativeTime } from '@/lib/format';

export function CommentThread() {
  const comments = useCommentsStore((s) => s.comments);
  const setComments = useCommentsStore((s) => s.setComments);
  const addComment = useCommentsStore((s) => s.addComment);
  const resolveCommentInStore = useCommentsStore((s) => s.resolveComment);
  const currentVersionId = useContentStore((s) => s.currentVersionId);

  const [newText, setNewText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const unresolvedCount = comments.filter((c) => !c.resolved).length;

  const fetchComments = useCallback(async () => {
    if (!currentVersionId) return;
    try {
      const data = await api.getComments(currentVersionId);
      setComments(data);
    } catch {
      // Silently handle
    }
  }, [currentVersionId, setComments]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  async function handleAddComment() {
    if (!newText.trim() || !currentVersionId) return;
    setSubmitting(true);
    try {
      const comment = await api.createComment(currentVersionId, { text: newText.trim() });
      addComment(comment);
      setNewText('');
    } catch {
      // Silently handle
    } finally {
      setSubmitting(false);
    }
  }

  async function handleResolve(commentId: string) {
    setResolvingId(commentId);
    try {
      await api.resolveComment(commentId, { resolved: true });
      resolveCommentInStore(commentId, true);
    } catch {
      // Silently handle
    } finally {
      setResolvingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-slate-900">Comments</h3>
        {unresolvedCount > 0 && (
          <Badge color="amber">{unresolvedCount} unresolved</Badge>
        )}
      </div>

      <div className="space-y-3">
        {comments.map((comment) => (
          <div
            key={comment.id}
            className={`rounded-md border px-3 py-2 ${
              comment.resolved ? 'border-slate-100 bg-slate-50' : 'border-slate-200'
            }`}
          >
            <div className="flex items-center justify-between">
              <span
                className={`text-xs font-medium ${
                  comment.resolved ? 'text-slate-400' : 'text-slate-700'
                }`}
              >
                {comment.user_id}
              </span>
              <span className="text-xs text-slate-400">
                {formatRelativeTime(comment.created_at)}
              </span>
            </div>
            <p
              className={`mt-1 text-sm ${
                comment.resolved ? 'text-slate-400 line-through' : 'text-slate-700'
              }`}
            >
              {comment.text}
            </p>
            {!comment.resolved && (
              <Button
                variant="ghost"
                size="sm"
                className="mt-1 px-0 text-xs text-green-600 hover:text-green-700"
                loading={resolvingId === comment.id}
                onClick={() => handleResolve(comment.id)}
              >
                Resolve
              </Button>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleAddComment();
            }
          }}
          placeholder="Add a comment..."
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
        <Button
          size="sm"
          loading={submitting}
          disabled={!newText.trim()}
          onClick={handleAddComment}
        >
          Add Comment
        </Button>
      </div>
    </div>
  );
}
