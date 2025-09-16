import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'

import { useIsMobile } from '../use-mobile'

describe('useIsMobile', () => {
  beforeEach(() => {
    mediaQueryLists.clear()
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 500 })
  })

  it('returns true when the viewport is below the mobile breakpoint', () => {
    const { result } = renderHook(() => useIsMobile())
    expect(result.current).toBe(true)
  })

  it('reacts to media query changes', () => {
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1024 })
    const { result } = renderHook(() => useIsMobile())

    expect(result.current).toBe(false)

    const mql = window.matchMedia('(max-width: 767px)')

    act(() => {
      Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 640 })
      mql.matches = true
      mql.dispatchEvent(new Event('change'))
    })

    expect(result.current).toBe(true)
  })
})
