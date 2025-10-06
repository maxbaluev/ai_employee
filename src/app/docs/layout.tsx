import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Documentation | AI Employee Platform',
  description: 'Rendered documentation sourced from the repository README.',
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="docs-layout">
      <header className="docs-hero">
        <div className="docs-hero__content">
          <div>
            <p className="docs-hero__eyebrow">AI Employee Platform</p>
            <h1 className="docs-hero__title">Documentation</h1>
            <p className="docs-hero__subtitle">This page is sourced directly from README.md.</p>
          </div>
          <Link href="/" className="docs-hero__link">
            ← Back to app
          </Link>
        </div>
      </header>
      <main className="docs-main">{children}</main>
    </div>
  );
}
