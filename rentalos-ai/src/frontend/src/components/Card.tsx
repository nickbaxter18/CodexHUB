import { ReactNode } from 'react'

interface CardProps {
  title: string
  subtitle?: string
  children: ReactNode
}

const Card = ({ title, subtitle, children }: CardProps) => (
  <section className="rounded-2xl bg-slate-900/70 p-6 shadow-xl shadow-slate-950/40">
    <header className="mb-4">
      <h2 className="text-lg font-semibold">{title}</h2>
      {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
    </header>
    <div>{children}</div>
  </section>
)

export default Card
