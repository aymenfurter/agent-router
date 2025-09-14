import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    // Just verify the app renders without throwing
    expect(document.body).toBeInTheDocument()
  })
})
