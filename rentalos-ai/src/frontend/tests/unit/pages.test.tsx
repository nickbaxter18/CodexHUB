import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import Dashboard from '../../src/pages/Dashboard'
import PluginsPage from '../../src/pages/PluginsPage'
import PricingPage from '../../src/pages/PricingPage'

it('renders dashboard metrics', () => {
  const { getAllByText, getByText } = render(<Dashboard />)
  expect(getAllByText(/occupancy/i)).not.toHaveLength(0)
  expect(getByText(/Fairness Watch/)).toBeInTheDocument()
})

it('renders pricing description', () => {
  const { getAllByText } = render(<PricingPage />)
  expect(getAllByText(/pricing/i)).not.toHaveLength(0)
})

it('renders plugin marketplace cards', () => {
  const { getByText } = render(<PluginsPage />)
  expect(getByText(/Plugin Marketplace/)).toBeInTheDocument()
  expect(getByText(/Equitable Pricing/)).toBeInTheDocument()
})
