'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { createProject } from '@/lib/api';
import { AUDIENCE_LABELS, GOAL_LABELS, TONE_LABELS } from '@/lib/constants';
import type { Audience, Goal, Tone } from '@/types';

function toOptions(labels: Record<string, string>) {
  return Object.entries(labels).map(([value, label]) => ({ value, label }));
}

export default function HomePage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [audience, setAudience] = useState<Audience>('hcp');
  const [goal, setGoal] = useState<Goal>('awareness');
  const [tone, setTone] = useState<Tone>('professional');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError('');
    try {
      const project = await createProject({
        name: name.trim(),
        content_type: 'email',
        audience,
        goal,
        tone,
      });
      router.push(`/project/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-52px)]">
      <Card className="w-full max-w-lg">
        <h1 className="text-xl font-semibold text-slate-900">New Project</h1>
        <p className="mt-1 text-sm text-slate-500">Create a new email campaign to get started.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <Input
            label="Project Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Q1 HCP awareness campaign"
            required
          />

          <Select
            label="Audience"
            options={toOptions(AUDIENCE_LABELS)}
            value={audience}
            onChange={(v) => setAudience(v as Audience)}
          />

          <Select
            label="Campaign Goal"
            options={toOptions(GOAL_LABELS)}
            value={goal}
            onChange={(v) => setGoal(v as Goal)}
          />

          <Select
            label="Tone"
            options={toOptions(TONE_LABELS)}
            value={tone}
            onChange={(v) => setTone(v as Tone)}
          />

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <Button type="submit" loading={loading} className="w-full">
            Create Project
          </Button>
        </form>
      </Card>
    </div>
  );
}
