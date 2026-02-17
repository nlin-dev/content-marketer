import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Bootstrap } from './Bootstrap';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'Content Marketer',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Bootstrap>{children}</Bootstrap>
      </body>
    </html>
  );
}
