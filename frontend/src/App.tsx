import { useEffect, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Send, Sidebar } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { EmptyState } from '@/components/chat/empty-state'
import { HistoryPanel } from '@/components/chat/history-panel'
import { MessageList } from '@/components/chat/message-list'
import { ModeSelector } from '@/components/chat/mode-selector'
import { SamplePrompts } from '@/components/chat/sample-prompts'
import type {
  AgentIdentifier,
  AppState,
  ChatMessage,
  ConversationEntry,
  SelectedMode,
} from '@/types/chat'

const CONVERSATIONS_STORAGE_KEY = 'ai-conversations'

function App() {
  const [query, setQuery] = useState('')
  const [appState, setAppState] = useState<AppState>('idle')
  const [conversations, setConversations] = useState<ConversationEntry[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [selectedMode, setSelectedMode] = useState<SelectedMode>('auto')
  const [fabricAgentEnabled, setFabricAgentEnabled] = useState(true)
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [hasHydrated, setHasHydrated] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    try {
      const saved = localStorage.getItem(CONVERSATIONS_STORAGE_KEY)
      if (saved) {
        setConversations(JSON.parse(saved))
      }
    } catch (error) {
      setConversations([])
    } finally {
      setHasHydrated(true)
    }
  }, [])

  useEffect(() => {
    if (!hasHydrated) {
      return
    }

    try {
      if (conversations.length === 0) {
        localStorage.removeItem(CONVERSATIONS_STORAGE_KEY)
      } else {
        localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify(conversations))
      }
    } catch (error) {}
  }, [conversations, hasHydrated])

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('/api/config')
        if (!response.ok) {
          return
        }
        const config = await response.json()
        const fabricEnabled =
          config?.features?.fabric_agent_enabled ?? config?.fabric_agent_enabled
        setFabricAgentEnabled(
          typeof fabricEnabled === 'boolean' ? fabricEnabled : true,
        )
      } catch (error) {}
    }

    fetchConfig()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  const saveConversation = (
    question: string,
    response: string,
    threadId: string,
    agentType?: ConversationEntry['agent_type'],
  ) => {
    if (currentConversationId) {
      setConversations((previous) =>
        (previous || []).map((conversation) =>
          conversation.id === currentConversationId
            ? {
                ...conversation,
                last_query: question,
                last_response: response,
                message_count: conversation.message_count + 2,
                timestamp: Date.now(),
                agent_type: agentType || conversation.agent_type,
              }
            : conversation,
        ),
      )
      return
    }

    const title = question.length > 50 ? `${question.substring(0, 50)}...` : question
    const newConversation: ConversationEntry = {
      id: Date.now().toString(),
      title,
      thread_id: threadId,
      last_query: question,
      last_response: response,
      message_count: 2,
      timestamp: Date.now(),
      agent_type: agentType || 'auto',
    }

    setConversations((previous) => [newConversation, ...(previous || [])])
    setCurrentConversationId(newConversation.id)
  }

  const loadConversation = async (conversation: ConversationEntry) => {
    try {
      setAppState('analyzing')
      setCurrentConversationId(conversation.id)
      setCurrentThreadId(conversation.thread_id)
      setShowHistory(false)
      setChatMessages([
        {
          id: 'loading-conversation',
          type: 'system',
          content: 'Loading conversation...',
          timestamp: Date.now(),
          isTyping: true,
        },
      ])

      const response = await fetch(`/api/thread/${conversation.thread_id}/messages`)
      if (!response.ok) {
        setChatMessages([
          {
            id: 'fetch-error',
            type: 'system',
            content:
              'Failed to fetch conversation messages. You can continue the conversation by asking a new question.',
            timestamp: Date.now(),
            isTyping: false,
          },
        ])
        setAppState('idle')
        return
      }

      const result = await response.json()
      if (!result.success || !result.messages) {
        setChatMessages([
          {
            id: 'load-error',
            type: 'system',
            content: `Could not load conversation messages: ${result.error || 'Unknown error'}. You can continue the conversation by asking a new question.`,
            timestamp: Date.now(),
            isTyping: false,
          },
        ])
        setAppState('idle')
        return
      }

      const agentForConversation = mapConversationAgent(conversation.agent_type)
      const loadedMessages: ChatMessage[] = result.messages.map((message: any, index: number) => ({
        id: message.id || `loaded-${index}`,
        type: message.role === 'user' ? 'user' : 'agent',
        content: message.content,
        agent: message.role === 'assistant' ? agentForConversation : undefined,
        timestamp: new Date(message.created_at).getTime(),
        isTyping: false,
      }))

      setChatMessages(loadedMessages)
      setAppState('idle')
    } catch (error: any) {
      setChatMessages([
        {
          id: 'error',
          type: 'system',
          content: `Error loading conversation: ${error.message}. You can start a new conversation.`,
          timestamp: Date.now(),
          isTyping: false,
        },
      ])
      setAppState('idle')
    }
  }

  const startNewConversation = () => {
    setChatMessages([])
    setCurrentThreadId(null)
    setCurrentConversationId(null)
    setAppState('idle')
  }

  const clearAllConversations = () => {
    setConversations([])
  }

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      timestamp: Date.now(),
    }
    setChatMessages((previous) => [...previous, newMessage])
    return newMessage.id
  }

  const updateMessage = (id: string, updates: Partial<ChatMessage>) => {
    setChatMessages((previous) => previous.map((message) => (message.id === id ? { ...message, ...updates } : message)))
  }

  const typeMessage = async (id: string, content: string, speed = 15) => {
    const words = content.split(' ')
    let current = ''

    for (let index = 0; index < words.length; index += 1) {
      current += (index > 0 ? ' ' : '') + words[index]
      updateMessage(id, { content: current, isTyping: true })
      const delay = words[index].match(/[.!?]/) ? speed * 3 : words[index].match(/[;,]/) ? speed * 2 : speed
      await new Promise((resolve) => setTimeout(resolve, delay))
    }

    updateMessage(id, { isTyping: false })
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!query.trim() || appState !== 'idle') {
      return
    }

    const userQuery = query.trim()
    setQuery('')

    addMessage({
      type: 'user',
      content: userQuery,
    })

    setAppState('analyzing')

    try {
      const purviewMessageId = addMessage({
        type: 'system',
        agent: 'purview',
        content: '',
        isTyping: true,
      })

      await new Promise((resolve) => setTimeout(resolve, 500))

      if (selectedMode !== 'auto') {
        const routingExplanation = getRoutingExplanation(selectedMode)
        await typeMessage(purviewMessageId, routingExplanation, 15)
        updateMessage(purviewMessageId, { isTyping: true })
        await processDirectly(selectedMode, userQuery, routingExplanation, purviewMessageId)
        return
      }

      await typeMessage(purviewMessageId, 'Analyzing query to determine optimal data source and processing method...', 15)
      updateMessage(purviewMessageId, { isTyping: true })

      const analyzeResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userQuery }),
      })

      if (!analyzeResponse.ok) {
        throw new Error(`Analysis failed: ${analyzeResponse.statusText}`)
      }

      const analysisResult = await analyzeResponse.json()
      if (!analysisResult.success) {
        throw new Error(analysisResult.error || 'Analysis failed')
      }

      await new Promise((resolve) => setTimeout(resolve, 300))
      updateMessage(purviewMessageId, { content: '', isTyping: true })

      let analysisMessage = `**Purview Analysis Complete**: Found ${analysisResult.catalog_results?.assets_found || 0} relevant data assets`
      if (analysisResult.catalog_results?.assets_found > 0) {
        const assets = analysisResult.catalog_results.results
        const agentTypes = assets.map((asset: any) => asset.connected_agent).filter(Boolean)
        if (agentTypes.length > 0) {
          const uniqueAgents = [...new Set(agentTypes)]
          if (uniqueAgents.length > 0) {
            analysisMessage += `\n**Available Agents**: ${uniqueAgents.join(', ')}`
            if (uniqueAgents.length > 1) {
              analysisMessage += `\n**Agent Options**: ${uniqueAgents.length} different agent types available`
            }
          }
        }
      }

      await typeMessage(purviewMessageId, analysisMessage, 12)
      updateMessage(purviewMessageId, { isTyping: true })
      setAppState('processing')

      await new Promise((resolve) => setTimeout(resolve, 600))
      await processWithConnectedAgents(userQuery, analysisResult, purviewMessageId)
    } catch (error: any) {
      setChatMessages((previous) => previous.map((message) => ({ ...message, isTyping: false })))
      addMessage({
        type: 'system',
        content: `Sorry, I encountered an error processing your request: ${error.message}. Please try again.`,
      })
      setAppState('idle')
    }
  }

  const processDirectly = async (
    agent: SelectedMode,
    userQuery: string,
    purviewAnalysis: string,
    purviewMessageId?: string,
  ) => {
    if (agent === 'auto') {
      await processWithConnectedAgents(userQuery, { purview: purviewAnalysis }, purviewMessageId)
      return
    }

    const agentMessageId = addMessage({
      type: 'agent',
      agent: agent as AgentIdentifier,
      content: '',
      isTyping: true,
    })

    if (purviewMessageId) {
      updateMessage(purviewMessageId, { isTyping: false })
    }

    try {
      const directResponse = await fetch('/api/process-direct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userQuery,
          agent,
          thread_id: currentThreadId,
        }),
      })

      if (!directResponse.ok) {
        throw new Error(`Direct processing failed: ${directResponse.statusText}`)
      }

      const directResult = await directResponse.json()
      if (!directResult.success) {
        throw new Error(directResult.error || 'Direct processing failed')
      }

      if (directResult.metadata?.thread_id && !currentThreadId) {
        setCurrentThreadId(directResult.metadata.thread_id)
      }

      const responseWithCitations = appendAnnotations(directResult.response, directResult.annotations)
      await typeMessage(agentMessageId, responseWithCitations, 12)

      const threadId = directResult.metadata?.thread_id || currentThreadId || 'unknown'
      saveConversation(userQuery, directResult.response, threadId, agent)
      setAppState('idle')
    } catch (error: any) {
      await typeMessage(
        agentMessageId,
        `I encountered an error while processing your request directly with the ${agent} agent: ${error.message}. Please try again.`,
      )
      setAppState('idle')
    }
  }

  const processWithConnectedAgents = async (
    userQuery: string,
    analysisResult: any,
    purviewMessageId?: string,
  ) => {
    const identifiedAgent = extractAgentFromAnalysis(analysisResult.purview)
    const agentMessageId = addMessage({
      type: 'agent',
      agent: identifiedAgent || 'purview',
      content: '',
      isTyping: true,
    })

    if (purviewMessageId) {
      updateMessage(purviewMessageId, { isTyping: false })
    }

    try {
      const routeResponse = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userQuery,
          thread_id: currentThreadId,
        }),
      })

      if (!routeResponse.ok) {
        throw new Error(`Processing failed: ${routeResponse.statusText}`)
      }

      const processingResult = await routeResponse.json()
      if (!processingResult.success) {
        throw new Error(processingResult.error || 'Processing failed')
      }

      if (processingResult.metadata?.thread_id && !currentThreadId) {
        setCurrentThreadId(processingResult.metadata.thread_id)
      }

      const actualAgent = extractActualAgentFromResponse(processingResult)
      if (actualAgent && actualAgent !== identifiedAgent) {
        updateMessage(agentMessageId, { agent: actualAgent })
      }

      const routingNote = buildRoutingNote(actualAgent, identifiedAgent)
      const baseResponse = routingNote ? `${routingNote}\n\n${processingResult.response}` : processingResult.response
      const responseWithCitations = appendAnnotations(baseResponse, processingResult.annotations)

      await typeMessage(agentMessageId, responseWithCitations, 12)

      const finalAgent: ConversationEntry['agent_type'] = actualAgent || identifiedAgent || 'auto'
      const threadId = processingResult.metadata?.thread_id || currentThreadId || 'unknown'

      saveConversation(userQuery, processingResult.response, threadId, finalAgent)
      setAppState('idle')
    } catch (error: any) {
      await typeMessage(
        agentMessageId,
        `I encountered an error while processing your request through the connected agent service: ${error.message}. Please try again or contact support if the issue persists.`,
      )
      setAppState('idle')
    }
  }

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-6 py-6 max-w-7xl h-screen flex flex-col">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gradient">Agent Router Demo App</h1>
              <div className="flex items-center gap-2">
                <p className="text-sm text-muted-foreground">Purview-powered intent routing</p>
                {currentConversationId && (
                  <Badge variant="outline" className="text-xs px-2 py-1 bg-accent/10 text-accent border-accent/30">
                    Active conversation
                  </Badge>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {chatMessages.length > 0 && (
              <Button
                variant="ghost"
                onClick={startNewConversation}
                className="h-10 px-4 rounded-xl hover:bg-accent/10 transition-all duration-300"
              >
                New Chat
              </Button>
            )}
            {import.meta.env.DEV && conversations.length > 0 && (
              <Button
                variant="ghost"
                onClick={clearAllConversations}
                className="h-10 px-4 rounded-xl hover:bg-red-500/10 hover:text-red-400 transition-all duration-300 text-muted-foreground"
              >
                Clear All
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={() => setShowHistory(!showHistory)}
              className="h-10 px-4 rounded-xl hover:bg-accent/10 transition-all duration-300"
            >
              <Sidebar size={18} className="mr-2" />
              History
            </Button>
          </div>
        </motion.div>

        <div className="flex-1 grid gap-6 transition-all duration-300 relative">
          <div className="flex flex-col">
            <AnimatePresence>
              {showHistory && (
                <HistoryPanel
                  conversations={conversations}
                  onSelect={loadConversation}
                  onClose={() => setShowHistory(false)}
                />
              )}
            </AnimatePresence>

            <div className="flex-1 flex flex-col min-h-0 relative">
              {chatMessages.length === 0 ? (
                <EmptyState />
              ) : (
                <MessageList messages={chatMessages} endRef={messagesEndRef} />
              )}
            </div>

            <Card className="glass-card border-0 p-6 mt-6 space-y-4">
              {chatMessages.length === 0 && (
                <SamplePrompts onSelect={setQuery} disabled={appState !== 'idle'} />
              )}

              <form onSubmit={handleSubmit} className="flex gap-3 items-end">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <ModeSelector
                      value={selectedMode}
                      onChange={setSelectedMode}
                      disabled={appState !== 'idle'}
                      fabricAgentEnabled={fabricAgentEnabled}
                    />

                    {selectedMode !== 'auto' && (
                      <Badge variant="outline" className="text-xs px-2 py-1 bg-accent/10 text-accent border-accent/30">
                        Manual mode
                      </Badge>
                    )}
                  </div>

                  <Input
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder={getPlaceholder(selectedMode, fabricAgentEnabled)}
                    className="h-12 bg-background/40 border-border/50 rounded-xl font-medium placeholder:text-muted-foreground/70 focus:border-accent/50 focus:ring-2 focus:ring-accent/20 transition-all duration-300"
                    disabled={appState !== 'idle'}
                  />
                </div>

                <Button
                  type="submit"
                  size="lg"
                  className="h-12 px-8 rounded-xl bg-gradient-to-r from-accent via-accent to-primary hover:from-accent/90 hover:via-accent/90 hover:to-primary/90 transition-all duration-300 shadow-lg hover:shadow-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={!query.trim() || appState !== 'idle'}
                >
                  <Send size={18} className="mr-2" />
                  {appState === 'idle' ? 'Send' : 'Processing...'}
                </Button>
              </form>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

function mapConversationAgent(agentType?: ConversationEntry['agent_type']): AgentIdentifier {
  switch (agentType) {
    case 'fabric':
      return 'fabric'
    case 'rag':
      return 'rag'
    case 'web':
      return 'web'
    case 'genie':
      return 'genie'
    default:
      return 'purview'
  }
}

function extractAgentFromAnalysis(purviewMessage: string): ConversationEntry['agent_type'] | null {
  if (!purviewMessage) {
    return null
  }

  const lowerMessage = purviewMessage.toLowerCase()
  if (lowerMessage.includes('fabric') || lowerMessage.includes('fabric_agent')) {
    return 'fabric'
  }
  if (lowerMessage.includes('rag') || lowerMessage.includes('rag_agent') || lowerMessage.includes('document')) {
    return 'rag'
  }
  if (lowerMessage.includes('web') || lowerMessage.includes('search') || lowerMessage.includes('bing')) {
    return 'web'
  }
  if (lowerMessage.includes('genie') || lowerMessage.includes('databricks')) {
    return 'genie'
  }

  return null
}

function extractActualAgentFromResponse(processingResult: any): ConversationEntry['agent_type'] | null {
  const toolsCalled = processingResult?.metadata?.tools_called || []
  if (toolsCalled.some((tool: string) => tool.includes('handoff_genie_agent'))) {
    return 'genie'
  }

  const connectedAgentsCalled = processingResult?.metadata?.connected_agents_called || []
  if (connectedAgentsCalled.length > 0) {
    const actualAgent = connectedAgentsCalled[0]
    if (actualAgent === 'web-agent' || actualAgent === 'web_agent') {
      return 'web'
    }
    if (actualAgent === 'rag-agent' || actualAgent === 'rag_agent') {
      return 'rag'
    }
    if (actualAgent === 'fabric-agent' || actualAgent === 'fabric_agent') {
      return 'fabric'
    }
  }

  return null
}

function appendAnnotations(baseText: string, annotations: any[] | undefined): string {
  if (!annotations || annotations.length === 0) {
    return baseText
  }

  let result = baseText

  annotations.forEach((annotation: any, index: number) => {
    const citationNumber = index + 1
    if (annotation.type === 'url_citation') {
      result += `\n\n**Source ${citationNumber}:** [${annotation.title}](${annotation.url})`
    } else if (annotation.type === 'file_citation') {
      result += `\n\n**Source ${citationNumber}:** ${annotation.file_name} - "${annotation.quote}"`
    }
  })

  return result
}

function buildRoutingNote(actualAgent: ConversationEntry['agent_type'], identifiedAgent: ConversationEntry['agent_type'] | null) {
  if (!actualAgent) {
    return ''
  }

  if (actualAgent && actualAgent !== identifiedAgent) {
    return `**Final Routing Decision**: ${actualAgent} agent selected and provided this response based on query context and analysis.`
  }

  if (actualAgent && actualAgent === identifiedAgent) {
    return `**Routing Confirmed**: ${actualAgent} agent processed this request as anticipated from catalog analysis.`
  }

  return `**Final Routing Decision**: ${actualAgent} agent selected to handle this request.`
}

function getRoutingExplanation(mode: SelectedMode) {
  switch (mode) {
    case 'fabric':
      return 'User selected Fabric Data Agent. Routing directly to structured data analysis via NL2SQL.'
    case 'rag':
      return 'User selected RAG Agent. Routing to document processing and semantic search.'
    case 'web':
      return 'User selected Web Search. Routing to Bing search for real-time information.'
    case 'genie':
      return 'User selected Databricks Genie Agent. Routing to natural language data analysis.'
    default:
      return 'Routing via Purview intelligence.'
  }
}

function getPlaceholder(mode: SelectedMode, fabricAgentEnabled: boolean) {
  if (mode === 'fabric') {
    return 'Ask about customer data, sales analytics, reports...'
  }
  if (mode === 'rag') {
    return 'Ask about invoices, documents, contracts...'
  }
  if (mode === 'web') {
    return 'Ask about current events, general knowledge...'
  }
  if (mode === 'genie') {
    return 'Ask about data analysis, SQL queries, insights...'
  }
  if (fabricAgentEnabled) {
    return 'Ask about customer data, invoice analysis, reports...'
  }
  return 'Ask about data analysis, documents, web search...'
}

export default App
