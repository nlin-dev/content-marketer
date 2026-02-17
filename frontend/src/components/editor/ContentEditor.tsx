'use client';

import { useCallback, useRef } from 'react';
import DOMPurify from 'dompurify';
import { Button } from '@/components/ui/Button';
import { Spinner } from '@/components/ui/Spinner';
import { AiEditBar } from './AiEditBar';
import { DirectEditor } from './DirectEditor';
import { useContentStore } from '@/stores/content';
import { useClaimsStore } from '@/stores/claims';
import { useAssetsStore } from '@/stores/assets';
import { useProjectStore } from '@/stores/project';
import { useUiStore } from '@/stores/ui';
import { streamGenerate } from '@/lib/api';
import { useRefreshVersions } from '@/hooks/useRefreshVersions';

export function ContentEditor() {
  const project = useProjectStore((s) => s.project);
  const currentHtml = useContentStore((s) => s.currentHtml);
  const streaming = useContentStore((s) => s.streaming);
  const setCurrentHtml = useContentStore((s) => s.setCurrentHtml);
  const appendToken = useContentStore((s) => s.appendToken);
  const setStreaming = useContentStore((s) => s.setStreaming);
  const selectedClaims = useClaimsStore((s) => s.selected);
  const selectedAssets = useAssetsStore((s) => s.selected);
  const setError = useUiStore((s) => s.setError);
  const { refreshVersionList } = useRefreshVersions(project?.id);
  const abortRef = useRef<AbortController | null>(null);

  const handleGenerate = useCallback(() => {
    if (!project) return;
    const claimIds = selectedClaims.map((c) => c.id);
    const assetIds = selectedAssets.map((a) => a.id);
    if (claimIds.length === 0) {
      setError('Select at least one claim before generating');
      return;
    }

    setCurrentHtml('');
    setStreaming(true);

    abortRef.current = streamGenerate(
      { claim_ids: claimIds, asset_ids: assetIds },
      project.id,
      (token) => appendToken(token),
      async (fullHtml) => {
        setCurrentHtml(fullHtml);
        setStreaming(false);
        try {
          const versions = await refreshVersionList();
          if (versions.length > 0) {
            useContentStore.getState().setCurrentVersionId(versions[versions.length - 1].id);
          }
        } catch {
          // versions fetch is non-critical
        }
      },
      (error) => {
        setError(error);
        setStreaming(false);
      },
    );
  }, [project, selectedClaims, selectedAssets, setCurrentHtml, appendToken, setStreaming, refreshVersionList, setError]);

  const hasContent = currentHtml.length > 0;

  // No content yet — show generate button
  if (!hasContent && !streaming) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed border-slate-300 p-12">
        <p className="text-sm text-slate-500">
          Select claims and assets, then generate content.
        </p>
        <Button onClick={handleGenerate} disabled={selectedClaims.length === 0}>
          Generate Content
        </Button>
      </div>
    );
  }

  // Streaming — show read-only preview
  if (streaming && !hasContent) {
    return (
      <div className="flex items-center justify-center gap-2 p-12">
        <Spinner size="md" />
        <span className="text-sm text-slate-500">Generating content...</span>
      </div>
    );
  }

  if (streaming && hasContent) {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm text-primary-600">
          <Spinner size="sm" />
          Generating...
        </div>
        <div
          className="prose max-w-none rounded-lg border border-slate-200 p-6"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(currentHtml, { ALLOW_DATA_ATTR: true }) }}
        />
      </div>
    );
  }

  // Content ready — show editor
  return (
    <div className="flex flex-col gap-4">
      <AiEditBar />
      <DirectEditor />
    </div>
  );
}
