import { useState, useEffect, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Send, Clock, Sidebar, X, User, Brain, Zap, Database, FileText, Bot, Sparkles, Search, Globe, Settings, MapPin, Code } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import React from 'react'

interface MessageContentProps {
  content: string
  isUser: boolean
}

function MessageContent({ content, isUser }: MessageContentProps) {
  const parseContent = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = []
    let currentIndex = 0
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
    let match
    const codeBlocks: Array<{start: number, end: number, language?: string, code: string}> = []
    while ((match = codeBlockRegex.exec(text)) !== null) {
      codeBlocks.push({
        start: match.index,
        end: match.index + match[0].length,
        language: match[1] || '',
        code: match[2]
      })
    }
    let lastIndex = 0
    codeBlocks.forEach((block, blockIndex) => {
      if (block.start > lastIndex) {
        const beforeCode = text.slice(lastIndex, block.start)
        parts.push(...parseRegularContent(beforeCode, blockIndex * 2))
      }
      parts.push(
        <div key={`code-${blockIndex}`} className="my-4 rounded-lg bg-muted/50 border border-border/50 overflow-hidden">
          {block.language && (
            <div className="px-3 py-2 bg-muted/80 text-xs font-medium text-muted-foreground border-b border-border/30">
              {block.language.toUpperCase()}
            </div>
          )}
          <pre className="p-3 text-xs overflow-x-auto">
            <code className="text-foreground">{block.code}</code>
          </pre>
        </div>
      )
      lastIndex = block.end
    })
    if (lastIndex < text.length) {
      const afterCode = text.slice(lastIndex)
      parts.push(...parseRegularContent(afterCode, codeBlocks.length * 2))
    }
    return parts
  }
  
  const parseRegularContent = (text: string, keyOffset: number = 0): React.ReactNode[] => {
    const parts: React.ReactNode[] = []
    const lines = text.split('\n')
    let currentTable: string[] = []
    let inTable = false
    lines.forEach((line, lineIndex) => {
      const key = `${keyOffset}-line-${lineIndex}`
      if (line.includes('|') && (line.match(/\|/g) || []).length >= 2) {
        currentTable.push(line)
        inTable = true
      } else {
        if (inTable && currentTable.length > 0) {
          const tableElement = renderTable(currentTable, `${key}-table`)
          if (tableElement) {
            parts.push(tableElement)
          }
          currentTable = []
          inTable = false
        }
        if (line.trim()) {
          parts.push(
            <div key={key} className="mb-2">
              {renderFormattedText(line)}
            </div>
          )
        }
      }
    })
    if (inTable && currentTable.length > 0) {
      const tableElement = renderTable(currentTable, `${keyOffset}-final-table`)
      if (tableElement) {
        parts.push(tableElement)
      }
    }
    return parts
  }
  
  const renderTable = (rows: string[], key: string): React.ReactElement | null => {
    if (rows.length === 0) return null
    const tableData = rows.map(row => 
      row.split('|').map(cell => cell.trim()).filter(cell => cell !== '')
    )
    if (tableData.length === 0) return null
    const hasHeader = tableData.length > 1 && tableData[0].every(cell => 
      !cell.match(/^\d{4}-\d{2}-\d{2}/) && !cell.match(/^\d+\.?\d*$/)
    )
    return (
      <div key={key} className="my-4 overflow-x-auto">
        <table className="w-full text-xs border border-border/50 rounded-lg overflow-hidden">
          {hasHeader && (
            <thead>
              <tr className="bg-muted/50">
                {tableData[0].map((header, i) => (
                  <th key={i} className="px-3 py-2 text-left font-medium border-r border-border/30 last:border-r-0">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody>
            {(hasHeader ? tableData.slice(1) : tableData).map((row, i) => (
              <tr key={i} className={`${i % 2 === 0 ? 'bg-background/50' : 'bg-muted/20'} hover:bg-accent/10 transition-colors`}>
                {row.map((cell, j) => (
                  <td key={j} className="px-3 py-2 border-r border-border/30 last:border-r-0 font-mono">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }
  
  const renderFormattedText = (text: string): React.ReactNode => {
    const elements: (string | React.ReactElement)[] = []
    let lastIndex = 0
    const boldRegex = /\*\*(.*?)\*\*/g
    let match
    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        elements.push(text.slice(lastIndex, match.index))
      }
      elements.push(
        <span key={`bold-${match.index}`} className={`font-semibold ${
          isUser ? 'text-accent-foreground' : 'text-foreground'
        }`}>
          {match[1]}
        </span>
      )
      lastIndex = match.index + match[0].length
    }
    if (lastIndex < text.length) {
      elements.push(text.slice(lastIndex))
    }
    return elements.map((element, index) => {
      if (typeof element === 'string') {
        return element.split(/(\[([^\]]+)\]\(([^)]+)\))/).map((linkPart, linkIndex) => {
          if (linkIndex % 4 === 0) {
            return <span key={`${index}-${linkIndex}`}>{linkPart}</span>
          } else if (linkIndex % 4 === 2) {
            const urlMatch = element.match(/(\[([^\]]+)\]\(([^)]+)\))/g)
            if (urlMatch && urlMatch[Math.floor(linkIndex / 4)]) {
              const url = urlMatch[Math.floor(linkIndex / 4)].match(/\(([^)]+)\)/)?.[1]
              return (
                <a 
                  key={`${index}-${linkPart}`}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:text-accent/80 underline"
                >
                  {linkPart}
                </a>
              )
            }
          }
          return null
        }).filter(Boolean)
      }
      return element
    })
  }
  
  return <div className="space-y-1">{parseContent(content)}</div>
}

interface ChatMessage {
  id: string
  type: 'user' | 'system' | 'agent' | 'purview' | 'web'
  content: string
  agent?: 'purview' | 'fabric' | 'rag' | 'web' | 'redirect' | 'genie'
  timestamp: number
  isTyping?: boolean
}

interface ConversationEntry {
  id: string
  title: string
  thread_id: string
  last_query: string
  last_response: string
  message_count: number
  timestamp: number
  agent_type?: 'fabric' | 'rag' | 'web' | 'redirect' | 'genie' | 'auto'
}

type AppState = 'idle' | 'analyzing' | 'routing' | 'processing' | 'complete'

type SelectedMode = 'auto' | 'fabric' | 'rag' | 'web' | 'genie'

function App() {
  const [query, setQuery] = useState('')
  const [appState, setAppState] = useState<AppState>('idle')
  const [conversations, setConversations] = useState<ConversationEntry[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [selectedMode, setSelectedMode] = useState<SelectedMode>('auto')
  const [showModeSelector, setShowModeSelector] = useState(false)
  const [fabricAgentEnabled, setFabricAgentEnabled] = useState(false)
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const isAnyTyping = chatMessages.some(m => m.isTyping)

  useEffect(() => {
    try {
      const saved = localStorage.getItem('ai-conversations')
      if (saved) {
        const parsedConversations = JSON.parse(saved)
        setConversations(parsedConversations)
      }
    } catch (error) {
      setConversations([])
    } finally {
      setIsLoaded(true)
    }
  }, [])

  useEffect(() => {
    if (!isLoaded) {
      return
    }
    try {
      localStorage.setItem('ai-conversations', JSON.stringify(conversations))
    } catch (error) {}
  }, [conversations, isLoaded])

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('/api/config')
        if (response.ok) {
          const config = await response.json()
          setFabricAgentEnabled(config.features?.fabric_agent_enabled || false)
        }
      } catch (error) {}
    }
    fetchConfig()
  }, [])

  const saveConversation = (query: string, response: string, threadId: string, agentType?: 'fabric' | 'rag' | 'web' | 'genie' | 'auto') => {
    try {
      if (currentConversationId) {
        setConversations(prev => (prev || []).map(conv => 
          conv.id === currentConversationId 
            ? { 
                ...conv, 
                last_query: query, 
                last_response: response,
                message_count: conv.message_count + 2,
                timestamp: Date.now(),
                agent_type: agentType || conv.agent_type
              }
            : conv
        ))
      } else {
        const title = query.length > 50 ? query.substring(0, 50) + '...' : query
        const newConversation: ConversationEntry = {
          id: Date.now().toString(),
          title: title,
          thread_id: threadId,
          last_query: query,
          last_response: response,
          message_count: 2,
          timestamp: Date.now(),
          agent_type: agentType || 'auto'
        }
        setConversations(prev => [newConversation, ...(prev || [])])
        setCurrentConversationId(newConversation.id)
      }
    } catch (error) {}
  }

  const loadConversation = async (conversation: ConversationEntry) => {
    try {
      setAppState('analyzing')
      setCurrentConversationId(conversation.id)
      setCurrentThreadId(conversation.thread_id)
      setShowHistory(false)
      setChatMessages([{
        id: 'loading-conversation',
        type: 'system',
        content: 'Loading conversation...',
        timestamp: Date.now(),
        isTyping: true
      }])
      const response = await fetch(`/api/thread/${conversation.thread_id}/messages`)
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.messages) {
          const loadedMessages: ChatMessage[] = result.messages.map((msg: any, index: number) => ({
            id: msg.id || `loaded-${index}`,
            type: msg.role === 'user' ? 'user' : 'agent',
            content: msg.content,
            agent: msg.role === 'assistant' ? (conversation.agent_type === 'genie' ? 'genie' : 
                                               conversation.agent_type === 'fabric' ? 'fabric' :
                                               conversation.agent_type === 'rag' ? 'rag' :
                                               conversation.agent_type === 'web' ? 'web' : 'purview') : undefined,
            timestamp: new Date(msg.created_at).getTime(),
            isTyping: false
          }))
          setChatMessages(loadedMessages)
        } else {
          setChatMessages([{
            id: 'load-error',
            type: 'system',
            content: `Could not load conversation messages: ${result.error || 'Unknown error'}. You can continue the conversation by asking a new question.`,
            timestamp: Date.now(),
            isTyping: false
          }])
        }
      } else {
        setChatMessages([{
          id: 'fetch-error',
          type: 'system',
          content: 'Failed to fetch conversation messages. You can continue the conversation by asking a new question.',
          timestamp: Date.now(),
          isTyping: false
        }])
      }
      setAppState('idle')
    } catch (error: any) {
      setChatMessages([{
        id: 'error',
        type: 'system',
        content: `Error loading conversation: ${error.message}. You can start a new conversation.`,
        timestamp: Date.now(),
        isTyping: false
      }])
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
    try {
      setConversations([])
      localStorage.removeItem('ai-conversations')
      setIsLoaded(false)
      setTimeout(() => setIsLoaded(true), 100)
    } catch (error) {}
  }

  const extractAgentFromAnalysis = (purviewMessage: string): 'fabric' | 'rag' | 'web' | 'genie' | null => {
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

  const extractActualAgentFromResponse = (processingResult: any): 'fabric' | 'rag' | 'web' | 'genie' | null => {
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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatMessages])

  const addMessage = (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ChatMessage = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now()
    }
    setChatMessages(prev => [...prev, newMessage])
    return newMessage.id
  }

  const updateMessage = (id: string, updates: Partial<ChatMessage>) => {
    setChatMessages(prev => prev.map(msg => 
      msg.id === id ? { ...msg, ...updates } : msg
    ))
  }

  const typeMessage = async (id: string, content: string, speed: number = 15) => {
    const words = content.split(' ')
    let currentText = ''
    for (let i = 0; i < words.length; i++) {
      currentText += (i > 0 ? ' ' : '') + words[i]
      updateMessage(id, { content: currentText, isTyping: true })
      const delay = words[i].includes('.') || words[i].includes('!') || words[i].includes('?') 
        ? speed * 3 
        : words[i].includes(',') || words[i].includes(';') 
        ? speed * 2 
        : speed
      await new Promise(resolve => setTimeout(resolve, delay))
    }
    updateMessage(id, { isTyping: false })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || appState !== 'idle') return
    const userQuery = query.trim()
    setQuery('')
    addMessage({
      type: 'user',
      content: userQuery
    })
    setAppState('analyzing')
    try {
      const purviewMessageId = addMessage({
        type: 'system',
        agent: 'purview',
        content: '',
        isTyping: true
      })
      await new Promise(resolve => setTimeout(resolve, 500))
      if (selectedMode !== 'auto') {
        let routingExplanation = ''
        switch (selectedMode) {
          case 'fabric':
            routingExplanation = 'User selected Fabric Data Agent. Routing directly to structured data analysis via NL2SQL.'
            break
          case 'rag':
            routingExplanation = 'User selected RAG Agent. Routing to document processing and semantic search.'
            break
          case 'web':
            routingExplanation = 'User selected Web Search. Routing to Bing search for real-time information.'
            break
          case 'genie':
            routingExplanation = 'User selected Databricks Genie Agent. Routing to natural language data analysis.'
            break
        }
        await typeMessage(purviewMessageId, `${routingExplanation}`, 15)
        updateMessage(purviewMessageId, { isTyping: true })
        await processDirectly(selectedMode, userQuery, routingExplanation, purviewMessageId)
        return
      }
      await typeMessage(purviewMessageId, `Analyzing query to determine optimal data source and processing method...`, 15)
      updateMessage(purviewMessageId, { isTyping: true })
      const analyzeResponse = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: userQuery })
      })
      if (!analyzeResponse.ok) {
        throw new Error(`Analysis failed: ${analyzeResponse.statusText}`)
      }
      const analysisResult = await analyzeResponse.json()
      if (!analysisResult.success) {
        throw new Error(analysisResult.error || 'Analysis failed')
      }
      await new Promise(resolve => setTimeout(resolve, 300))
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
      await new Promise(resolve => setTimeout(resolve, 600))
      await processWithConnectedAgents(userQuery, analysisResult, purviewMessageId)
    } catch (error: any) {
      setChatMessages(prev => prev.map(msg => ({ ...msg, isTyping: false })))
      addMessage({
        type: 'system',
        content: `Sorry, I encountered an error processing your request: ${error.message}. Please try again.`
      })
      setAppState('idle')
    }
  }

  const processDirectly = async (agent: SelectedMode, userQuery: string, purviewAnalysis: string, purviewMessageId?: string) => {
    if (agent === 'auto') {
      await processWithConnectedAgents(userQuery, { purview: purviewAnalysis }, purviewMessageId)
      return
    }
    const agentMessageId = addMessage({
      type: 'agent',
      agent: agent as any,
      content: '',
      isTyping: true
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
          agent: agent,
          thread_id: currentThreadId
        })
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
      let responseText = directResult.response
      if (directResult.annotations && directResult.annotations.length > 0) {
        directResult.annotations.forEach((annotation: any, index: number) => {
          const citationNumber = index + 1
          if (annotation.type === 'url_citation') {
            responseText += `\n\n**Source ${citationNumber}:** [${annotation.title}](${annotation.url})`
          } else if (annotation.type === 'file_citation') {
            responseText += `\n\n**Source ${citationNumber}:** ${annotation.file_name} - "${annotation.quote}"`
          }
        })
      }
      await typeMessage(agentMessageId, responseText, 12)
      const threadId = directResult.metadata?.thread_id || currentThreadId || 'unknown'
      saveConversation(userQuery, directResult.response, threadId, agent)
      setAppState('idle')
    } catch (error: any) {
      await typeMessage(agentMessageId, `I encountered an error while processing your request directly with the ${agent} agent: ${error.message}. Please try again.`)
      setAppState('idle')
    }
  }

  const processWithConnectedAgents = async (userQuery: string, analysisResult: any, purviewMessageId?: string) => {
    const identifiedAgent = extractAgentFromAnalysis(analysisResult.purview)
    const agentMessageId = addMessage({
      type: 'agent',
      agent: identifiedAgent || 'purview',
      content: '',
      isTyping: true
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
          thread_id: currentThreadId
        })
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
      let responseText = processingResult.response
      const actualAgent = extractActualAgentFromResponse(processingResult)
      if (actualAgent && actualAgent !== identifiedAgent) {
        updateMessage(agentMessageId, { agent: actualAgent })
        const routingNote = `**Final Routing Decision**: ${actualAgent} agent selected and provided this response based on query context and analysis.`
        responseText = routingNote + "\n\n" + responseText
      } else if (actualAgent && actualAgent === identifiedAgent) {
        const routingNote = `**Routing Confirmed**: ${actualAgent} agent processed this request as anticipated from catalog analysis.`
        responseText = routingNote + "\n\n" + responseText
      } else if (actualAgent) {
        const routingNote = `**Final Routing Decision**: ${actualAgent} agent selected to handle this request.`
        responseText = routingNote + "\n\n" + responseText
      }
      if (processingResult.annotations && processingResult.annotations.length > 0) {
        processingResult.annotations.forEach((annotation: any, index: number) => {
          const citationNumber = index + 1
          if (annotation.type === 'url_citation') {
            responseText += `\n\n**Source ${citationNumber}:** [${annotation.title}](${annotation.url})`
          } else if (annotation.type === 'file_citation') {
            responseText += `\n\n**Source ${citationNumber}:** ${annotation.file_name} - "${annotation.quote}"`
          }
        })
      }
      await typeMessage(agentMessageId, responseText, 12)
      const finalAgent = actualAgent || identifiedAgent || 'auto'
      const threadId = processingResult.metadata?.thread_id || currentThreadId || 'unknown'
      saveConversation(userQuery, processingResult.response, threadId, finalAgent)
      setAppState('idle')
    } catch (error: any) {
      await typeMessage(agentMessageId, `I encountered an error while processing your request through the connected agent service: ${error.message}. Please try again or contact support if the issue persists.`)
      setAppState('idle')
    }
  }

  const resetState = () => {
    setAppState('idle')
    setChatMessages([])
  }

  const getMessageIcon = (message: ChatMessage) => {
    if (message.type === 'user') return <User size={16} />
    if (message.agent === 'purview') return <Brain size={16} />
    if (message.agent === 'fabric') return <Database size={16} />
    if (message.agent === 'rag') return <FileText size={16} />
    if (message.agent === 'web') return <Globe size={16} />
    if (message.agent === 'redirect') return <MapPin size={16} />
    if (message.agent === 'genie') return <Code size={16} />
    return <Bot size={16} />
  }

  const getMessageBadge = (message: ChatMessage) => {
    if (message.type === 'user') return 'You'
    if (message.agent === 'purview') return 'Purview Analysis'
    if (message.agent === 'fabric') return 'Fabric Data Agent'
    if (message.agent === 'rag') return 'RAG Agent'
    if (message.agent === 'web') return 'Web Search Agent'
    if (message.agent === 'redirect') return 'Purview Redirect'
    if (message.agent === 'genie') return 'Databricks Genie Agent'
    return 'System'
  }

  const getAgentColor = (message: ChatMessage) => {
    if (message.type === 'user') return 'user'
    if (message.agent === 'purview') return 'purview'
    if (message.agent === 'fabric') return 'fabric'
    if (message.agent === 'rag') return 'rag'
    if (message.agent === 'web') return 'web'
    if (message.agent === 'redirect') return 'redirect'
    if (message.agent === 'genie') return 'genie'
    return 'system'
  }

  const formatTimestamp = (timestamp: number) => {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(new Date(timestamp))
  }

  return (
    <div className="min-h-screen gradient-bg">
      <div className="container mx-auto px-6 py-6 max-w-7xl h-screen flex flex-col">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
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
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="fixed inset-0 z-50 flex items-center justify-end p-6"
                  onClick={() => setShowHistory(false)}
                >
                  <div className="absolute inset-0 history-overlay-backdrop" />
                  <motion.div
                    initial={{ opacity: 0, x: 400, scale: 0.95 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: 400, scale: 0.95 }}
                    transition={{ duration: 0.3, ease: "easeOut" }}
                    className="relative w-full max-w-md h-[80vh] glass-card border-0 p-6 shadow-2xl"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-accent/20">
                          <Clock className="text-accent" size={20} />
                        </div>
                        <h2 className="text-lg font-semibold">Recent History</h2>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowHistory(false)}
                        className="h-8 w-8 p-0 hover:bg-accent/20 rounded-lg"
                      >
                        <X size={16} />
                      </Button>
                    </div>
                    
                    <ScrollArea className="h-[calc(100%-5rem)]">
                      <div className="space-y-3">
                        {(conversations || []).slice(0, 5).map((conv, index) => (
                          <motion.div
                            key={conv.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="history-item p-4 rounded-xl cursor-pointer group hover:bg-accent/10 transition-all duration-200"
                            onClick={() => loadConversation(conv)}
                          >
                            <div className="flex items-center gap-2 mb-2">
                              <Badge 
                                variant={conv.agent_type === 'fabric' ? 'default' : conv.agent_type === 'rag' ? 'secondary' : 'outline'} 
                                className="text-xs px-2 py-1"
                              >
                                {conv.agent_type === 'fabric' ? 'Fabric Agent' : 
                                 conv.agent_type === 'rag' ? 'RAG Agent' : 
                                 conv.agent_type === 'web' ? 'Web Agent' : 
                                 conv.agent_type === 'genie' ? 'Genie Agent' : 
                                 conv.agent_type === 'auto' ? 'Auto Route' : 
                                 'Auto Route'}
                              </Badge>
                              <span className="text-xs text-muted-foreground ml-auto">
                                {formatTimestamp(conv.timestamp)}
                              </span>
                            </div>
                            <p className="text-sm font-medium mb-2 line-clamp-2 group-hover:text-accent transition-colors">
                              {conv.title}
                            </p>
                            <p className="text-xs text-muted-foreground line-clamp-1">
                              {conv.last_response.substring(0, 100)}...
                            </p>
                            <div 
                              className="mt-2 pt-2 border-t border-border/30 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                className="h-6 px-2 text-xs hover:bg-accent/20 hover:text-accent"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  loadConversation(conv)
                                }}
                              >
                                Continue conversation
                              </Button>
                            </div>
                          </motion.div>
                        ))}
                        {(!conversations || conversations.length === 0) && (
                          <div className="text-center py-12">
                            <Bot className="text-muted-foreground mx-auto mb-4" size={40} />
                            <p className="text-sm text-muted-foreground font-medium">No conversations yet</p>
                            <p className="text-xs text-muted-foreground mt-1">Start by asking a question below</p>
                          </div>
                        )}
                      </div>
                    </ScrollArea>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
            
            <div className="flex-1 flex flex-col min-h-0 relative">
              {chatMessages.length === 0 ? (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex-1 flex items-center justify-center p-12"
                >
                  <div className="text-center max-w-2xl">
                    <motion.div
                      animate={{ 
                        rotate: [0, 5, -5, 0],
                        scale: [1, 1.05, 1]
                      }}
                      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                      className="mb-8"
                    >
                      <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-accent/20 via-primary/20 to-accent/10 backdrop-blur border border-accent/30">
                        <Sparkles className="text-accent" size={36} />
                      </div>
                    </motion.div>
                    <h2 className="text-4xl font-bold text-gradient mb-6">Purview Router</h2>
                    <p className="text-lg text-muted-foreground leading-relaxed mb-8">
                      Route your queries through Microsoft Purview to find the right data source and specialist agent. 
                      Whether you need structured analytics, document processing, or real-time information, we'll connect you to the optimal solution.
                    </p>
                    <div className="flex flex-wrap justify-center gap-3">
                      <Badge variant="outline" className="px-4 py-2 bg-red-500/15 text-red-400 border-red-400/30">
                        Structured Data • Databricks
                      </Badge>
                      <Badge variant="outline" className="px-4 py-2 bg-white/10 text-white border-white/30">
                        Unstructured Docs • RAG
                      </Badge>
                      <Badge variant="outline" className="px-4 py-2 bg-orange-500/15 text-orange-400 border-orange-400/30">
                        Real-Time Info • Web
                      </Badge>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <Card className="flex-1 glass-card border-0 m-0 relative min-h-0">
                  <div className="absolute inset-0 overflow-hidden">
                    <div className="h-full overflow-y-auto scrollbar-hide">
                      <div className="p-6 space-y-6 max-w-4xl mx-auto">
                        {chatMessages.map((message, index) => (
                          <motion.div
                            key={message.id}
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ duration: 0.3, delay: index * 0.1 }}
                            className="relative"
                          >
                            {message.isTyping && (
                              <div className={`loading-border ${
                                getAgentColor(message) === 'user' ? 'loading-border-user' :
                                getAgentColor(message) === 'purview' ? 'loading-border-purview' :
                                getAgentColor(message) === 'fabric' ? 'loading-border-fabric' :
                                getAgentColor(message) === 'rag' ? 'loading-border-rag' :
                                getAgentColor(message) === 'web' ? 'loading-border-web' :
                                getAgentColor(message) === 'genie' ? 'loading-border-genie' :
                                ''
                              }`} />
                            )}
                            <div className="flex gap-4">
                              <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
                                getAgentColor(message) === 'user' ? 'bg-gradient-to-br from-blue-500/20 to-blue-600/30 text-blue-400 border border-blue-400/40' :
                                getAgentColor(message) === 'purview' ? 'bg-gradient-to-br from-purple-500/30 to-violet-500/20 text-purple-400 border border-purple-400/40' :
                                getAgentColor(message) === 'fabric' ? 'bg-gradient-to-br from-emerald-500/30 to-green-500/20 text-emerald-400 border border-emerald-400/40' :
                                getAgentColor(message) === 'rag' ? 'bg-gradient-to-br from-secondary/40 to-muted/30 text-secondary-foreground border border-secondary-60' :
                                getAgentColor(message) === 'web' ? 'bg-gradient-to-br from-orange-500/30 to-amber-500/20 text-orange-400 border border-orange-400/40' :
                                getAgentColor(message) === 'redirect' ? 'bg-gradient-to-br from-muted/40 to-secondary/20 text-muted-foreground border border-muted/60' :
                                getAgentColor(message) === 'genie' ? 'bg-gradient-to-br from-rose-500/30 to-pink-500/20 text-rose-400 border border-rose-400/40' :
                                'bg-muted/50 text-muted-foreground border border-border/50'
                              }`}>
                                {getMessageIcon(message)}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3 mb-3">
                                  <Badge 
                                    variant="outline" 
                                    className={`text-xs font-medium px-3 py-1 rounded-full ${
                                      getAgentColor(message) === 'user' ? 'bg-blue-500/10 text-blue-400 border-blue-400/30' :
                                      getAgentColor(message) === 'purview' ? 'bg-purple-500/10 text-purple-400 border-purple-400/30' :
                                      getAgentColor(message) === 'fabric' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-400/30' :
                                      getAgentColor(message) === 'rag' ? 'bg-secondary/20 text-secondary-foreground border-secondary-50' :
                                      getAgentColor(message) === 'web' ? 'bg-orange-500/10 text-orange-400 border-orange-400/30' :
                                      getAgentColor(message) === 'redirect' ? 'bg-muted/20 text-muted-foreground border-muted/50' :
                                      getAgentColor(message) === 'genie' ? 'bg-rose-500/10 text-rose-400 border-rose-400/30' :
                                      'bg-muted/30 text-muted-foreground border-border/50'
                                    }`}
                                  >
                                    {getMessageBadge(message)}
                                  </Badge>
                                  {message.isTyping && (
                                    <div className="flex items-center gap-3">
                                      <div className="flex gap-1">
                                        {[0, 1, 2].map((i) => (
                                          <motion.div
                                            key={i}
                                            className={`w-1.5 h-1.5 rounded-full ${
                                              getAgentColor(message) === 'user' ? 'bg-blue-400' :
                                              getAgentColor(message) === 'purview' ? 'bg-purple-400' :
                                              getAgentColor(message) === 'fabric' ? 'bg-emerald-400' :
                                              getAgentColor(message) === 'rag' ? 'bg-secondary-foreground' :
                                              getAgentColor(message) === 'web' ? 'bg-orange-400' :
                                              getAgentColor(message) === 'genie' ? 'bg-rose-400' :
                                              'bg-muted-foreground'
                                            }`}
                                            animate={{
                                              scale: [1, 1.3, 1],
                                              opacity: [0.5, 1, 0.5]
                                            }}
                                            transition={{
                                              duration: 0.8,
                                              repeat: Infinity,
                                              delay: i * 0.2,
                                              ease: "easeInOut"
                                            }}
                                          />
                                        ))}
                                      </div>
                                      <span className="text-xs text-muted-foreground">thinking...</span>
                                    </div>
                                  )}
                                </div>
                                <div className={`rounded-2xl p-4 ${
                                  message.type === 'user' 
                                    ? 'bg-gradient-to-r from-blue-500/20 to-blue-600/30 text-blue-100 border border-blue-400/30 ml-8' 
                                    : 'bg-card/80 backdrop-blur border border-border/30'
                                }`}>
                                  <div className="text-sm leading-relaxed break-words">
                                    {message.content ? (
                                      <MessageContent 
                                        content={message.content} 
                                        isUser={message.type === 'user'} 
                                      />
                                    ) : (
                                      <span className="text-muted-foreground italic">Processing...</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        ))}
                        <div ref={messagesEndRef} />
                      </div>
                    </div>
                  </div>
                  <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-card/80 to-transparent pointer-events-none"></div>
                </Card>
              )}
            </div>

            <Card className="glass-card border-0 p-6 mt-6 space-y-4">
              {chatMessages.length === 0 && (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground font-medium">Try these sample queries:</p>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "What is the cost of Microsoft Encarta?",
                      "What is the weather like tomorrow in Madrid?",
                      "What is the maximum taxi fare amount recorded?",
                      "What is the maximum taxi fare amount recorded in New York City?",
                      "Tell me about this month's ContosoSales data"
                    ].map((prompt, index) => (
                      <Button
                        key={index}
                        variant="outline"
                        size="sm"
                        onClick={() => setQuery(prompt)}
                        className="text-xs h-8 px-3 rounded-lg bg-muted/30 hover:bg-accent/20 hover:text-accent border-border/50 hover:border-accent/30 transition-all duration-300"
                        disabled={appState !== 'idle'}
                      >
                        {prompt}
                      </Button>
                    ))}
                  </div>
                </div>
              )}

              <form onSubmit={handleSubmit} className="flex gap-3 items-end">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="h-8 px-3 rounded-lg bg-muted/30 hover:bg-accent/20 border border-border/50 hover:border-accent/30 transition-all duration-300"
                          disabled={appState !== 'idle'}
                        >
                          <Settings size={14} className="mr-2" />
                          {selectedMode === 'auto' ? (
                            <>Auto Route <span className="text-primary">(using Purview)</span></>
                          ) :
                           selectedMode === 'fabric' ? 'Fabric Agent' :
                           selectedMode === 'rag' ? 'RAG Agent' :
                           selectedMode === 'web' ? 'Web Agent' :
                           selectedMode === 'genie' ? 'Databricks Genie' : 'Auto Route'}
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="start" className="w-64 glass-card border-border/50">
                        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">
                          Agent Selection
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        
                        <DropdownMenuItem 
                          onClick={() => setSelectedMode('auto')}
                          className={selectedMode === 'auto' ? 'bg-accent/20' : ''}
                        >
                          <Brain size={16} className="mr-2 text-accent" />
                          <div className="font-medium">
                            Auto Route <span className="text-primary">(using Purview)</span>
                          </div>
                        </DropdownMenuItem>
                        
                        {fabricAgentEnabled && (
                          <DropdownMenuItem 
                            onClick={() => setSelectedMode('fabric')}
                            className={selectedMode === 'fabric' ? 'bg-primary/20' : ''}
                          >
                            <Database size={16} className="mr-2 text-primary" />
                            <div className="font-medium">Fabric Data Agent</div>
                          </DropdownMenuItem>
                        )}
                        
                        <DropdownMenuItem 
                          onClick={() => setSelectedMode('genie')}
                          className={selectedMode === 'genie' ? 'bg-accent/20' : ''}
                        >
                          <Code size={16} className="mr-2 text-accent" />
                          <div className="font-medium">Databricks Genie</div>
                        </DropdownMenuItem>
                        
                        <DropdownMenuItem 
                          onClick={() => setSelectedMode('rag')}
                          className={selectedMode === 'rag' ? 'bg-secondary/20' : ''}
                        >
                          <FileText size={16} className="mr-2 text-secondary-foreground" />
                          <div className="font-medium">RAG Agent</div>
                        </DropdownMenuItem>
                        
                        <DropdownMenuSeparator />
                        
                        <DropdownMenuItem 
                          onClick={() => setSelectedMode('web')}
                          className={selectedMode === 'web' ? 'bg-accent/20' : ''}
                        >
                          <Search size={16} className="mr-2 text-accent" />
                          <div className="font-medium">Web Search</div>
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>

                    {selectedMode !== 'auto' && (
                      <Badge variant="outline" className="text-xs px-2 py-1 bg-accent/10 text-accent border-accent/30">
                        Manual mode
                      </Badge>
                    )}
                  </div>

                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={
                      selectedMode === 'fabric' ? 'Ask about customer data, sales analytics, reports...' :
                      selectedMode === 'rag' ? 'Ask about invoices, documents, contracts...' :
                      selectedMode === 'web' ? 'Ask about current events, general knowledge...' :
                      selectedMode === 'genie' ? 'Ask about data analysis, SQL queries, insights...' :
                      fabricAgentEnabled ? 'Ask about customer data, invoice analysis, reports...' : 'Ask about data analysis, documents, web search...'
                    }
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

export default App