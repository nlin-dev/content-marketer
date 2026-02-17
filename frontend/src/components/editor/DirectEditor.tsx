'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import DOMPurify from 'dompurify';
import { Button } from '@/components/ui/Button';
import { AssetSwapModal } from './AssetSwapModal';
import { useContentStore } from '@/stores/content';
import { useProjectStore } from '@/stores/project';
import { useUiStore } from '@/stores/ui';
import { directEditContent } from '@/lib/api';
import { useRefreshVersions } from '@/hooks/useRefreshVersions';

export function DirectEditor() {
  const editorRef = useRef<HTMLDivElement>(null);
  const currentHtml = useContentStore((s) => s.currentHtml);
  const currentVersionId = useContentStore((s) => s.currentVersionId);
  const project = useProjectStore((s) => s.project);
  const setError = useUiStore((s) => s.setError);
  const { refreshAfterEdit } = useRefreshVersions(project?.id);

  const [isDirty, setIsDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [swapAssetId, setSwapAssetId] = useState<string | null>(null);

  function decorateEditor(el: HTMLDivElement) {
    el.querySelectorAll('[data-isi]').forEach((node) => {
      (node as HTMLElement).contentEditable = 'false';
    });
    el.querySelectorAll('[data-claim-id]').forEach((node) => {
      (node as HTMLElement).classList.add('bg-primary-50', 'rounded', 'px-0.5');
    });
  }

  // Set innerHTML on version change — never bind to React state
  useEffect(() => {
    if (!editorRef.current) return;
    editorRef.current.innerHTML = currentHtml;
    decorateEditor(editorRef.current);
    setIsDirty(false);
  }, [currentVersionId]);

  // Track dirty state via input events
  useEffect(() => {
    const el = editorRef.current;
    if (!el) return;

    function handleInput() {
      setIsDirty(true);
    }

    el.addEventListener('input', handleInput);
    return () => {
      el.removeEventListener('input', handleInput);
    };
  }, []);

  const handleSave = useCallback(async () => {
    if (!editorRef.current || !project) return;
    const raw = editorRef.current.innerHTML;
    const clean = DOMPurify.sanitize(raw, { ALLOW_DATA_ATTR: true });

    setSaving(true);
    try {
      const { version } = await directEditContent(project.id, { html_content: clean });
      await refreshAfterEdit(version.html_content, version.id);
      setIsDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }, [project, refreshAfterEdit, setError]);

  const handleDiscard = useCallback(() => {
    if (!editorRef.current) return;
    editorRef.current.innerHTML = currentHtml;
    decorateEditor(editorRef.current);

    setIsDirty(false);
  }, [currentHtml]);

  // Delegate clicks for asset swap
  const handleClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'IMG' && target.dataset.assetId) {
      e.preventDefault();
      setSwapAssetId(target.dataset.assetId);
    }
  }, []);

  return (
    <div className="flex flex-col gap-3">
      {isDirty && (
        <div className="flex items-center gap-2">
          <Button onClick={handleSave} loading={saving} size="sm">
            Save Changes
          </Button>
          <Button variant="secondary" onClick={handleDiscard} size="sm" disabled={saving}>
            Discard Changes
          </Button>
        </div>
      )}
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        onClick={handleClick}
        className="prose max-w-none rounded-lg border border-slate-200 p-6 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      />
      {swapAssetId && (
        <AssetSwapModal
          currentAssetId={swapAssetId}
          onClose={() => setSwapAssetId(null)}
        />
      )}
    </div>
  );
}
