'use client';

import { STEPS } from '@/lib/constants';
import { useNavigationStore } from '@/stores/navigation';
import { cn } from '@/lib/utils';

export function StepIndicator() {
  const { currentStep, setStep } = useNavigationStore();

  return (
    <nav className="flex items-center justify-center gap-0 px-8 py-3">
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
                'flex items-center gap-2 rounded-full px-1 py-1',
                clickable ? 'cursor-pointer hover:opacity-80' : 'cursor-default',
              )}
            >
              <span
                className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-full text-xs font-medium',
                  completed && 'bg-accent-100 text-accent-700',
                  active && 'bg-primary-500 text-white shadow-sm',
                  !completed && !active && 'bg-slate-100 text-slate-400',
                )}
              >
                {completed ? (
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  i + 1
                )}
              </span>
              <span
                className={cn(
                  'text-sm font-medium',
                  completed && 'text-accent-700',
                  active && 'text-primary-700',
                  !completed && !active && 'text-slate-400',
                )}
              >
                {step.label}
              </span>
            </button>

            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  'mx-2 h-px w-6',
                  i < currentStep ? 'bg-accent-300' : 'bg-slate-200',
                )}
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
