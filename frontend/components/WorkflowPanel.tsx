'use client'

import { Brain, Route, Wrench, CheckCircle2, Loader2, AlertCircle, Zap, Package, MessageSquare, Eye, BarChart3, Users } from 'lucide-react'
import type { WorkflowEvent } from '@/app/page'
import { Language, getTranslations } from '@/lib/i18n'

interface WorkflowPanelProps {
  events: WorkflowEvent[]
  isProcessing: boolean
  activeAgent: string | null
  language?: Language
}

export default function WorkflowPanel({ events, isProcessing, activeAgent, language = 'es' }: WorkflowPanelProps) {
  const t = getTranslations(language)
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'thinking': return <Brain size={14} className="text-purple-400" />
      case 'routing': return <Route size={14} className="text-blue-400" />
      case 'agent_selected': return <Zap size={14} className="text-yellow-400" />
      case 'tool_call': return <Wrench size={14} className="text-orange-400" />
      case 'tool_result': return <CheckCircle2 size={14} className="text-green-400" />
      case 'response': return <MessageSquare size={14} className="text-disa-accent" />
      case 'error': return <AlertCircle size={14} className="text-red-400" />
      case 'society_start': return <Users size={14} className="text-rose-400" />
      case 'society_turn': return <Brain size={14} className="text-rose-300" />
      case 'society_proposal': return <MessageSquare size={14} className="text-rose-400" />
      case 'society_moderator': return <Users size={14} className="text-amber-400" />
      case 'society_consensus': return <CheckCircle2 size={14} className="text-rose-400" />
      case 'guardrails': return <AlertCircle size={14} className="text-amber-400" />
      default: return <Brain size={14} className="text-slate-400" />
    }
  }

  const getEventLabel = (event: WorkflowEvent) => {
    switch (event.type) {
      case 'thinking':
        return event.data.message || 'Analyzing...'
      case 'routing':
        return `Router → ${event.data.agent_selected} (${Math.round((event.data.confidence || 0) * 100)}%) [${event.data.language || '?'}]`
      case 'agent_selected':
        return `Agent ${event.data.agent} activated`
      case 'tool_call':
        return `Executing: ${event.data.tool}()`
      case 'tool_result':
        return `✓ ${event.data.tool} completed [${event.data.transport || ''}]`
      case 'response':
        return `Response by ${event.data.agent || 'agent'}`
      case 'error':
        return `Error: ${event.data.error || 'unknown'}`
      case 'guardrails':
        return `🛡️ Guardrails: ${event.data.action} (${event.data.stage})`
      // Society events
      case 'society_start':
        return `🏛️ Agent Society convened (${event.data.participants?.length || 0} agents)`
      case 'society_turn':
        return `${event.data.emoji || '🤔'} ${event.data.agent}: ${event.data.status}`
      case 'society_proposal':
        return `${event.data.emoji || '💬'} ${event.data.agent} (R${event.data.round})`
      case 'society_moderator':
        return `🎯 Moderator analysis (R${event.data.round})`
      case 'society_consensus':
        return `✅ Consensus reached!`
      default:
        return event.type
    }
  }

  const getEventBgColor = (type: string) => {
    switch (type) {
      case 'routing': return 'bg-blue-500/5 border-blue-500/20'
      case 'agent_selected': return 'bg-yellow-500/5 border-yellow-500/20'
      case 'tool_call': return 'bg-orange-500/5 border-orange-500/20'
      case 'tool_result': return 'bg-green-500/5 border-green-500/20'
      case 'response': return 'bg-emerald-500/5 border-emerald-500/20'
      case 'error': return 'bg-red-500/5 border-red-500/20'
      case 'guardrails': return 'bg-amber-500/5 border-amber-500/20'
      case 'society_start': return 'bg-rose-500/5 border-rose-500/20'
      case 'society_turn': return 'bg-rose-500/5 border-rose-500/10'
      case 'society_proposal': return 'bg-rose-500/5 border-rose-500/20'
      case 'society_moderator': return 'bg-amber-500/5 border-amber-500/20'
      case 'society_consensus': return 'bg-rose-500/10 border-rose-500/30'
      default: return 'bg-slate-800/50 border-slate-700'
    }
  }

  const isSocietyEvent = (type: string) => type.startsWith('society_')

  return (
    <div className="h-full flex flex-col bg-slate-900/50 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain size={16} className="text-purple-400" />
          <span className="font-medium text-white text-sm">{t.workflow}</span>
        </div>
        {isProcessing && (
          <div className="flex items-center gap-1.5">
            <Loader2 size={12} className="animate-spin text-disa-secondary" />
            <span className="text-xs text-disa-secondary">{t.running}</span>
          </div>
        )}
      </div>

      {/* Workflow Steps */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {events.length === 0 && !isProcessing && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <Route size={24} className="text-slate-600 mb-2" />
            <p className="text-slate-500 text-xs">
              {t.workflow}
            </p>
            <div className="mt-4 text-left w-full space-y-1.5">
              <p className="text-[10px] text-slate-600 uppercase font-medium">{t.availableAgents}</p>
              <div className="text-[11px] text-slate-500 space-y-1">
                <p>⚡ Energy — Tariffs, savings, contracts</p>
                <p>📦 Logistics — Packages, deliveries</p>
                <p>💬 Support — Recharges, PINs, catalog</p>
                <p>👁️ Visual — Image analysis</p>
                <p>📊 Analytics — Performance metrics</p>
                <p>🏛️ Society — Strategic debate</p>
              </div>
            </div>
          </div>
        )}

        {isProcessing && events.length === 0 && (
          <div className="workflow-step bg-purple-500/5 border border-purple-500/20">
            <Loader2 size={14} className="animate-spin text-purple-400" />
            <span className="text-slate-300 text-xs">Analyzing message...</span>
          </div>
        )}

        {events.map((event, index) => (
          <div key={index} className={`workflow-step border ${getEventBgColor(event.type)}`}>
            {getEventIcon(event.type)}
            <div className="flex-1 min-w-0">
              <span className="text-slate-300 text-xs block truncate">
                {getEventLabel(event)}
              </span>
              {event.type === 'tool_call' && event.data.args && (
                <span className="text-[10px] text-slate-500 block truncate mt-0.5">
                  {JSON.stringify(event.data.args).slice(0, 60)}
                </span>
              )}
              {event.type === 'society_proposal' && event.data.proposal && (
                <span className="text-[10px] text-slate-400 block mt-0.5 line-clamp-2">
                  {event.data.proposal.slice(0, 120)}...
                </span>
              )}
            </div>
            <span className="text-[10px] text-slate-600 shrink-0">
              {isSocietyEvent(event.type) ? `R${event.data.round || ''}` : `${index + 1}`}
            </span>
          </div>
        ))}
      </div>

      {/* Footer */}
      {activeAgent && (
        <div className="px-3 py-2 border-t border-slate-700 bg-slate-800/30">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-500">{t.activeAgent}:</span>
            <span className={`text-[10px] font-medium ${
              activeAgent === 'energia' ? 'text-yellow-400' :
              activeAgent === 'logistica' ? 'text-blue-400' :
              activeAgent === 'soporte' ? 'text-green-400' :
              activeAgent === 'visual' ? 'text-purple-400' :
              activeAgent === 'analytics' ? 'text-cyan-400' :
              activeAgent === 'society' ? 'text-rose-400' : 'text-slate-400'
            }`}>
              {activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)}
            </span>
          </div>
          <div className="text-[10px] text-slate-600 mt-0.5">
            {events.length} {t.steps} • {events.filter(e => e.type === 'tool_result').length} {t.toolsExecuted}
          </div>
        </div>
      )}
    </div>
  )
}
