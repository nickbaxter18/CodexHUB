import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import NavBar from '../../src/components/NavBar'
import Sidebar from '../../src/components/Sidebar'

it('renders navbar title', () => {
  const { getByText } = render(<NavBar title="RentalOS" />)
  expect(getByText('RentalOS')).toBeInTheDocument()
})

it('filters sidebar modules by role', () => {
  const { queryByText } = render(<Sidebar roles={['sustainability']} />)
  expect(queryByText('ESG')).toBeInTheDocument()
  expect(queryByText('Fairness & Ethics')).toBeInTheDocument()
  expect(queryByText('Pricing')).toBeNull()
})
