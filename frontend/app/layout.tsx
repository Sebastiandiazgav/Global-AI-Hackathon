import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'MyAgent - Enterprise AI Copilot',
  description: 'Multi-agent AI system for enterprise operations. Powered by Qwen Cloud + LangGraph + MCP Protocol.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
