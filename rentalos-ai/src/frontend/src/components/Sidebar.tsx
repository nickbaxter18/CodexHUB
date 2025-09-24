interface SidebarProps {
  roles: string[]
}

const modules = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    roles: ['manager', 'owner', 'tenant'],
  },
  { key: 'pricing', label: 'Pricing', roles: ['manager', 'owner'] },
  {
    key: 'maintenance',
    label: 'Maintenance',
    roles: ['manager', 'technician'],
  },
  { key: 'esg', label: 'ESG', roles: ['sustainability'] },
]

const Sidebar = ({ roles }: SidebarProps) => {
  const visibleModules = modules.filter((module) =>
    module.roles.some((role) => roles.includes(role)),
  )
  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 p-4 space-y-3">
      {visibleModules.map((module) => (
        <div
          key={module.key}
          className="rounded-lg bg-slate-800/70 px-3 py-2 text-sm font-medium"
        >
          {module.label}
        </div>
      ))}
    </aside>
  )
}

export default Sidebar
