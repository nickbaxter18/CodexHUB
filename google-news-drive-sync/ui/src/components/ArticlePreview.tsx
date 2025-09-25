import { CalendarDaysIcon, LinkIcon } from '@heroicons/react/24/outline';
import type { Article } from '../App';

interface Props {
  article: Article;
}

function formatDate(value?: string | null) {
  if (!value) return 'Unknown';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export default function ArticlePreview({ article }: Props) {
  return (
    <article className="group relative flex flex-col gap-3 rounded-2xl border border-slate-700/40 bg-slate-900/60 p-5 shadow-xl backdrop-blur transition hover:border-sky-400/70 hover:bg-slate-900/80">
      <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
        <span>{article.source ?? 'Unknown source'}</span>
        <span className="inline-flex items-center gap-1">
          <CalendarDaysIcon className="h-4 w-4" aria-hidden="true" />
          {formatDate(article.published_at)}
        </span>
      </div>

      <h2 className="text-xl font-semibold text-slate-100 group-hover:text-sky-200">
        {article.title}
      </h2>

      {article.description && <p className="text-sm text-slate-300">{article.description}</p>}

      <a
        className="inline-flex items-center gap-2 self-start rounded-full border border-sky-500/60 px-4 py-2 text-sm font-medium text-sky-200 transition hover:border-sky-300 hover:text-sky-100"
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
      >
        <LinkIcon className="h-4 w-4" aria-hidden="true" />
        Read source
      </a>
    </article>
  );
}
