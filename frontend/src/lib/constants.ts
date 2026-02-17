import type {
  ContentType, Audience, Goal, Tone, ClaimCategory, ComplianceStatus,
} from '@/types';

export const CONTENT_TYPE_LABELS: Record<ContentType, string> = {
  email: 'Email',
  banner_ad: 'Banner Ad',
  social_post: 'Social Post',
  website: 'Website',
  brochure: 'Brochure',
};

export const AUDIENCE_LABELS: Record<Audience, string> = {
  hcp: 'Healthcare Professional',
  patient: 'Patient',
  caregiver: 'Caregiver',
  payer: 'Payer',
};

export const GOAL_LABELS: Record<Goal, string> = {
  awareness: 'Awareness',
  education: 'Education',
  conversion: 'Conversion',
  retention: 'Retention',
};

export const TONE_LABELS: Record<Tone, string> = {
  professional: 'Professional',
  empathetic: 'Empathetic',
  urgent: 'Urgent',
  optimistic: 'Optimistic',
};

export const CLAIM_CATEGORY_CONFIG: Record<ClaimCategory, { label: string; color: string }> = {
  efficacy_os: { label: 'Efficacy (OS)', color: 'blue' },
  efficacy_pfs: { label: 'Efficacy (PFS)', color: 'blue' },
  safety: { label: 'Safety', color: 'amber' },
  moa: { label: 'Mechanism of Action', color: 'purple' },
  dosing: { label: 'Dosing', color: 'teal' },
  qol: { label: 'Quality of Life', color: 'green' },
  subgroups: { label: 'Subgroups', color: 'indigo' },
  dcr: { label: 'Disease Control', color: 'cyan' },
  unmet_need: { label: 'Unmet Need', color: 'rose' },
  positioning: { label: 'Positioning', color: 'slate' },
};

export const COMPLIANCE_STATUS_CONFIG: Record<ComplianceStatus, { label: string; color: string }> = {
  pass: { label: 'Pass', color: 'green' },
  fail: { label: 'Fail', color: 'red' },
  warning: { label: 'Warning', color: 'amber' },
};

export const STEPS = [
  { key: 'brief', label: 'Brief' },
  { key: 'claims', label: 'Claims' },
  { key: 'assets', label: 'Assets' },
  { key: 'generate', label: 'Generate' },
  { key: 'review', label: 'Review' },
  { key: 'export', label: 'Export' },
] as const;
