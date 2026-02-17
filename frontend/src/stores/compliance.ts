import { create } from 'zustand';
import type { ComplianceCheckResponse, ComplianceReportResponse, ComplianceStatus } from '@/types';

interface ComplianceState {
  checks: ComplianceCheckResponse[];
  overallStatus: ComplianceStatus | null;
  setReport: (report: ComplianceReportResponse) => void;
  clearCompliance: () => void;
}

export const useComplianceStore = create<ComplianceState>((set) => ({
  checks: [],
  overallStatus: null,
  setReport: (report) =>
    set({ checks: report.checks, overallStatus: report.overall_status }),
  clearCompliance: () => set({ checks: [], overallStatus: null }),
}));
