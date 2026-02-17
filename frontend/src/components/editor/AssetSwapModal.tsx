'use client';

import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { useAssetsStore } from '@/stores/assets';
import { useProjectStore } from '@/stores/project';
import { useUiStore } from '@/stores/ui';
import { swapAsset } from '@/lib/api';
import { useRefreshVersions } from '@/hooks/useRefreshVersions';
import { cn } from '@/lib/utils';

interface AssetSwapModalProps {
  currentAssetId: string;
  onClose: () => void;
}

export function AssetSwapModal({ currentAssetId, onClose }: AssetSwapModalProps) {
  const available = useAssetsStore((s) => s.available);
  const project = useProjectStore((s) => s.project);
  const setError = useUiStore((s) => s.setError);
  const { refreshAfterEdit } = useRefreshVersions(project?.id);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [swapping, setSwapping] = useState(false);

  async function handleConfirm() {
    if (!selectedId || !project) return;
    setSwapping(true);
    try {
      const { version } = await swapAsset(project.id, {
        old_asset_id: currentAssetId,
        new_asset_id: selectedId,
      });
      await refreshAfterEdit(version.html_content, version.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Asset swap failed');
    } finally {
      setSwapping(false);
    }
  }

  return (
    <Modal open onClose={onClose} title="Swap Asset" className="max-w-2xl">
      <div className="grid grid-cols-3 gap-3 max-h-80 overflow-y-auto">
        {available.map((asset) => (
          <button
            key={asset.id}
            type="button"
            onClick={() => setSelectedId(asset.id)}
            className={cn(
              'flex flex-col items-center gap-2 rounded-lg border-2 p-3 text-left transition-colors cursor-pointer',
              asset.id === currentAssetId && 'border-green-500 bg-green-50',
              asset.id === selectedId && asset.id !== currentAssetId && 'border-primary-500 bg-primary-50',
              asset.id !== currentAssetId && asset.id !== selectedId && 'border-slate-200 hover:border-slate-300',
            )}
            disabled={asset.id === currentAssetId}
          >
            {asset.asset_type === 'image' ? (
              <img
                src={asset.file_url}
                alt={asset.name}
                className="h-20 w-full rounded object-cover"
              />
            ) : (
              <div className="flex h-20 w-full items-center justify-center rounded bg-slate-100 text-xs text-slate-500">
                {asset.asset_type}
              </div>
            )}
            <span className="w-full truncate text-xs font-medium text-slate-700">
              {asset.name}
            </span>
            {asset.id === currentAssetId && (
              <span className="text-xs text-green-600">Current</span>
            )}
          </button>
        ))}
      </div>
      {available.length === 0 && (
        <p className="text-sm text-slate-500">No assets available.</p>
      )}
      <div className="mt-4 flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose} disabled={swapping}>
          Cancel
        </Button>
        <Button
          onClick={handleConfirm}
          loading={swapping}
          disabled={!selectedId || selectedId === currentAssetId}
        >
          Swap Asset
        </Button>
      </div>
    </Modal>
  );
}
