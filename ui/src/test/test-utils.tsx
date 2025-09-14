import { render, RenderOptions } from '@testing-library/react'
import { ReactElement } from 'react'
import { ErrorBoundary } from 'react-error-boundary'

// Custom render function that includes providers
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => {
    return (
      <ErrorBoundary fallback={<div>Something went wrong</div>}>
        {children}
      </ErrorBoundary>
    )
  }

  return render(ui, { wrapper: Wrapper, ...options })
}

// Mock conversation data for testing
export const mockConversation = {
  id: '1',
  title: 'Test conversation',
  thread_id: 'thread-123',
  last_query: 'Test query',
  last_response: 'Test response',
  message_count: 2,
  timestamp: Date.now(),
  agent_type: 'auto' as const
}

export const mockMessage = {
  id: '1',
  type: 'user' as const,
  content: 'Test message',
  timestamp: Date.now(),
  isTyping: false
}

export const mockAgentMessage = {
  id: '2',
  type: 'agent' as const,
  agent: 'purview' as const,
  content: 'Test agent response',
  timestamp: Date.now(),
  isTyping: false
}

// re-export everything
export * from '@testing-library/react'

// override render method
export { customRender as render }