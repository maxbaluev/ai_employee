import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { loadMarkdown } from '@/lib/loadMarkdown';

export default async function DocsPage() {
  const markdown = await loadMarkdown('README.md');

  return (
    <article className="docs-markdown">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </article>
  );
}
