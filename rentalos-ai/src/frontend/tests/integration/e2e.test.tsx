import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'
import App from '../../src/App'

describe('App integration', () => {
  it('renders command center card', () => {
    const { getByText } = render(<App />)
    expect(getByText(/command center/i)).toBeInTheDocument()
  })
})
