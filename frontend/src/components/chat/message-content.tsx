import type { ReactNode } from 'react'

interface MessageContentProps {
  content: string
  isUser: boolean
}

const CODE_BLOCK_REGEX = /```(\w+)?\n([\s\S]*?)```/g

export function MessageContent({ content, isUser }: MessageContentProps) {
  return <div className="space-y-1">{parseMessageContent(content, isUser)}</div>
}

function parseMessageContent(content: string, isUser: boolean): ReactNode[] {
  const parts: ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null
  let blockIndex = 0

  CODE_BLOCK_REGEX.lastIndex = 0

  while ((match = CODE_BLOCK_REGEX.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const beforeBlock = content.slice(lastIndex, match.index)
      parts.push(...renderRegularSegments(beforeBlock, isUser, `segment-${blockIndex}-pre`))
    }

    parts.push(renderCodeBlock(match[1], match[2], `code-${blockIndex}`))

    lastIndex = match.index + match[0].length
    blockIndex += 1
  }

  if (lastIndex < content.length) {
    const afterBlock = content.slice(lastIndex)
    parts.push(...renderRegularSegments(afterBlock, isUser, `segment-${blockIndex}-post`))
  }

  return parts
}

function renderRegularSegments(text: string, isUser: boolean, keyPrefix: string): ReactNode[] {
  const segments: ReactNode[] = []
  const lines = text.split('\n')
  let currentTable: string[] = []

  const flushTable = () => {
    if (currentTable.length === 0) {
      return
    }
    const table = renderTable(currentTable, `${keyPrefix}-table-${segments.length}`)
    if (table) {
      segments.push(table)
    }
    currentTable = []
  }

  lines.forEach((line, index) => {
    const key = `${keyPrefix}-line-${index}`
    const pipeCount = (line.match(/\|/g) ?? []).length
    if (pipeCount >= 2) {
      currentTable.push(line)
      return
    }

    flushTable()

    if (!line.trim()) {
      return
    }

    segments.push(
      <div key={key} className="mb-2">
        {renderFormattedText(line, isUser, `${key}-text`)}
      </div>
    )
  })

  flushTable()
  return segments
}

function renderTable(rows: string[], key: string): ReactNode | null {
  if (rows.length === 0) {
    return null
  }

  const tableData = rows
    .map((row) => row.split('|').map((cell) => cell.trim()).filter(Boolean))
    .filter((row) => row.length > 0)

  if (tableData.length === 0) {
    return null
  }

  const hasHeader =
    tableData.length > 1 &&
    tableData[0].every(
      (cell) => !/^\d{4}-\d{2}-\d{2}/.test(cell) && !/^\d+\.?\d*$/.test(cell)
    )

  const dataRows = hasHeader ? tableData.slice(1) : tableData

  return (
    <div key={key} className="my-4 overflow-x-auto">
      <table className="w-full text-xs border border-border/50 rounded-lg overflow-hidden">
        {hasHeader && (
          <thead>
            <tr className="bg-muted/50">
              {tableData[0].map((header, index) => (
                <th
                  key={`${key}-header-${index}`}
                  className="px-3 py-2 text-left font-medium border-r border-border/30 last:border-r-0"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {dataRows.map((row, rowIndex) => (
            <tr
              key={`${key}-row-${rowIndex}`}
              className={`${rowIndex % 2 === 0 ? 'bg-background/50' : 'bg-muted/20'} hover:bg-accent/10 transition-colors`}
            >
              {row.map((cell, cellIndex) => (
                <td
                  key={`${key}-row-${rowIndex}-cell-${cellIndex}`}
                  className="px-3 py-2 border-r border-border/30 last:border-r-0 font-mono"
                >
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

function renderFormattedText(text: string, isUser: boolean, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const boldRegex = /\*\*(.*?)\*\*/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let segmentIndex = 0

  while ((match = boldRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const plainText = text.slice(lastIndex, match.index)
      nodes.push(...renderLinks(plainText, `${keyPrefix}-plain-${segmentIndex}`))
      segmentIndex += 1
    }

    nodes.push(
      <span
        key={`${keyPrefix}-bold-${match.index}`}
        className={`font-semibold ${isUser ? 'text-accent-foreground' : 'text-foreground'}`}
      >
        {match[1]}
      </span>
    )

    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    const plainText = text.slice(lastIndex)
    nodes.push(...renderLinks(plainText, `${keyPrefix}-plain-${segmentIndex}`))
  }

  return nodes.length > 0 ? nodes : renderLinks(text, keyPrefix)
}

function renderLinks(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = []
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  let linkIndex = 0

  while ((match = linkRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const beforeLink = text.slice(lastIndex, match.index)
      if (beforeLink) {
        nodes.push(
          <span key={`${keyPrefix}-text-${linkIndex}`}>{beforeLink}</span>
        )
        linkIndex += 1
      }
    }

    nodes.push(
      <a
        key={`${keyPrefix}-link-${linkIndex}`}
        href={match[2]}
        target="_blank"
        rel="noopener noreferrer"
        className="text-accent hover:text-accent/80 underline"
      >
        {match[1]}
      </a>
    )
    linkIndex += 1
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    const afterLink = text.slice(lastIndex)
    if (afterLink) {
      nodes.push(
        <span key={`${keyPrefix}-text-${linkIndex}`}>{afterLink}</span>
      )
    }
  }

  return nodes
}

function renderCodeBlock(language: string | undefined, code: string, key: string): ReactNode {
  return (
    <div key={key} className="my-4 rounded-lg bg-muted/50 border border-border/50 overflow-hidden">
      {language && (
        <div className="px-3 py-2 bg-muted/80 text-xs font-medium text-muted-foreground border-b border-border/30">
          {language.toUpperCase()}
        </div>
      )}
      <pre className="p-3 text-xs overflow-x-auto">
        <code className="text-foreground">{code}</code>
      </pre>
    </div>
  )
}
