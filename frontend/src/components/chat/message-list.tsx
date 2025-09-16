import { motion } from 'framer-motion'
import type { MutableRefObject } from 'react'
import type { LucideIcon } from 'lucide-react'
import { User, Brain, Database, FileText, Globe, MapPin, Code, Bot } from 'lucide-react'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { ChatMessage } from '@/types/chat'

import { MessageContent } from './message-content'

interface MessageListProps {
  messages: ChatMessage[]
  endRef: MutableRefObject<HTMLDivElement | null>
}

type MessageStyleKey = 'user' | 'purview' | 'fabric' | 'rag' | 'web' | 'redirect' | 'genie' | 'system'

interface MessageStyle {
  icon: LucideIcon
  label: string
  avatarClass: string
  badgeClass: string
  typingDotClass: string
  typingBorderClass?: string
}

const MESSAGE_STYLES: Record<MessageStyleKey, MessageStyle> = {
  user: {
    icon: User,
    label: 'You',
    avatarClass:
      'bg-gradient-to-br from-blue-500/20 to-blue-600/30 text-blue-400 border border-blue-400/40',
    badgeClass: 'bg-blue-500/10 text-blue-400 border-blue-400/30',
    typingDotClass: 'bg-blue-400',
    typingBorderClass: 'loading-border-user',
  },
  purview: {
    icon: Brain,
    label: 'Purview Analysis',
    avatarClass:
      'bg-gradient-to-br from-purple-500/30 to-violet-500/20 text-purple-400 border border-purple-400/40',
    badgeClass: 'bg-purple-500/10 text-purple-400 border-purple-400/30',
    typingDotClass: 'bg-purple-400',
    typingBorderClass: 'loading-border-purview',
  },
  fabric: {
    icon: Database,
    label: 'Fabric Data Agent',
    avatarClass:
      'bg-gradient-to-br from-emerald-500/30 to-green-500/20 text-emerald-400 border border-emerald-400/40',
    badgeClass: 'bg-emerald-500/10 text-emerald-400 border-emerald-400/30',
    typingDotClass: 'bg-emerald-400',
    typingBorderClass: 'loading-border-fabric',
  },
  rag: {
    icon: FileText,
    label: 'RAG Agent',
    avatarClass:
      'bg-gradient-to-br from-secondary/40 to-muted/30 text-secondary-foreground border border-secondary-60',
    badgeClass: 'bg-secondary/20 text-secondary-foreground border-secondary-50',
    typingDotClass: 'bg-secondary-foreground',
    typingBorderClass: 'loading-border-rag',
  },
  web: {
    icon: Globe,
    label: 'Web Search Agent',
    avatarClass:
      'bg-gradient-to-br from-orange-500/30 to-amber-500/20 text-orange-400 border border-orange-400/40',
    badgeClass: 'bg-orange-500/10 text-orange-400 border-orange-400/30',
    typingDotClass: 'bg-orange-400',
    typingBorderClass: 'loading-border-web',
  },
  redirect: {
    icon: MapPin,
    label: 'Purview Redirect',
    avatarClass:
      'bg-gradient-to-br from-muted/40 to-secondary/20 text-muted-foreground border border-muted/60',
    badgeClass: 'bg-muted/20 text-muted-foreground border-muted/50',
    typingDotClass: 'bg-muted-foreground',
  },
  genie: {
    icon: Code,
    label: 'Databricks Genie Agent',
    avatarClass:
      'bg-gradient-to-br from-rose-500/30 to-pink-500/20 text-rose-400 border border-rose-400/40',
    badgeClass: 'bg-rose-500/10 text-rose-400 border-rose-400/30',
    typingDotClass: 'bg-rose-400',
    typingBorderClass: 'loading-border-genie',
  },
  system: {
    icon: Bot,
    label: 'System',
    avatarClass: 'bg-muted/50 text-muted-foreground border border-border/50',
    badgeClass: 'bg-muted/30 text-muted-foreground border-border/50',
    typingDotClass: 'bg-muted-foreground',
  },
}

export function MessageList({ messages, endRef }: MessageListProps) {
  return (
    <Card className="flex-1 glass-card border-0 m-0 relative min-h-0">
      <div className="absolute inset-0 overflow-hidden">
        <div className="h-full overflow-y-auto scrollbar-hide">
          <div className="p-6 space-y-6 max-w-4xl mx-auto">
            {messages.map((message, index) => {
              const styleKey = resolveMessageStyle(message)
              const style = MESSAGE_STYLES[styleKey]
              const Icon = style.icon
              const showTyping = Boolean(message.isTyping)
              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="relative"
                >
                  {showTyping && (
                    <div className={`loading-border ${style.typingBorderClass ?? ''}`} />
                  )}
                  <div className="flex gap-4">
                    <div
                      className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${style.avatarClass}`}
                    >
                      <Icon size={16} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3">
                        <Badge
                          variant="outline"
                          className={`text-xs font-medium px-3 py-1 rounded-full ${style.badgeClass}`}
                        >
                          {style.label}
                        </Badge>
                        {showTyping && (
                          <div className="flex items-center gap-3">
                            <div className="flex gap-1">
                              {[0, 1, 2].map((i) => (
                                <motion.div
                                  key={i}
                                  className={`w-1.5 h-1.5 rounded-full ${style.typingDotClass}`}
                                  animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
                                  transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.2, ease: 'easeInOut' }}
                                />
                              ))}
                            </div>
                            <span className="text-xs text-muted-foreground">thinking...</span>
                          </div>
                        )}
                      </div>
                      <div
                        className={`rounded-2xl p-4 ${
                          message.type === 'user'
                            ? 'bg-gradient-to-r from-blue-500/20 to-blue-600/30 text-blue-100 border border-blue-400/30 ml-8'
                            : 'bg-card/80 backdrop-blur border border-border/30'
                        }`}
                      >
                        <div className="text-sm leading-relaxed break-words">
                          {message.content ? (
                            <MessageContent content={message.content} isUser={message.type === 'user'} />
                          ) : (
                            <span className="text-muted-foreground italic">Processing...</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )
            })}
            <div ref={endRef} />
          </div>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-card/80 to-transparent pointer-events-none" />
    </Card>
  )
}

function resolveMessageStyle(message: ChatMessage): MessageStyleKey {
  if (message.type === 'user') {
    return 'user'
  }

  switch (message.agent) {
    case 'purview':
      return 'purview'
    case 'fabric':
      return 'fabric'
    case 'rag':
      return 'rag'
    case 'web':
      return 'web'
    case 'redirect':
      return 'redirect'
    case 'genie':
      return 'genie'
    default:
      return 'system'
  }
}
