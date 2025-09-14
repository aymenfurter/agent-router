import { describe, test, expect, beforeEach } from 'vitest'
import {
  loadConversations,
  saveConversations,
  clearAllConversations,
  createConversation,
  updateConversation,
  ConversationEntry
} from './localStorage'

const mockConversation: ConversationEntry = {
  id: '1',
  title: 'Test conversation',
  thread_id: 'thread-123',
  last_query: 'What is the weather like?',
  last_response: 'The weather is sunny.',
  message_count: 2,
  timestamp: Date.now(),
  agent_type: 'web'
}

describe('localStorage utilities', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('loadConversations', () => {
    test('returns empty array when no conversations stored', () => {
      const conversations = loadConversations()
      expect(conversations).toEqual([])
    })

    test('loads conversations from localStorage', () => {
      const testConversations = [mockConversation]
      // Use the mock localStorage correctly
      vi.mocked(localStorage.getItem).mockReturnValue(JSON.stringify(testConversations))

      const conversations = loadConversations()
      expect(conversations).toEqual(testConversations)
    })

    test('returns empty array when localStorage contains invalid JSON', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('invalid json')

      const conversations = loadConversations()
      expect(conversations).toEqual([])
    })

    test('handles localStorage access errors gracefully', () => {
      const originalGetItem = localStorage.getItem
      localStorage.getItem = vi.fn().mockImplementation(() => {
        throw new Error('localStorage access denied')
      })

      const conversations = loadConversations()
      expect(conversations).toEqual([])

      localStorage.getItem = originalGetItem
    })
  })

  describe('saveConversations', () => {
    test('saves conversations to localStorage', () => {
      const testConversations = [mockConversation]
      saveConversations(testConversations)

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'ai-conversations', 
        JSON.stringify(testConversations)
      )
    })

    test('handles localStorage save errors gracefully', () => {
      const originalSetItem = localStorage.setItem
      vi.mocked(localStorage.setItem).mockImplementation(() => {
        throw new Error('localStorage quota exceeded')
      })

      // Should not throw an error
      expect(() => saveConversations([mockConversation])).not.toThrow()

      localStorage.setItem = originalSetItem
    })
  })

  describe('clearAllConversations', () => {
    test('removes conversations from localStorage', () => {
      clearAllConversations()
      
      expect(localStorage.removeItem).toHaveBeenCalledWith('ai-conversations')
    })

    test('handles localStorage clear errors gracefully', () => {
      const originalRemoveItem = localStorage.removeItem
      vi.mocked(localStorage.removeItem).mockImplementation(() => {
        throw new Error('localStorage access denied')
      })

      expect(() => clearAllConversations()).not.toThrow()

      localStorage.removeItem = originalRemoveItem
    })
  })

  describe('createConversation', () => {
    test('creates conversation with all required fields', () => {
      const conversation = createConversation(
        'Test query',
        'Test response',
        'thread-123',
        'web'
      )

      expect(conversation).toMatchObject({
        title: 'Test query',
        thread_id: 'thread-123',
        last_query: 'Test query',
        last_response: 'Test response',
        message_count: 2,
        agent_type: 'web'
      })
      expect(conversation.id).toBeTruthy()
      expect(conversation.timestamp).toBeTruthy()
    })

    test('truncates long queries for title', () => {
      const longQuery = 'This is a very long query that should be truncated because it exceeds the maximum length limit for titles'
      const conversation = createConversation(longQuery, 'Response', 'thread-123')

      expect(conversation.title).toBe('This is a very long query that should be truncated...')
      expect(conversation.title.length).toBeLessThanOrEqual(53) // 50 + '...'
    })

    test('uses auto as default agent type', () => {
      const conversation = createConversation('Query', 'Response', 'thread-123')
      expect(conversation.agent_type).toBe('auto')
    })

    test('preserves short queries as full title', () => {
      const shortQuery = 'Short query'
      const conversation = createConversation(shortQuery, 'Response', 'thread-123')
      expect(conversation.title).toBe(shortQuery)
    })
  })

  describe('updateConversation', () => {
    test('updates conversation with new query and response', () => {
      const updatedConversation = updateConversation(
        mockConversation,
        'New query',
        'New response',
        'fabric'
      )

      expect(updatedConversation.last_query).toBe('New query')
      expect(updatedConversation.last_response).toBe('New response')
      expect(updatedConversation.message_count).toBe(4) // original 2 + 2 new messages
      expect(updatedConversation.agent_type).toBe('fabric')
      expect(updatedConversation.timestamp).toBeGreaterThan(mockConversation.timestamp)
    })

    test('preserves original agent type when not specified', () => {
      const updatedConversation = updateConversation(
        mockConversation,
        'New query',
        'New response'
      )

      expect(updatedConversation.agent_type).toBe(mockConversation.agent_type)
    })

    test('increments message count correctly', () => {
      const originalCount = mockConversation.message_count
      const updatedConversation = updateConversation(
        mockConversation,
        'Query',
        'Response'
      )

      expect(updatedConversation.message_count).toBe(originalCount + 2)
    })

    test('preserves all other conversation properties', () => {
      const updatedConversation = updateConversation(
        mockConversation,
        'Query',
        'Response'
      )

      expect(updatedConversation.id).toBe(mockConversation.id)
      expect(updatedConversation.title).toBe(mockConversation.title)
      expect(updatedConversation.thread_id).toBe(mockConversation.thread_id)
    })
  })
})