import { motion } from 'framer-motion'
import { Clock, X, Bot } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { ConversationEntry } from '@/types/chat'

interface HistoryPanelProps {
  conversations: ConversationEntry[]
  onSelect: (conversation: ConversationEntry) => void
  onClose: () => void
}

export function HistoryPanel({ conversations, onSelect, onClose }: HistoryPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      className="fixed inset-0 z-50 flex items-center justify-end p-6"
      onClick={onClose}
    >
      <div className="absolute inset-0 history-overlay-backdrop" />
      <motion.div
        initial={{ opacity: 0, x: 400, scale: 0.95 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 400, scale: 0.95 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="relative w-full max-w-md h-[80vh] glass-card border-0 p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
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
            onClick={onClose}
            className="h-8 w-8 p-0 hover:bg-accent/20 rounded-lg"
          >
            <X size={16} />
          </Button>
        </div>

        <ScrollArea className="h-[calc(100%-5rem)]">
          <div className="space-y-3">
            {conversations.slice(0, 5).map((conversation, index) => (
              <motion.div
                key={conversation.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="history-item p-4 rounded-xl cursor-pointer group hover:bg-accent/10 transition-all duration-200"
                onClick={() => onSelect(conversation)}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Badge
                    variant={getBadgeVariant(conversation.agent_type)}
                    className="text-xs px-2 py-1"
                  >
                    {getBadgeLabel(conversation.agent_type)}
                  </Badge>
                  <span className="text-xs text-muted-foreground ml-auto">
                    {formatTimestamp(conversation.timestamp)}
                  </span>
                </div>
                <p className="text-sm font-medium mb-2 line-clamp-2 group-hover:text-accent transition-colors">
                  {conversation.title}
                </p>
                <p className="text-xs text-muted-foreground line-clamp-1">
                  {conversation.last_response.substring(0, 100)}...
                </p>
                <div className="mt-2 pt-2 border-t border-border/30 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs hover:bg-accent/20 hover:text-accent"
                    onClick={(event) => {
                      event.stopPropagation()
                      onSelect(conversation)
                    }}
                  >
                    Continue conversation
                  </Button>
                </div>
              </motion.div>
            ))}
            {conversations.length === 0 && (
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
  )
}

function getBadgeVariant(agentType: ConversationEntry['agent_type']) {
  switch (agentType) {
    case 'fabric':
      return 'default'
    case 'rag':
      return 'secondary'
    default:
      return 'outline'
  }
}

function getBadgeLabel(agentType: ConversationEntry['agent_type']) {
  switch (agentType) {
    case 'fabric':
      return 'Fabric Agent'
    case 'rag':
      return 'RAG Agent'
    case 'web':
      return 'Web Agent'
    case 'genie':
      return 'Genie Agent'
    case 'auto':
      return 'Auto Route'
    case 'redirect':
      return 'Purview Redirect'
    default:
      return 'Auto Route'
  }
}

function formatTimestamp(timestamp: number) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(timestamp))
}
