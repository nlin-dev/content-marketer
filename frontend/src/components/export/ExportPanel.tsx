'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useComplianceStore } from '@/stores/compliance';
import { useContentStore } from '@/stores/content';
import { useProjectStore } from '@/stores/project';
import { exportVersion } from '@/lib/api';

export function ExportPanel() {
  const overallStatus = useComplianceStore((s) => s.overallStatus);
  const currentVersionId = useContentStore((s) => s.currentVersionId);
  const project = useProjectStore((s) => s.project);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{
    html_content: string;
    exported_at: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const allPassed = overallStatus === 'pass';
  const hasVersion = !!currentVersionId;

  async function handleExport() {
    if (!currentVersionId) return;
    setExporting(true);
    setError(null);
    try {
      const result = await exportVersion(currentVersionId);
      setExportResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  }

  function handleCopyHtml() {
    if (!exportResult) return;
    navigator.clipboard.writeText(exportResult.html_content).catch(() => {});
  }

  if (exportResult) {
    return (
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="rounded-lg border border-green-200 bg-green-50 p-6 text-center">
          <div className="text-2xl mb-2">&#10003;</div>
          <h2 className="text-xl font-semibold text-green-900">Content Exported</h2>
          <p className="text-sm text-green-700 mt-1">
            {project?.name} — exported {new Date(exportResult.exported_at).toLocaleString()}
          </p>
        </div>

        <div className="space-y-3">
          <Button onClick={handleCopyHtml} className="w-full">
            Copy HTML to Clipboard
          </Button>
        </div>

        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-medium text-gray-700 mb-2">HTML Preview</h3>
          <div className="max-h-64 overflow-y-auto rounded bg-gray-50 p-3 text-xs font-mono text-gray-600 whitespace-pre-wrap break-all">
            {exportResult.html_content}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Export Content</h2>
        <p className="text-sm text-gray-500 mt-1">
          Export the current version for use in your campaign.
        </p>
      </div>

      <div className="rounded-lg border p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Compliance Status</span>
          {overallStatus ? (
            <Badge color={allPassed ? 'green' : 'red'}>
              {allPassed ? 'All Checks Passed' : 'Issues Found'}
            </Badge>
          ) : (
            <Badge color="gray">Not Checked</Badge>
          )}
        </div>

        {!allPassed && overallStatus && (
          <p className="text-sm text-red-600">
            All compliance checks must pass before export. Go back to Review to resolve issues.
          </p>
        )}

        {!hasVersion && (
          <p className="text-sm text-amber-600">
            No content version available. Generate content first.
          </p>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Button
        onClick={handleExport}
        disabled={!allPassed || !hasVersion || exporting}
        className="w-full"
      >
        {exporting ? 'Exporting...' : 'Export Content'}
      </Button>
    </div>
  );
}
