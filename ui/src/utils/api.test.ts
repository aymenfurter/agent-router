import { describe, test, expect, beforeEach, vi } from 'vitest'
import {
  API_ENDPOINTS,
  fetchConfig,
  analyzeQuery,
  processQuery,
  processDirectQuery,
  fetchThreadMessages
} from './api'

// Mock fetch globally
global.fetch = vi.fn()

describe('API utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('API_ENDPOINTS', () => {
    test('contains all required endpoints', () => {
      expect(API_ENDPOINTS.CONFIG).toBe('/api/config')
      expect(API_ENDPOINTS.ANALYZE).toBe('/api/analyze')
      expect(API_ENDPOINTS.PROCESS).toBe('/api/process')
      expect(API_ENDPOINTS.PROCESS_DIRECT).toBe('/api/process-direct')
    })

    test('THREAD_MESSAGES function returns correct endpoint', () => {
      expect(API_ENDPOINTS.THREAD_MESSAGES('thread-123')).toBe('/api/thread/thread-123/messages')
    })
  })

  describe('fetchConfig', () => {
    test('returns successful response when API call succeeds', async () => {
      const mockResponse = { features: { fabric_agent_enabled: true } }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await fetchConfig()
      
      expect(fetch).toHaveBeenCalledWith('/api/config')
      expect(result).toEqual(mockResponse)
    })

    test('returns error response when API call fails', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      const result = await fetchConfig()
      
      expect(result.success).toBe(false)
      expect(result.error).toContain('HTTP error! status: 500')
    })

    test('handles network errors', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Network error'))

      const result = await fetchConfig()
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Network error')
    })
  })

  describe('analyzeQuery', () => {
    test('sends correct request for query analysis', async () => {
      const mockResponse = { success: true, catalog_results: { assets_found: 2 } }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await analyzeQuery('test query')
      
      expect(fetch).toHaveBeenCalledWith('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: 'test query' })
      })
      expect(result).toEqual(mockResponse)
    })

    test('returns error response when analysis fails', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      })

      const result = await analyzeQuery('test query')
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Analysis failed: Bad Request')
    })

    test('handles analysis network errors', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Connection timeout'))

      const result = await analyzeQuery('test query')
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Connection timeout')
    })
  })

  describe('processQuery', () => {
    test('sends correct request for query processing', async () => {
      const mockResponse = { success: true, response: 'Processed response' }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await processQuery('test query')
      
      expect(fetch).toHaveBeenCalledWith('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: 'test query',
          thread_id: undefined 
        })
      })
      expect(result).toEqual(mockResponse)
    })

    test('includes thread_id when provided', async () => {
      const mockResponse = { success: true, response: 'Processed response' }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await processQuery('test query', 'thread-123')
      
      expect(fetch).toHaveBeenCalledWith('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: 'test query',
          thread_id: 'thread-123' 
        })
      })
    })

    test('returns error response when processing fails', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      })

      const result = await processQuery('test query')
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Processing failed: Internal Server Error')
    })
  })

  describe('processDirectQuery', () => {
    test('sends correct request for direct processing', async () => {
      const mockResponse = { success: true, response: 'Direct response' }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await processDirectQuery('test query', 'web', 'thread-123')
      
      expect(fetch).toHaveBeenCalledWith('/api/process-direct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: 'test query',
          agent: 'web',
          thread_id: 'thread-123'
        })
      })
      expect(result).toEqual(mockResponse)
    })

    test('handles missing thread_id', async () => {
      const mockResponse = { success: true, response: 'Direct response' }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await processDirectQuery('test query', 'fabric')
      
      expect(fetch).toHaveBeenCalledWith('/api/process-direct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: 'test query',
          agent: 'fabric',
          thread_id: undefined
        })
      })
    })

    test('returns error response when direct processing fails', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Service Unavailable',
      })

      const result = await processDirectQuery('test query', 'rag')
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Direct processing failed: Service Unavailable')
    })
  })

  describe('fetchThreadMessages', () => {
    test('sends correct request for thread messages', async () => {
      const mockResponse = { success: true, messages: [{ content: 'Hello' }] }
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await fetchThreadMessages('thread-123')
      
      expect(fetch).toHaveBeenCalledWith('/api/thread/thread-123/messages')
      expect(result).toEqual(mockResponse)
    })

    test('returns error response when fetching messages fails', async () => {
      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      })

      const result = await fetchThreadMessages('invalid-thread')
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Failed to fetch thread messages: Not Found')
    })

    test('handles thread messages network errors', async () => {
      ;(global.fetch as any).mockRejectedValueOnce(new Error('Server unreachable'))

      const result = await fetchThreadMessages('thread-123')
      
      expect(result.success).toBe(false)
      expect(result.error).toBe('Server unreachable')
    })
  })
})