// Utility functions extracted from App.tsx for testing
export const formatTimestamp = (timestamp: number) => {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(timestamp))
}

export const extractAgentFromAnalysis = (purviewMessage: string): 'fabric' | 'rag' | 'web' | 'genie' | null => {
  if (!purviewMessage) return null
  const lowerMessage = purviewMessage.toLowerCase()
  if (lowerMessage.includes('fabric') || lowerMessage.includes('fabric_agent')) {
    return 'fabric'
  } else if (lowerMessage.includes('rag') || lowerMessage.includes('rag_agent') || lowerMessage.includes('document')) {
    return 'rag'
  } else if (lowerMessage.includes('web') || lowerMessage.includes('search') || lowerMessage.includes('bing')) {
    return 'web'
  } else if (lowerMessage.includes('genie') || lowerMessage.includes('databricks')) {
    return 'genie'
  }
  return null
}

export const extractActualAgentFromResponse = (processingResult: any): 'fabric' | 'rag' | 'web' | 'genie' | null => {
  const toolsCalled = processingResult?.metadata?.tools_called || []
  if (toolsCalled.some((tool: string) => tool.includes('handoff_genie_agent'))) {
    return 'genie'
  }
  const connectedAgentsCalled = processingResult?.metadata?.connected_agents_called || []
  if (connectedAgentsCalled.length > 0) {
    const actualAgent = connectedAgentsCalled[0]
    if (actualAgent === 'web-agent' || actualAgent === 'web_agent') {
      return 'web'
    } else if (actualAgent === 'rag-agent' || actualAgent === 'rag_agent') {
      return 'rag'
    } else if (actualAgent === 'fabric-agent' || actualAgent === 'fabric_agent') {
      return 'fabric'
    }
  }
  return null
}

export const getMessageIcon = (message: { type: string; agent?: string }) => {
  // Returns the icon type for testing
  if (message.type === 'user') return 'User'
  if (message.agent === 'purview') return 'Brain'
  if (message.agent === 'fabric') return 'Database'
  if (message.agent === 'rag') return 'FileText'
  if (message.agent === 'web') return 'Globe'
  if (message.agent === 'redirect') return 'MapPin'
  if (message.agent === 'genie') return 'Code'
  return 'Bot'
}

export const getMessageBadge = (message: { type: string; agent?: string }) => {
  if (message.type === 'user') return 'You'
  if (message.agent === 'purview') return 'Purview Analysis'
  if (message.agent === 'fabric') return 'Fabric Data Agent'
  if (message.agent === 'rag') return 'RAG Agent'
  if (message.agent === 'web') return 'Web Search Agent'
  if (message.agent === 'redirect') return 'Purview Redirect'
  if (message.agent === 'genie') return 'Databricks Genie Agent'
  return 'System'
}

export const getAgentColor = (message: { type: string; agent?: string }) => {
  if (message.type === 'user') return 'user'
  if (message.agent === 'purview') return 'purview'
  if (message.agent === 'fabric') return 'fabric'
  if (message.agent === 'rag') return 'rag'
  if (message.agent === 'web') return 'web'
  if (message.agent === 'redirect') return 'redirect'
  if (message.agent === 'genie') return 'genie'
  return 'system'
}