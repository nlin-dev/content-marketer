'use client';

import { useState } from 'react';
import { useComplianceStore } from '@/stores/compliance';
import { COMPLIANCE_STATUS_CONFIG } from '@/lib/constants';
import { Badge } from '@/components/ui/Badge';
import type { ComplianceCheckResponse } from '@/types';

function CheckItem({ check }: { check: ComplianceCheckResponse }) {
  const [expanded, setExpanded] = useState(false);
  const config = COMPLIANCE_STATUS_CONFIG[check.status];

  return (
    <div className="border border-slate-200 rounded-md">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left cursor-pointer hover:bg-slate-50"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-sm font-medium text-slate-900">
          {check.check_name}
        </span>
        <div className="flex items-center gap-2">
          <Badge color={config.color as 'green' | 'red' | 'amber'}>
            {config.label}
          </Badge>
          <svg
            className={`h-4 w-4 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>
      {expanded && check.details && (
        <div className="border-t border-slate-200 px-4 py-3 text-sm text-slate-600">
          {check.details.detail != null && (
            <p>{String(check.details.detail)}</p>
          )}
          {check.details.claim != null && (
            <p className="mt-2 italic text-slate-500">
              {'Referenced claim: '}{String(check.details.claim)}
            </p>
          )}
          {check.details.text != null && (
            <p className="mt-2 italic text-slate-500">
              {'Referenced text: '}{String(check.details.text)}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export function CompliancePanel() {
  const checks = useComplianceStore((s) => s.checks);
  const overallStatus = useComplianceStore((s) => s.overallStatus);

  const allPass = overallStatus === 'pass';
  const hasFailures = checks.some((c) => c.status === 'fail');

  return (
    <div className="space-y-4">
      {/* Summary banner */}
      <div
        className={`rounded-md px-4 py-3 text-sm font-medium ${
          allPass
            ? 'bg-green-100 text-green-800'
            : 'bg-red-100 text-red-800'
        }`}
      >
        {allPass ? 'All checks passed' : 'Compliance issues found'}
      </div>

      {/* Individual checks */}
      <div className="space-y-2">
        {checks.map((check) => (
          <CheckItem key={check.id} check={check} />
        ))}
      </div>

      {/* Export blocked warning */}
      {hasFailures && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          Export is blocked until all compliance checks pass.
        </div>
      )}
    </div>
  );
}
