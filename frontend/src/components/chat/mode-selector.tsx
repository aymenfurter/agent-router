import { Settings, Brain, Database, FileText, Search, Code } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import type { SelectedMode } from '@/types/chat'

interface ModeSelectorProps {
  value: SelectedMode
  onChange: (mode: SelectedMode) => void
  disabled: boolean
  fabricAgentEnabled: boolean
}

export function ModeSelector({ value, onChange, disabled, fabricAgentEnabled }: ModeSelectorProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-8 px-3 rounded-lg bg-muted/30 hover:bg-accent/20 border border-border/50 hover:border-accent/30 transition-all duration-300"
          disabled={disabled}
        >
          <Settings size={14} className="mr-2" />
          {renderButtonLabel(value)}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64 glass-card border-border/50">
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">
          Agent Selection
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => onChange('auto')}
          className={cn(value === 'auto' && 'bg-accent/20')}
        >
          <Brain size={16} className="mr-2 text-accent" />
          <div className="font-medium">
            Auto Route <span className="text-primary">(using Purview)</span>
          </div>
        </DropdownMenuItem>

        {fabricAgentEnabled && (
          <DropdownMenuItem
            onClick={() => onChange('fabric')}
            className={cn(value === 'fabric' && 'bg-primary/20')}
          >
            <Database size={16} className="mr-2 text-primary" />
            <div className="font-medium">Fabric Data Agent</div>
          </DropdownMenuItem>
        )}

        <DropdownMenuItem
          onClick={() => onChange('genie')}
          className={cn(value === 'genie' && 'bg-accent/20')}
        >
          <Code size={16} className="mr-2 text-accent" />
          <div className="font-medium">Databricks Genie</div>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={() => onChange('rag')}
          className={cn(value === 'rag' && 'bg-secondary/20')}
        >
          <FileText size={16} className="mr-2 text-secondary-foreground" />
          <div className="font-medium">RAG Agent</div>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={() => onChange('web')}
          className={cn(value === 'web' && 'bg-accent/20')}
        >
          <Search size={16} className="mr-2 text-accent" />
          <div className="font-medium">Web Search</div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function renderButtonLabel(value: SelectedMode) {
  switch (value) {
    case 'fabric':
      return 'Fabric Agent'
    case 'rag':
      return 'RAG Agent'
    case 'web':
      return 'Web Agent'
    case 'genie':
      return 'Databricks Genie'
    default:
      return (
        <>
          Auto Route <span className="text-primary">(using Purview)</span>
        </>
      )
  }
}
