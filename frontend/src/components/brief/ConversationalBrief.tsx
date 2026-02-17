'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/Button';
import { useProjectStore } from '@/stores/project';
import { useNavigationStore } from '@/stores/navigation';
import { useUiStore } from '@/stores/ui';
import { updateBrief } from '@/lib/api';

const QUESTIONS = [
  {
    id: 'messaging_priority',
    text: "What's your primary messaging priority?",
    pills: ['Clinical efficacy', 'Safety profile', 'Quality of life', 'Mechanism of action', 'Dosing convenience'],
  },
  {
    id: 'subgroup_focus',
    text: 'Any specific patient subgroup to focus on?',
    pills: ['Previously treated', 'First-line', 'Elderly (65+)', 'All patients'],
  },
  {
    id: 'additional_context',
    text: 'Any additional context for this campaign?',
    pills: null,
  },
] as const;

interface Message {
  role: 'system' | 'user';
  text: string;
}

export function ConversationalBrief() {
  const project = useProjectStore((s) => s.project);
  const nextStep = useNavigationStore((s) => s.nextStep);

  const [messages, setMessages] = useState<Message[]>([
    { role: 'system', text: QUESTIONS[0].text },
  ]);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [freeText, setFreeText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [advancing, setAdvancing] = useState(false);

  const advance = useCallback(
    async (questionIndex: number, answer: string) => {
      if (advancing) return;
      setAdvancing(true);
      const q = QUESTIONS[questionIndex];
      const newAnswers = { ...answers, [q.id]: answer };
      setAnswers(newAnswers);

      const newMessages: Message[] = [
        ...messages,
        { role: 'user', text: answer },
      ];

      const nextQ = questionIndex + 1;
      if (nextQ < QUESTIONS.length) {
        newMessages.push({ role: 'system', text: QUESTIONS[nextQ].text });
        setMessages(newMessages);
        setCurrentQ(nextQ);
        setAdvancing(false);
      } else {
        setMessages(newMessages);
        setCurrentQ(QUESTIONS.length);
        setSubmitting(true);
        try {
          await updateBrief(project!.id, { brief_responses: newAnswers });
          nextStep();
        } catch (err) {
          useUiStore.getState().setError(err instanceof Error ? err.message : 'Failed to save brief');
          setSubmitting(false);
          setAdvancing(false);
        }
      }
    },
    [answers, messages, project, nextStep, advancing],
  );

  const handlePill = (pill: string) => advance(currentQ, pill);

  const handleFreeText = () => {
    const text = freeText.trim() || '';
    advance(currentQ, text);
  };

  const handleSkip = () => advance(currentQ, '');

  const currentQuestion = currentQ < QUESTIONS.length ? QUESTIONS[currentQ] : null;

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto">
      <div className="flex-1 overflow-y-auto space-y-4 py-6">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              msg.role === 'system'
                ? 'flex justify-start'
                : 'flex justify-end'
            }
          >
            <div
              className={
                msg.role === 'system'
                  ? 'bg-slate-100 text-slate-900 rounded-2xl rounded-tl-sm px-4 py-3 max-w-[80%] text-sm'
                  : 'bg-primary-500 text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[80%] text-sm'
              }
            >
              {msg.text || <span className="italic text-slate-400">Skipped</span>}
            </div>
          </div>
        ))}
      </div>

      {currentQuestion && !submitting && (
        <div className="border-t border-slate-200 bg-white py-4 space-y-3">
          {currentQuestion.pills ? (
            <div className="flex flex-wrap gap-2">
              {currentQuestion.pills.map((pill) => (
                <button
                  key={pill}
                  onClick={() => handlePill(pill)}
                  disabled={advancing || submitting}
                  className="px-4 py-2 rounded-full border border-slate-200 text-sm font-medium cursor-pointer hover:bg-primary-50 hover:border-primary-300 hover:text-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {pill}
                </button>
              ))}
            </div>
          ) : (
            <div className="flex gap-2">
              <input
                type="text"
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleFreeText();
                }}
                placeholder="Type your response..."
                className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
              <Button onClick={handleFreeText} size="sm">
                Send
              </Button>
              <Button onClick={handleSkip} variant="ghost" size="sm">
                Skip
              </Button>
            </div>
          )}
        </div>
      )}

      {submitting && (
        <div className="border-t border-slate-200 bg-white py-4 text-center text-sm text-slate-500">
          Saving brief...
        </div>
      )}
    </div>
  );
}
