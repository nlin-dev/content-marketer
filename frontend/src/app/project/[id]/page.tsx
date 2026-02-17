'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';
import { StepIndicator } from '@/components/StepIndicator';
import { useProjectStore } from '@/stores/project';
import { useNavigationStore } from '@/stores/navigation';
import { useClaimsStore } from '@/stores/claims';
import { useAssetsStore } from '@/stores/assets';
import { useContentStore } from '@/stores/content';
import { getProject } from '@/lib/api';
import { STEPS } from '@/lib/constants';
import { Spinner } from '@/components/ui/Spinner';

const STEP_COMPONENTS: Record<string, () => React.ReactNode> = {
  brief: () => <Placeholder label="Brief" />,
  claims: () => <Placeholder label="Claims" />,
  assets: () => <Placeholder label="Assets" />,
  generate: () => <Placeholder label="Generate" />,
  review: () => <Placeholder label="Review" />,
  export: () => <Placeholder label="Export" />,
};

function Placeholder({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-gray-400 text-lg">
      {label} step
    </div>
  );
}

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const { project, setProject } = useProjectStore();
  const { currentStep, setStep } = useNavigationStore();

  useEffect(() => {
    // Reset stores to avoid stale state
    setStep(0);
    useClaimsStore.getState().clearSelected();
    useAssetsStore.getState().clearSelected();
    useContentStore.getState().setCurrentHtml('');
    useContentStore.getState().setVersions([]);
    useContentStore.getState().setCurrentVersionId(null);
    setProject(null);

    getProject(id).then(setProject).catch(console.error);
  }, [id, setStep, setProject]);

  const stepKey = STEPS[currentStep].key;

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-52px)]">
        <Spinner />
      </div>
    );
  }

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
          {STEP_COMPONENTS[stepKey]()}
        </main>
        <aside className="w-96 border-l overflow-y-auto p-4 bg-gray-50">
          {/* Side panel — populated in later plans */}
        </aside>
      </div>
    </div>
  );
}
