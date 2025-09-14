import { describe, test, expect } from 'vitest'
import {
  formatTimestamp,
  extractAgentFromAnalysis,
  extractActualAgentFromResponse,
  getMessageIcon,
  getMessageBadge,
  getAgentColor
} from './helpers'

describe('Utility Functions', () => {
  describe('formatTimestamp', () => {
    test('formats timestamp correctly', () => {
      const timestamp = new Date('2024-01-15T14:30:00').getTime()
      const formatted = formatTimestamp(timestamp)
      
      expect(formatted).toBe('Jan 15, 02:30 PM')
    })

    test('handles different dates', () => {
      const timestamp = new Date('2024-12-25T09:15:00').getTime()
      const formatted = formatTimestamp(timestamp)
      
      expect(formatted).toBe('Dec 25, 09:15 AM')
    })
  })

  describe('extractAgentFromAnalysis', () => {
    test('returns null for empty message', () => {
      expect(extractAgentFromAnalysis('')).toBe(null)
      expect(extractAgentFromAnalysis(null as any)).toBe(null)
      expect(extractAgentFromAnalysis(undefined as any)).toBe(null)
    })

    test('extracts fabric agent correctly', () => {
      expect(extractAgentFromAnalysis('Using fabric agent for analysis')).toBe('fabric')
      expect(extractAgentFromAnalysis('Routing to fabric_agent')).toBe('fabric')
      expect(extractAgentFromAnalysis('FABRIC processing required')).toBe('fabric')
    })

    test('extracts rag agent correctly', () => {
      expect(extractAgentFromAnalysis('Using rag for document search')).toBe('rag')
      expect(extractAgentFromAnalysis('rag_agent will handle this')).toBe('rag')
      expect(extractAgentFromAnalysis('Document processing needed')).toBe('rag')
    })

    test('extracts web agent correctly', () => {
      expect(extractAgentFromAnalysis('Using web search')).toBe('web')
      expect(extractAgentFromAnalysis('Bing search required')).toBe('web')
      expect(extractAgentFromAnalysis('Search the internet')).toBe('web')
    })

    test('extracts genie agent correctly', () => {
      expect(extractAgentFromAnalysis('Using genie for data analysis')).toBe('genie')
      expect(extractAgentFromAnalysis('Databricks processing needed')).toBe('genie')
      expect(extractAgentFromAnalysis('GENIE agent selected')).toBe('genie')
    })

    test('returns null for non-matching messages', () => {
      expect(extractAgentFromAnalysis('General processing message')).toBe(null)
      expect(extractAgentFromAnalysis('Unknown agent type')).toBe(null)
    })
  })

  describe('extractActualAgentFromResponse', () => {
    test('returns null for empty or invalid processing result', () => {
      expect(extractActualAgentFromResponse(null)).toBe(null)
      expect(extractActualAgentFromResponse({})).toBe(null)
      expect(extractActualAgentFromResponse({ metadata: {} })).toBe(null)
    })

    test('extracts genie agent from tools_called', () => {
      const result = {
        metadata: {
          tools_called: ['handoff_genie_agent', 'other_tool']
        }
      }
      expect(extractActualAgentFromResponse(result)).toBe('genie')
    })

    test('extracts web agent from connected_agents_called', () => {
      const result = {
        metadata: {
          connected_agents_called: ['web-agent']
        }
      }
      expect(extractActualAgentFromResponse(result)).toBe('web')

      const result2 = {
        metadata: {
          connected_agents_called: ['web_agent']
        }
      }
      expect(extractActualAgentFromResponse(result2)).toBe('web')
    })

    test('extracts rag agent from connected_agents_called', () => {
      const result = {
        metadata: {
          connected_agents_called: ['rag-agent']
        }
      }
      expect(extractActualAgentFromResponse(result)).toBe('rag')

      const result2 = {
        metadata: {
          connected_agents_called: ['rag_agent']
        }
      }
      expect(extractActualAgentFromResponse(result2)).toBe('rag')
    })

    test('extracts fabric agent from connected_agents_called', () => {
      const result = {
        metadata: {
          connected_agents_called: ['fabric-agent']
        }
      }
      expect(extractActualAgentFromResponse(result)).toBe('fabric')

      const result2 = {
        metadata: {
          connected_agents_called: ['fabric_agent']
        }
      }
      expect(extractActualAgentFromResponse(result2)).toBe('fabric')
    })

    test('prioritizes genie agent from tools_called over connected_agents', () => {
      const result = {
        metadata: {
          tools_called: ['handoff_genie_agent'],
          connected_agents_called: ['web-agent']
        }
      }
      expect(extractActualAgentFromResponse(result)).toBe('genie')
    })
  })

  describe('getMessageIcon', () => {
    test('returns correct icons for different message types', () => {
      expect(getMessageIcon({ type: 'user' })).toBe('User')
      expect(getMessageIcon({ type: 'system' })).toBe('Bot')
      expect(getMessageIcon({ type: 'agent', agent: 'purview' })).toBe('Brain')
      expect(getMessageIcon({ type: 'agent', agent: 'fabric' })).toBe('Database')
      expect(getMessageIcon({ type: 'agent', agent: 'rag' })).toBe('FileText')
      expect(getMessageIcon({ type: 'agent', agent: 'web' })).toBe('Globe')
      expect(getMessageIcon({ type: 'agent', agent: 'redirect' })).toBe('MapPin')
      expect(getMessageIcon({ type: 'agent', agent: 'genie' })).toBe('Code')
      expect(getMessageIcon({ type: 'agent' })).toBe('Bot')
    })
  })

  describe('getMessageBadge', () => {
    test('returns correct badges for different message types', () => {
      expect(getMessageBadge({ type: 'user' })).toBe('You')
      expect(getMessageBadge({ type: 'system' })).toBe('System')
      expect(getMessageBadge({ type: 'agent', agent: 'purview' })).toBe('Purview Analysis')
      expect(getMessageBadge({ type: 'agent', agent: 'fabric' })).toBe('Fabric Data Agent')
      expect(getMessageBadge({ type: 'agent', agent: 'rag' })).toBe('RAG Agent')
      expect(getMessageBadge({ type: 'agent', agent: 'web' })).toBe('Web Search Agent')
      expect(getMessageBadge({ type: 'agent', agent: 'redirect' })).toBe('Purview Redirect')
      expect(getMessageBadge({ type: 'agent', agent: 'genie' })).toBe('Databricks Genie Agent')
      expect(getMessageBadge({ type: 'agent' })).toBe('System')
    })
  })

  describe('getAgentColor', () => {
    test('returns correct colors for different message types', () => {
      expect(getAgentColor({ type: 'user' })).toBe('user')
      expect(getAgentColor({ type: 'system' })).toBe('system')
      expect(getAgentColor({ type: 'agent', agent: 'purview' })).toBe('purview')
      expect(getAgentColor({ type: 'agent', agent: 'fabric' })).toBe('fabric')
      expect(getAgentColor({ type: 'agent', agent: 'rag' })).toBe('rag')
      expect(getAgentColor({ type: 'agent', agent: 'web' })).toBe('web')
      expect(getAgentColor({ type: 'agent', agent: 'redirect' })).toBe('redirect')
      expect(getAgentColor({ type: 'agent', agent: 'genie' })).toBe('genie')
      expect(getAgentColor({ type: 'agent' })).toBe('system')
    })
  })
})