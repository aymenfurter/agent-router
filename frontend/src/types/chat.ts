export type AgentIdentifier = 'purview' | 'fabric' | 'rag' | 'web' | 'redirect' | 'genie'

export type ChatMessageType = 'user' | 'agent' | 'system'

export type SelectedMode = 'auto' | 'fabric' | 'rag' | 'web' | 'genie'

export interface ChatMessage {
  id: string
  type: ChatMessageType
  content: string
  timestamp: number
  agent?: AgentIdentifier
  isTyping?: boolean
}

export interface ConversationEntry {
  id: string
  title: string
  thread_id: string
  last_query: string
  last_response: string
  message_count: number
  timestamp: number
  agent_type?: Exclude<AgentIdentifier, 'purview'> | 'auto'
}

export type AppState = 'idle' | 'analyzing' | 'processing'
