import { Button } from '@/components/ui/button'

interface SamplePromptsProps {
  onSelect: (prompt: string) => void
  disabled: boolean
}

const SAMPLE_PROMPTS = [
  'What is the cost of Microsoft Encarta?',
  'What is the weather like tomorrow in Madrid?',
  'What is the maximum taxi fare amount recorded?',
  'What is the maximum taxi fare amount recorded in New York City?',
  "Tell me about this month's ContosoSales data",
] as const

export function SamplePrompts({ onSelect, disabled }: SamplePromptsProps) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground font-medium">Try these sample queries:</p>
      <div className="flex flex-wrap gap-2">
        {SAMPLE_PROMPTS.map((prompt) => (
          <Button
            key={prompt}
            variant="outline"
            size="sm"
            onClick={() => onSelect(prompt)}
            className="text-xs h-8 px-3 rounded-lg bg-muted/30 hover:bg-accent/20 hover:text-accent border-border/50 hover:border-accent/30 transition-all duration-300"
            disabled={disabled}
          >
            {prompt}
          </Button>
        ))}
      </div>
    </div>
  )
}
