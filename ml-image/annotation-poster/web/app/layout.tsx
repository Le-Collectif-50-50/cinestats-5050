import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ML-image · Annotation des affiches',
  robots: { index: false, follow: false },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return <html lang="fr"><body>{children}</body></html>;
}
