import { useCallback } from 'react';
import { getVersions } from '@/lib/api';
import { useContentStore } from '@/stores/content';
import type { VersionSummary } from '@/types';

export function useRefreshVersions(projectId: string | undefined) {
  const setCurrentHtml = useContentStore((s) => s.setCurrentHtml);
  const setCurrentVersionId = useContentStore((s) => s.setCurrentVersionId);
  const setVersions = useContentStore((s) => s.setVersions);

  const refreshAfterEdit = useCallback(
    async (html: string, versionId: string) => {
      setCurrentHtml(html);
      setCurrentVersionId(versionId);
      if (projectId) {
        const versions = await getVersions(projectId);
        setVersions(versions);
      }
    },
    [projectId, setCurrentHtml, setCurrentVersionId, setVersions],
  );

  const refreshVersionList = useCallback(async (): Promise<VersionSummary[]> => {
    if (!projectId) return [];
    const versions = await getVersions(projectId);
    setVersions(versions);
    return versions;
  }, [projectId, setVersions]);

  return { refreshAfterEdit, refreshVersionList };
}
