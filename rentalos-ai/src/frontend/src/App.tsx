import { useMemo } from 'react'
import NavBar from './components/NavBar'
import Sidebar from './components/Sidebar'
import Card from './components/Card'
import NotificationBell from './components/NotificationBell'
import Dashboard from './pages/Dashboard'

const App = () => {
  const userRoles = useMemo(() => ['manager', 'sustainability'], [])

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <NavBar title="RentalOS-AI" rightSlot={<NotificationBell count={3} />} />
      <div className="flex">
        <Sidebar roles={userRoles} />
        <main className="flex-1 p-6 space-y-6">
          <Card title="Command Center" subtitle="Live portfolio overview">
            <Dashboard />
          </Card>
        </main>
      </div>
    </div>
  )
}

export default App
