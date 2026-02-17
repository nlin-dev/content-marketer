'use client';

import { Card } from '@/components/ui/Card';

export default function HomePage() {
  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-52px)]">
      <Card className="max-w-md text-center">
        <h1 className="text-2xl font-semibold text-navy-900">
          Welcome to Content Marketer
        </h1>
        <p className="mt-2 text-gray-600">
          Generate compliant pharmaceutical content from pre-approved claims.
        </p>
      </Card>
    </div>
  );
}
