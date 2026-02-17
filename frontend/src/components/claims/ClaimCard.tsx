'use client';

import { Badge } from '@/components/ui/Badge';
import { CLAIM_CATEGORY_CONFIG } from '@/lib/constants';
import { useClaimsStore } from '@/stores/claims';
import type { ClaimResponse } from '@/types';
import { cn } from '@/lib/utils';

interface ClaimCardProps {
  claim: ClaimResponse;
}

export function ClaimCard({ claim }: ClaimCardProps) {
  const selected = useClaimsStore((s) => s.selected);
  const addSelected = useClaimsStore((s) => s.addSelected);
  const removeSelected = useClaimsStore((s) => s.removeSelected);

  const isSelected = selected.some((c) => c.id === claim.id);
  const config = CLAIM_CATEGORY_CONFIG[claim.category];

  const toggle = () => {
    if (isSelected) {
      removeSelected(claim.id);
    } else {
      addSelected(claim);
    }
  };

  return (
    <button
      onClick={toggle}
      className={cn(
        'w-full text-left rounded-lg border p-4 transition-colors hover:bg-gray-50',
        isSelected ? 'border-blue-500 bg-blue-50/50' : 'border-gray-200',
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <Badge color={config.color as 'blue'}>{config.label}</Badge>
      </div>
      <p className="text-sm text-gray-900 leading-relaxed">{claim.text}</p>
      {claim.sources.length > 0 && (
        <p className="mt-2 text-xs text-gray-500 truncate">
          Source: {claim.sources[0].source_id}
        </p>
      )}
    </button>
  );
}
