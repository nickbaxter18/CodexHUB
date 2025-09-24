import Card from '../components/Card'
import ChartWrapper from '../components/ChartWrapper'

const fairnessMetrics = [
  {
    label: 'Pricing parity',
    value: '1.02×',
    detail: 'Within fairness guardrail',
  },
  {
    label: 'Screening variance',
    value: '0.3%',
    detail: 'No disparate impact detected',
  },
]

const pluginStatuses = [
  {
    name: 'Equitable Pricing',
    status: 'active',
    description: 'Explains AI recommendations',
  },
  {
    name: 'Energy Optimizer',
    status: 'standby',
    description: 'Awaiting carbon market sync',
  },
]

const Dashboard = () => (
  <div className="grid gap-4 xl:grid-cols-3 lg:grid-cols-2">
    <ChartWrapper title="Occupancy">
      <p className="text-sm text-slate-300">
        98% occupancy across smart rentals.
      </p>
    </ChartWrapper>
    <ChartWrapper title="Energy Savings">
      <p className="text-sm text-slate-300">
        12% reduction via energy marketplace.
      </p>
    </ChartWrapper>
    <ChartWrapper title="Alert Latency">
      <p className="text-sm text-slate-300">
        Realtime streams stabilized at 45ms response.
      </p>
    </ChartWrapper>
    <Card
      title="Fairness Watch"
      subtitle="Live ethics telemetry for pricing and screening"
    >
      <div className="space-y-3">
        {fairnessMetrics.map((metric) => (
          <div
            key={metric.label}
            className="flex items-center justify-between rounded-xl bg-emerald-500/10 px-3 py-2"
          >
            <span className="text-sm font-medium text-emerald-200">
              {metric.label}
            </span>
            <div className="text-right">
              <p className="font-semibold text-emerald-100">{metric.value}</p>
              <p className="text-xs text-emerald-200/70">{metric.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
    <Card
      title="Plugin Marketplace"
      subtitle="Sandboxed integrations monitored in realtime"
    >
      <ul className="space-y-2 text-sm text-slate-200">
        {pluginStatuses.map((plugin) => (
          <li
            key={plugin.name}
            className="flex items-start justify-between rounded-xl bg-slate-800/70 px-3 py-2"
          >
            <div>
              <p className="font-semibold">{plugin.name}</p>
              <p className="text-xs text-slate-400">{plugin.description}</p>
            </div>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                plugin.status === 'active'
                  ? 'bg-emerald-500/20 text-emerald-200'
                  : 'bg-amber-500/10 text-amber-200'
              }`}
            >
              {plugin.status}
            </span>
          </li>
        ))}
      </ul>
    </Card>
    <Card
      title="Resilience Center"
      subtitle="Autoscaling, alerting, and recovery metrics"
    >
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl bg-slate-800/70 p-3 text-sm">
          <p className="font-semibold text-slate-100">Auto-healing</p>
          <p className="text-xs text-slate-400">
            4 self-healed incidents this week.
          </p>
        </div>
        <div className="rounded-xl bg-slate-800/70 p-3 text-sm">
          <p className="font-semibold text-slate-100">Carbon footprint</p>
          <p className="text-xs text-slate-400">
            0.6 tCO₂e saved via demand shaping.
          </p>
        </div>
      </div>
    </Card>
  </div>
)

export default Dashboard
