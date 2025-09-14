// localStorage utilities for conversation management
export interface ConversationEntry {
  id: string
  title: string
  thread_id: string
  last_query: string
  last_response: string
  message_count: number
  timestamp: number
  agent_type?: 'fabric' | 'rag' | 'web' | 'redirect' | 'genie' | 'auto'
}

export const loadConversations = (): ConversationEntry[] => {
  try {
    const saved = localStorage.getItem('ai-conversations')
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (error) {
    console.warn('Failed to load conversations from localStorage:', error)
  }
  return []
}

export const saveConversations = (conversations: ConversationEntry[]): void => {
  try {
    localStorage.setItem('ai-conversations', JSON.stringify(conversations))
  } catch (error) {
    console.warn('Failed to save conversations to localStorage:', error)
  }
}

export const clearAllConversations = (): void => {
  try {
    localStorage.removeItem('ai-conversations')
  } catch (error) {
    console.warn('Failed to clear conversations from localStorage:', error)
  }
}

export const createConversation = (
  query: string,
  response: string,
  threadId: string,
  agentType?: 'fabric' | 'rag' | 'web' | 'genie' | 'auto'
): ConversationEntry => {
  const title = query.length > 50 ? query.substring(0, 50) + '...' : query
  return {
    id: Date.now().toString(),
    title: title,
    thread_id: threadId,
    last_query: query,
    last_response: response,
    message_count: 2,
    timestamp: Date.now(),
    agent_type: agentType || 'auto'
  }
}

export const updateConversation = (
  conversation: ConversationEntry,
  query: string,
  response: string,
  agentType?: 'fabric' | 'rag' | 'web' | 'genie' | 'auto'
): ConversationEntry => {
  return {
    ...conversation,
    last_query: query,
    last_response: response,
    message_count: conversation.message_count + 2,
    timestamp: Date.now(),
    agent_type: agentType || conversation.agent_type
  }
}