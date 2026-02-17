'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { useAssetsStore } from '@/stores/assets';
import { useNavigationStore } from '@/stores/navigation';
import { useUiStore } from '@/stores/ui';
import { getAssets } from '@/lib/api';
import type { AssetResponse } from '@/types';
import { cn } from '@/lib/utils';

const ASSET_TYPE_OPTIONS = ['all', 'image', 'video', 'document', 'infographic'] as const;

export function AssetPicker() {
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const available = useAssetsStore((s) => s.available);
  const setAvailable = useAssetsStore((s) => s.setAvailable);
  const selected = useAssetsStore((s) => s.selected);
  const addSelected = useAssetsStore((s) => s.addSelected);
  const removeSelected = useAssetsStore((s) => s.removeSelected);
  const nextStep = useNavigationStore((s) => s.nextStep);

  useEffect(() => {
    const filter = typeFilter === 'all' ? undefined : typeFilter;
    setLoading(true);
    getAssets(filter)
      .then(setAvailable)
      .catch((err) => useUiStore.getState().setError(err instanceof Error ? err.message : 'Failed to load assets'))
      .finally(() => setLoading(false));
  }, [typeFilter, setAvailable]);

  const toggle = (asset: AssetResponse) => {
    if (selected.some((a) => a.id === asset.id)) {
      removeSelected(asset.id);
    } else {
      addSelected(asset);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="space-y-4 flex-1 overflow-y-auto pb-24">
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-md border border-slate-300 px-3 py-2 text-sm cursor-pointer focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        >
          {ASSET_TYPE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt === 'all' ? 'All types' : opt.charAt(0).toUpperCase() + opt.slice(1)}
            </option>
          ))}
        </select>

        {loading ? (
          <p className="text-sm text-slate-500">Loading assets...</p>
        ) : available.length === 0 ? (
          <p className="text-sm text-slate-500">No assets found.</p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {available.map((asset) => {
              const isSelected = selected.some((a) => a.id === asset.id);
              return (
                <Card
                  key={asset.id}
                  padding={false}
                  className={cn(
                    'relative cursor-pointer overflow-hidden transition-colors',
                    isSelected && 'ring-2 ring-primary-500',
                  )}
                >
                  <button
                    onClick={() => toggle(asset)}
                    className="w-full text-left"
                  >
                    <div className="aspect-video bg-slate-100 flex items-center justify-center">
                      {asset.asset_type === 'image' ? (
                        <img
                          src={asset.file_url}
                          alt={asset.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-slate-400 text-xs uppercase">
                          {asset.asset_type}
                        </span>
                      )}
                    </div>
                    <div className="p-3 space-y-1">
                      <p className="text-sm font-medium text-slate-900 truncate">
                        {asset.name}
                      </p>
                      <Badge color="gray">{asset.asset_type}</Badge>
                      {isSelected && (
                        <div className="absolute top-2 right-2 w-5 h-5 bg-primary-500 rounded text-white flex items-center justify-center text-xs">
                          &#10003;
                        </div>
                      )}
                    </div>
                  </button>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-6 py-3 flex items-center justify-between z-10 shadow-[0_-1px_3px_rgba(0,0,0,0.05)]">
        <span className="text-sm text-slate-600">
          {selected.length} asset{selected.length !== 1 ? 's' : ''} selected
        </span>
        <Button onClick={nextStep}>
          Generate Content
        </Button>
      </div>
    </div>
  );
}
