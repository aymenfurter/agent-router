import '@testing-library/jest-dom/vitest'

const mediaQueryLists = new Map<string, MediaQueryList>()

declare global {
  // eslint-disable-next-line no-var
  var mediaQueryLists: Map<string, MediaQueryList>
  // eslint-disable-next-line no-var
  var $RefreshSig$: <T>(type: T) => T
  // eslint-disable-next-line no-var
  var $RefreshReg$: (...args: unknown[]) => void
}

type Listener = (event: MediaQueryListEvent) => void

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string): MediaQueryList => {
    const existing = mediaQueryLists.get(query)
    if (existing) {
      return existing
    }

    const listeners = new Set<Listener>()
    const mediaQueryList: MediaQueryList = {
      matches: false,
      media: query,
      onchange: null,
      addEventListener: (event, listener) => {
        if (event === 'change') {
          listeners.add(listener as Listener)
        }
      },
      removeEventListener: (event, listener) => {
        if (event === 'change') {
          listeners.delete(listener as Listener)
        }
      },
      dispatchEvent: (event) => {
        listeners.forEach((listener) => listener(event as MediaQueryListEvent))
        return true
      },
      addListener: (listener: Listener) => {
        listeners.add(listener)
      },
      removeListener: (listener: Listener) => {
        listeners.delete(listener)
      },
    } as MediaQueryList

    mediaQueryLists.set(query, mediaQueryList)
    return mediaQueryList
  },
})

globalThis.mediaQueryLists = mediaQueryLists

globalThis.$RefreshSig$ = () => (type) => type
globalThis.$RefreshReg$ = () => {}
