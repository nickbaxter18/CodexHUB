interface NotificationBellProps {
  count: number
}

const NotificationBell = ({ count }: NotificationBellProps) => (
  <button className="relative inline-flex items-center justify-center rounded-full bg-slate-800 px-4 py-2">
    <span className="text-sm">Alerts</span>
    <span className="absolute -top-2 -right-2 rounded-full bg-emerald-500 px-2 text-xs font-semibold text-black">
      {count}
    </span>
  </button>
)

export default NotificationBell
