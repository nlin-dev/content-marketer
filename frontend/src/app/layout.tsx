import type { Metadata } from 'next';
import { Figtree } from 'next/font/google';
import { Bootstrap } from './Bootstrap';
import './globals.css';

const figtree = Figtree({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-figtree',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Content Marketer',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={figtree.variable}>
      <body className="font-sans">
        <Bootstrap>{children}</Bootstrap>
      </body>
    </html>
  );
}
