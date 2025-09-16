import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'

import { Badge } from '@/components/ui/badge'

export function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex-1 flex items-center justify-center p-12"
    >
      <div className="text-center max-w-2xl">
        <motion.div
          animate={{ rotate: [0, 5, -5, 0], scale: [1, 1.05, 1] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
          className="mb-8"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-accent/20 via-primary/20 to-accent/10 backdrop-blur border border-accent/30">
            <Sparkles className="text-accent" size={36} />
          </div>
        </motion.div>
        <h2 className="text-4xl font-bold text-gradient mb-6">Purview Router</h2>
        <p className="text-lg text-muted-foreground leading-relaxed mb-8">
          Route your queries through Microsoft Purview to find the right data source and specialist agent. Whether you need structured analytics, document processing, or real-time information, we'll connect you to the optimal solution.
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
  )
}
