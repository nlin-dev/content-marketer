'use client';

import { useState } from 'react';
import { useContentStore } from '@/stores/content';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import * as api from '@/lib/api';
import { formatRelativeTime } from '@/lib/format';

function editTypeBadge(instruction: string | null): { label: string; color: 'blue' | 'purple' | 'green' | 'amber' } {
  if (!instruction) return { label: 'Generated', color: 'green' };
  const lower = instruction.toLowerCase();
  if (lower.startsWith('revert')) return { label: 'Reverted', color: 'amber' };
  if (lower.startsWith('direct:')) return { label: 'Direct Edit', color: 'purple' };
  return { label: 'AI Edit', color: 'blue' };
}

interface VersionTimelineProps {
  projectId: string;
}

export function VersionTimeline({ projectId }: VersionTimelineProps) {
  const versions = useContentStore((s) => s.versions);
  const currentVersionId = useContentStore((s) => s.currentVersionId);
  const setCurrentHtml = useContentStore((s) => s.setCurrentHtml);
  const setVersions = useContentStore((s) => s.setVersions);
  const setCurrentVersionId = useContentStore((s) => s.setCurrentVersionId);
  const [reverting, setReverting] = useState<string | null>(null);

  async function handleRevert(targetVersionId: string) {
    setReverting(targetVersionId);
    try {
      const newVersion = await api.revertVersion(projectId, { target_version_id: targetVersionId });
      setCurrentHtml(newVersion.html_content);
      setCurrentVersionId(newVersion.id);
      const updatedVersions = await api.getVersions(projectId);
      setVersions(updatedVersions);
    } catch {
      // Silently handle - could add error toast later
    } finally {
      setReverting(null);
    }
  }

  return (
    <div className="space-y-0">
      {versions.map((version, idx) => {
        const isCurrent = version.id === currentVersionId;
        const badge = editTypeBadge(version.edit_instruction);
        const isLast = idx === versions.length - 1;

        return (
          <div key={version.id} className="relative flex gap-3 pb-6">
            {/* Vertical line */}
            {!isLast && (
              <div className="absolute left-[7px] top-4 h-full w-0.5 bg-slate-200" />
            )}

            {/* Dot indicator */}
            <div
              className={`relative z-10 mt-1 h-4 w-4 flex-shrink-0 rounded-full border-2 ${
                isCurrent
                  ? 'border-primary-500 bg-primary-500'
                  : 'border-slate-300 bg-white'
              }`}
            />

            {/* Content */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-900">
                  v{version.version_number}
                </span>
                <Badge color={badge.color}>{badge.label}</Badge>
                {isCurrent && (
                  <Badge color="blue">Current</Badge>
                )}
              </div>

              {version.edit_instruction && (
                <p className="mt-1 text-sm text-slate-600 line-clamp-2">
                  {version.edit_instruction}
                </p>
              )}

              <p className="mt-1 text-xs text-slate-400">
                {formatRelativeTime(version.created_at)}
              </p>

              {!isCurrent && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-1 px-0 text-xs text-primary-600 hover:text-primary-700 cursor-pointer"
                  loading={reverting === version.id}
                  onClick={() => handleRevert(version.id)}
                >
                  Revert to this version
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
