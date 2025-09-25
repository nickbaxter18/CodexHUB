import type { Article } from '../App';
import ArticlePreview from './ArticlePreview';

interface Props {
  articles: Article[];
  loading?: boolean;
}

export default function ArticleList({ articles, loading = false }: Props) {
  if (loading) {
    return <p className="text-slate-400">Loading latest headlines…</p>;
  }

  if (!articles.length) {
    return <p className="text-slate-400">No articles matched the current filters.</p>;
  }

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {articles.map((article) => (
        <ArticlePreview key={article.id} article={article} />
      ))}
    </section>
  );
}
