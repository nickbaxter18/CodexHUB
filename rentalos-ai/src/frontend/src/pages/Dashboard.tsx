import Card from '../components/Card'
import ChartWrapper from '../components/ChartWrapper'

const Dashboard = () => (
  <div className="grid gap-4 md:grid-cols-2">
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
    <Card title="Community Highlights">
      <p className="text-sm text-slate-300">
        Drone workshops and ESG community meetups scheduled.
      </p>
    </Card>
  </div>
)

export default Dashboard
