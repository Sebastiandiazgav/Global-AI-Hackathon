'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import SmartPOSLayout from '@/components/SmartPOSLayout'
import ChatPanel from '@/components/ChatPanel'
import WorkflowPanel from '@/components/WorkflowPanel'
import ServiceCards from '@/components/ServiceCards'
import TransactionLog from '@/components/TransactionLog'
import { streamChat, SSEEvent } from '@/lib/sse-client'
import { Language } from '@/lib/i18n'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://43.98.164.203:8000'

export interface WorkflowEvent {
  type: string
  data: Record<string, any>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  agent?: string
  tools?: string[]
  timestamp: string
  image?: string
}

export interface Transaction {
  id: string
  type: string
  description: string
  amount: string
  time: string
  icon: string
}

export default function Home() {
  const [sessionId] = useState(() => {
    if (typeof window === 'undefined') return 'demo-session'
    const key = 'myagent-session-id'
    const existing = window.localStorage.getItem(key)
    if (existing) return existing
    const generated = `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
    window.localStorage.setItem(key, generated)
    return generated
  })

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeAgent, setActiveAgent] = useState<string | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [totalCommission, setTotalCommission] = useState(0)
  const [transactionCount, setTransactionCount] = useState(0)
  const [language, setLanguage] = useState<Language>('es')
  const lastToolRef = useRef<Set<string>>(new Set())

  // Load transactions from backend on mount
  useEffect(() => {
    const loadTransactions = async () => {
      try {
        const r = await fetch(`${API_URL}/api/analytics/transactions?limit=20&days=1&session_id=${encodeURIComponent(sessionId)}`)
        if (!r.ok) return
        const json = await r.json()
        const dbTransactions = (json.transactions || []).map((tx: any) => ({
          id: `db-${tx.id}`,
          type: tx.type || 'other',
          description: tx.description || tx.tool_name || '',
          amount: tx.commission > 0 ? `+${tx.commission}€` : '📊',
          time: tx.created_at ? new Date(tx.created_at).toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) : '',
          icon: tx.type === 'recarga' ? '📱' : tx.type === 'pin' ? '🎮' : tx.type === 'energia' ? '⚡' : tx.type === 'paqueteria' ? '📦' : '✅',
        }))
        if (dbTransactions.length > 0) {
          setTransactions(dbTransactions)
          const totalComm = (json.transactions || []).reduce((sum: number, tx: any) => sum + (tx.commission || 0), 0)
          setTotalCommission(totalComm)
          setTransactionCount(json.transactions?.length || 0)
        }
      } catch {}
    }
    loadTransactions()
  }, [sessionId])

  const handleToolResult = useCallback((data: Record<string, any>) => {
    const tool = data.tool || ''
    const result = data.result || {}

    const dedupeKey = `${tool}-${result.estado || ''}-${result.ticket || ''}-${result.pin || ''}-${JSON.stringify(result.detalles || result.contrato || result.producto || '').slice(0, 80)}`
    if (lastToolRef.current.has(dedupeKey)) return
    lastToolRef.current.add(dedupeKey)
    setTimeout(() => lastToolRef.current.delete(dedupeKey), 30000)

    let newTransaction: Transaction | null = null

    if (tool === 'procesar_recarga' && result.estado === 'recarga_exitosa') {
      const comision = parseFloat(result.comision_generada?.replace('€', '') || '0')
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'recarga',
        description: `Recharge ${result.detalles?.pais || ''}`,
        amount: `+${comision}€`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '📱',
      }
      setTotalCommission(prev => prev + comision)
    } else if (tool === 'registrar_paquetes' && result.estado === 'registrados') {
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'paqueteria',
        description: `📥 ${result.transportista || 'Packages'} × ${result.paquetes_registrados || '?'}`,
        amount: `pending`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '📦',
      }
    } else if (tool === 'activar_pin_digital' && result.estado === 'pin_activado') {
      const comision = parseFloat(result.comision_generada?.replace('€', '') || '0')
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'pin',
        description: `${result.plataforma} ${result.producto || ''}`,
        amount: `+${comision}€`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '🎮',
      }
      setTotalCommission(prev => prev + comision)
    } else if (tool === 'preparar_contrato_energia' && result.estado === 'borrador_preparado') {
      const comision = result.contrato?.comision_punto_venta || 25
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'energia',
        description: `Contract ${result.contrato?.tarifa_destino || 'energy'}`,
        amount: `+${comision}€`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '⚡',
      }
      setTotalCommission(prev => prev + comision)
    } else if (tool === 'calcular_ahorro_energetico') {
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'energia',
        description: `Analysis: save ${result.ahorro_mensual || 0}€/mo`,
        amount: `📊`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '⚡',
      }
    } else if (tool === 'confirmar_entrega_paquete' && result.estado === 'entregado') {
      const comision = parseFloat(result.comision_generada?.replace('€', '') || '0.30')
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'paqueteria',
        description: `Delivery ${result.codigo_tracking || ''}`,
        amount: `+${comision}€`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '✅',
      }
      setTotalCommission(prev => prev + comision)
    } else if (tool === 'society_debate') {
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'strategy',
        description: `Strategic consulting (Agent Society)`,
        amount: `🏛️`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '🏛️',
      }
    } else if (tool === 'vision_analysis') {
      newTransaction = {
        id: `txn-${Date.now()}`, type: 'visual',
        description: `Image analysis completed`,
        amount: `👁️`,
        time: new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }),
        icon: '👁️',
      }
    }

    if (newTransaction) {
      setTransactions(prev => [newTransaction!, ...prev].slice(0, 15))
      setTransactionCount(prev => prev + 1)
    }
  }, [])

  const handleSendMessage = useCallback(async (message: string, imageData?: string) => {
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
      image: imageData ? 'attached' : undefined,
    }
    setMessages(prev => [...prev, userMsg])
    setIsProcessing(true)
    setWorkflowEvents([])
    setActiveAgent(null)

    await streamChat({
      message,
      sessionId,
      image: imageData,
      onEvent: (event: SSEEvent) => {
        setWorkflowEvents(prev => [...prev, event])
        if (event.type === 'routing') {
          setActiveAgent(event.data.agent_selected)
        }
        if (event.type === 'tool_result') {
          handleToolResult(event.data)
        }
        // Society debate events
        if (event.type === 'society_proposal' || event.type === 'society_moderator' || event.type === 'society_consensus') {
          // These are already in workflow events for the panel
        }
      },
      onComplete: (data) => {
        const agentMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'agent',
          content: data.message || '',
          agent: data.agent_used,
          tools: data.tools_called,
          timestamp: new Date().toISOString(),
        }
        setMessages(prev => [...prev, agentMsg])
        setIsProcessing(false)
      },
      onError: (error) => {
        const errorMsg: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'agent',
          content: `⚠️ ${error}`,
          timestamp: new Date().toISOString(),
        }
        setMessages(prev => [...prev, errorMsg])
        setIsProcessing(false)
      },
    })
  }, [sessionId, handleToolResult])

  const handleClearChat = useCallback(async () => {
    setMessages([])
    setWorkflowEvents([])
    setActiveAgent(null)
    try {
      await fetch(`${API_URL}/api/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })
    } catch {}
  }, [sessionId])

  return (
    <SmartPOSLayout language={language} onLanguageChange={(l) => setLanguage(l as Language)}>
      <div className="flex h-full gap-4 p-4">
        {/* Left Panel - Services & Transactions */}
        <div className="w-80 flex flex-col gap-4 shrink-0">
          <ServiceCards
            onQuickAction={handleSendMessage}
            totalCommission={totalCommission}
            transactionCount={transactionCount}
            language={language}
          />
          <TransactionLog transactions={transactions} totalCommission={totalCommission} language={language} />
        </div>

        {/* Center - Chat */}
        <div className="flex-1 flex flex-col min-w-0">
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            onClearChat={handleClearChat}
            isProcessing={isProcessing}
            activeAgent={activeAgent}
            language={language}
          />
        </div>

        {/* Right Panel - Workflow Visualization */}
        <div className="w-80 shrink-0">
          <WorkflowPanel
            events={workflowEvents}
            isProcessing={isProcessing}
            activeAgent={activeAgent}
            language={language}
          />
        </div>
      </div>
    </SmartPOSLayout>
  )
}
