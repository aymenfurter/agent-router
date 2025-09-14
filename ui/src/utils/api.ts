// API utilities for backend communication
export const API_ENDPOINTS = {
  CONFIG: '/api/config',
  ANALYZE: '/api/analyze',
  PROCESS: '/api/process',
  PROCESS_DIRECT: '/api/process-direct',
  THREAD_MESSAGES: (threadId: string) => `/api/thread/${threadId}/messages`
} as const

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  metadata?: Record<string, any>
}

export const fetchConfig = async (): Promise<ApiResponse> => {
  try {
    const response = await fetch(API_ENDPOINTS.CONFIG)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    return await response.json()
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error occurred'
    }
  }
}

export const analyzeQuery = async (query: string): Promise<ApiResponse> => {
  try {
    const response = await fetch(API_ENDPOINTS.ANALYZE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query })
    })
    
    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Analysis failed'
    }
  }
}

export const processQuery = async (query: string, threadId?: string): Promise<ApiResponse> => {
  try {
    const response = await fetch(API_ENDPOINTS.PROCESS, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        query,
        thread_id: threadId 
      })
    })
    
    if (!response.ok) {
      throw new Error(`Processing failed: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Processing failed'
    }
  }
}

export const processDirectQuery = async (
  query: string, 
  agent: string, 
  threadId?: string
): Promise<ApiResponse> => {
  try {
    const response = await fetch(API_ENDPOINTS.PROCESS_DIRECT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        query, 
        agent,
        thread_id: threadId
      })
    })
    
    if (!response.ok) {
      throw new Error(`Direct processing failed: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Direct processing failed'
    }
  }
}

export const fetchThreadMessages = async (threadId: string): Promise<ApiResponse> => {
  try {
    const response = await fetch(API_ENDPOINTS.THREAD_MESSAGES(threadId))
    
    if (!response.ok) {
      throw new Error(`Failed to fetch thread messages: ${response.statusText}`)
    }
    
    return await response.json()
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch conversation messages'
    }
  }
}