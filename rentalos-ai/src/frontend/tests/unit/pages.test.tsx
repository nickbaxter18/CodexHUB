import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import Dashboard from '../../src/pages/Dashboard'
import PricingPage from '../../src/pages/PricingPage'

it('renders dashboard metrics', () => {
  const { getAllByText } = render(<Dashboard />)
  expect(getAllByText(/occupancy/i)).not.toHaveLength(0)
})

it('renders pricing description', () => {
  const { getAllByText } = render(<PricingPage />)
  expect(getAllByText(/pricing/i)).not.toHaveLength(0)
})
