'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { StepIndicator } from '@/components/StepIndicator';
import { useProjectStore } from '@/stores/project';
import { useNavigationStore } from '@/stores/navigation';
import { useClaimsStore } from '@/stores/claims';
import { useAssetsStore } from '@/stores/assets';
import { useContentStore } from '@/stores/content';
import { useComplianceStore } from '@/stores/compliance';
import { getProject } from '@/lib/api';
import { STEPS } from '@/lib/constants';
import { Spinner } from '@/components/ui/Spinner';
import { ConversationalBrief } from '@/components/brief/ConversationalBrief';
import { ClaimDiscovery } from '@/components/claims/ClaimDiscovery';
import { AssetPicker } from '@/components/assets/AssetPicker';
import { ContentEditor } from '@/components/editor/ContentEditor';
import { ExportPanel } from '@/components/export/ExportPanel';
import { CompliancePanel } from '@/components/review/CompliancePanel';
import { VersionTimeline } from '@/components/review/VersionTimeline';
import { CommentThread } from '@/components/review/CommentThread';

const STEP_COMPONENTS: Record<string, React.ComponentType> = {
  brief: ConversationalBrief,
  claims: ClaimDiscovery,
  assets: AssetPicker,
  generate: ContentEditor,
  review: ContentEditor,
  export: ExportPanel,
};

function SidePanel({ stepKey, projectId }: { stepKey: string; projectId: string }) {
  if (stepKey === 'generate' || stepKey === 'review') {
    return (
      <div className="space-y-6">
        <CompliancePanel />
        <VersionTimeline projectId={projectId} />
        <CommentThread />
      </div>
    );
  }
  return null;
}

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const { project, setProject } = useProjectStore();
  const { currentStep, setStep } = useNavigationStore();
  const resetClaims = useClaimsStore((s) => s.reset);
  const resetAssets = useAssetsStore((s) => s.reset);
  const resetContent = useContentStore((s) => s.reset);
  const resetCompliance = useComplianceStore((s) => s.reset);

  useEffect(() => {
    setStep(0);
    resetClaims();
    resetAssets();
    resetContent();
    resetCompliance();
    setProject(null);

    getProject(id).then(setProject).catch(console.error);
  }, [id, setStep, setProject, resetClaims, resetAssets, resetContent, resetCompliance]);

  const stepKey = STEPS[currentStep].key;

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-52px)]">
        <Spinner />
      </div>
    );
  }

  const showSidePanel = stepKey === 'generate' || stepKey === 'review';

  return (
    <div className="flex flex-col h-[calc(100vh-52px)]">
      <div className="border-b bg-white">
        <div className="flex items-center justify-between px-6 py-2">
          <h1 className="text-lg font-semibold text-navy-900">{project.name}</h1>
        </div>
        <StepIndicator />
      </div>

      <div className="flex flex-1 overflow-hidden">
        <main className="flex-1 overflow-y-auto p-6">
          {(() => { const StepComponent = STEP_COMPONENTS[stepKey]; return StepComponent ? <StepComponent /> : null; })()}
        </main>
        {showSidePanel && (
          <aside className="w-96 border-l overflow-y-auto p-4 bg-gray-50">
            <SidePanel stepKey={stepKey} projectId={id} />
          </aside>
        )}
      </div>
    </div>
  );
}
