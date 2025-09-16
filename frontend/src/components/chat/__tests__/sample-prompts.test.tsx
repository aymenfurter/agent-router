import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { SamplePrompts } from '../sample-prompts'

describe('SamplePrompts', () => {
  it('renders the predefined prompts', () => {
    const onSelect = vi.fn()

    render(<SamplePrompts onSelect={onSelect} disabled={false} />)

    const promptButtons = screen.getAllByRole('button')
    expect(promptButtons).toHaveLength(5)
    expect(promptButtons[0]).toHaveTextContent('What is the cost of Microsoft Encarta?')
  })

  it('invokes the callback when a prompt is selected', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()

    render(<SamplePrompts onSelect={onSelect} disabled={false} />)

    const promptButtons = screen.getAllByRole('button', {
      name: 'What is the weather like tomorrow in Madrid?',
    })

    await user.click(promptButtons[promptButtons.length - 1])

    expect(onSelect).toHaveBeenCalledWith('What is the weather like tomorrow in Madrid?')
  })
})
