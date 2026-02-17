'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { editContent } from '@/lib/api';
import { useProjectStore } from '@/stores/project';
import { useUiStore } from '@/stores/ui';
import { useRefreshVersions } from '@/hooks/useRefreshVersions';

const QUICK_ACTIONS = [
  'Make more concise',
  'Simplify language',
  'Add call to action',
] as const;

export function AiEditBar() {
  const [instruction, setInstruction] = useState('');
  const [loading, setLoading] = useState(false);
  const project = useProjectStore((s) => s.project);
  const setError = useUiStore((s) => s.setError);
  const { refreshAfterEdit } = useRefreshVersions(project?.id);

  async function applyEdit(text: string) {
    if (!project || !text.trim()) return;
    setLoading(true);
    try {
      const { version } = await editContent(project.id, { instruction: text.trim() });
      await refreshAfterEdit(version.html_content, version.id);
      setInstruction('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Edit failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && applyEdit(instruction)}
          placeholder="Describe how to edit the content..."
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          disabled={loading}
        />
        <Button
          onClick={() => applyEdit(instruction)}
          loading={loading}
          disabled={!instruction.trim()}
          size="sm"
        >
          Apply Edit
        </Button>
      </div>
      <div className="flex flex-wrap gap-2">
        {QUICK_ACTIONS.map((action) => (
          <Button
            key={action}
            variant="secondary"
            size="sm"
            onClick={() => applyEdit(action)}
            disabled={loading}
          >
            {action}
          </Button>
        ))}
      </div>
    </div>
  );
}
