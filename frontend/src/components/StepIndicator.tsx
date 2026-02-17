'use client';

import { STEPS } from '@/lib/constants';
import { useNavigationStore } from '@/stores/navigation';
import { cn } from '@/lib/utils';

export function StepIndicator() {
  const { currentStep, setStep } = useNavigationStore();

  return (
    <nav className="flex items-center justify-center gap-0 px-8 py-4">
      {STEPS.map((step, i) => {
        const completed = i < currentStep;
        const active = i === currentStep;
        const clickable = completed || active;

        return (
          <div key={step.key} className="flex items-center">
            <button
              type="button"
              disabled={!clickable}
              onClick={() => clickable && setStep(i)}
              className={cn(
                'flex items-center gap-2 rounded-full transition-colors',
                clickable ? 'cursor-pointer' : 'cursor-default',
              )}
            >
              <span
                className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors',
                  completed && 'bg-green-100 text-green-700',
                  active && 'bg-blue-600 text-white',
                  !completed && !active && 'bg-gray-100 text-gray-400',
                )}
              >
                {completed ? (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  i + 1
                )}
              </span>
              <span
                className={cn(
                  'text-sm font-medium',
                  completed && 'text-green-700',
                  active && 'text-blue-600',
                  !completed && !active && 'text-gray-400',
                )}
              >
                {step.label}
              </span>
            </button>

            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  'mx-3 h-px w-8',
                  i < currentStep ? 'bg-green-300' : 'bg-gray-200',
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
