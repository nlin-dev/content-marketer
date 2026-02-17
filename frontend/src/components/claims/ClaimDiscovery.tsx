'use client';

import { useState, useEffect, useMemo } from 'react';
import { ClaimCard } from './ClaimCard';
import { Button } from '@/components/ui/Button';
import { useClaimsStore } from '@/stores/claims';
import { useNavigationStore } from '@/stores/navigation';
import { useUiStore } from '@/stores/ui';
import { getAllClaims, searchClaims } from '@/lib/api';
import { CLAIM_CATEGORY_CONFIG } from '@/lib/constants';
import type { ClaimResponse, ClaimCategory } from '@/types';

export function ClaimDiscovery() {
  const [allClaims, setAllClaims] = useState<ClaimResponse[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const selected = useClaimsStore((s) => s.selected);
  const nextStep = useNavigationStore((s) => s.nextStep);

  useEffect(() => {
    if (!query.trim()) {
      setLoading(true);
      getAllClaims()
        .then(setAllClaims)
        .catch((err) => useUiStore.getState().setError(err instanceof Error ? err.message : 'Failed to load claims'))
        .finally(() => setLoading(false));
      return;
    }
    const timeout = setTimeout(() => {
      searchClaims(query).then((results) => {
        setAllClaims(results.map((r) => r.claim));
      }).catch((err) => useUiStore.getState().setError(err instanceof Error ? err.message : 'Failed to load claims'));
    }, 300);
    return () => clearTimeout(timeout);
  }, [query]);

  const grouped = useMemo(() => {
    const groups: Partial<Record<ClaimCategory, ClaimResponse[]>> = {};
    for (const claim of allClaims) {
      if (!groups[claim.category]) groups[claim.category] = [];
      groups[claim.category]!.push(claim);
    }
    return groups;
  }, [allClaims]);

  const hasEfficacy = selected.some((c) => c.category.startsWith('efficacy'));
  const hasSafety = selected.some((c) => c.category === 'safety');
  const showFairBalance = hasEfficacy && !hasSafety;

  return (
    <div className="flex flex-col h-full">
      <div className="space-y-4 flex-1 overflow-y-auto pb-24">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search claims..."
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />

        {showFairBalance && (
          <div className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
            Fair balance: Consider adding safety claims to balance efficacy messaging.
          </div>
        )}

        {loading ? (
          <p className="text-sm text-slate-500">Loading claims...</p>
        ) : (
          Object.entries(grouped).map(([category, claims]) => {
            const config = CLAIM_CATEGORY_CONFIG[category as ClaimCategory];
            return (
              <div key={category}>
                <h3 className="text-sm font-semibold text-slate-700 mb-2">
                  {config?.label ?? category}
                </h3>
                <div className="space-y-2">
                  {claims!.map((claim) => (
                    <ClaimCard key={claim.id} claim={claim} />
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 px-6 py-3 flex items-center justify-between z-10 shadow-[0_-1px_3px_rgba(0,0,0,0.05)]">
        <span className="text-sm text-slate-600">
          {selected.length} claim{selected.length !== 1 ? 's' : ''} selected
        </span>
        <Button
          onClick={nextStep}
          disabled={selected.length === 0}
        >
          Continue to Assets
        </Button>
      </div>
    </div>
  );
}
