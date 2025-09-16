import { render, screen } from '@testing-library/react'
import userEvent, { PointerEventsCheckLevel } from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ModeSelector } from '../mode-selector'

describe('ModeSelector', () => {
  it('does not render the Fabric option when the feature is disabled', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    const onChange = vi.fn()

    render(
      <ModeSelector value="auto" onChange={onChange} disabled={false} fabricAgentEnabled={false} />,
    )

    await user.click(screen.getByRole('button', { name: /Auto Route/i }))

    await screen.findByRole('menuitem', { name: 'Databricks Genie' })
    expect(screen.queryByRole('menuitem', { name: 'Fabric Data Agent' })).not.toBeInTheDocument()
  })

  it('allows selecting the Fabric agent when enabled', async () => {
    const user = userEvent.setup({ pointerEventsCheck: PointerEventsCheckLevel.Never })
    const onChange = vi.fn()

    render(
      <ModeSelector value="auto" onChange={onChange} disabled={false} fabricAgentEnabled={true} />,
    )

    await user.click(screen.getByRole('button', { name: /Auto Route/i }))

    const fabricOption = await screen.findByRole('menuitem', { name: 'Fabric Data Agent' })
    await user.click(fabricOption)

    expect(onChange).toHaveBeenCalledWith('fabric')
  })
})
