const plugins = [
  {
    name: 'Equitable Pricing',
    version: '1.2.0',
    status: 'active',
    notes: 'Delivers price explanations and fairness telemetry.',
  },
  {
    name: 'Energy Optimizer',
    version: '0.9.1',
    status: 'standby',
    notes: 'Pre-stages bids for the renewable marketplace.',
  },
]

const PluginsPage = () => (
  <div className="space-y-4">
    <header>
      <h2 className="text-lg font-semibold">Plugin Marketplace</h2>
      <p className="text-sm text-slate-300">
        Review sandboxed extensions, verify signatures, and manage rollout
        waves.
      </p>
    </header>
    <div className="grid gap-3 md:grid-cols-2">
      {plugins.map((plugin) => (
        <div
          key={plugin.name}
          className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4"
        >
          <div className="flex items-center justify-between text-sm">
            <div>
              <p className="font-semibold text-slate-100">{plugin.name}</p>
              <p className="text-xs text-slate-400">v{plugin.version}</p>
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
          </div>
          <p className="mt-3 text-xs text-slate-300">{plugin.notes}</p>
        </div>
      ))}
    </div>
  </div>
)
export default PluginsPage
