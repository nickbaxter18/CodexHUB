import { ReactNode } from 'react'

interface ChartWrapperProps {
  title: string
  children: ReactNode
}

const ChartWrapper = ({ title, children }: ChartWrapperProps) => (
  <div className="rounded-xl border border-slate-800 p-4">
    <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
      {title}
    </h3>
    <div className="min-h-[120px]">{children}</div>
  </div>
)

export default ChartWrapper
