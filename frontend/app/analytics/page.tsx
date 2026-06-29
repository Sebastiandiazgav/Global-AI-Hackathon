'use client'

import { useState, useEffect, useRef } from 'react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Download, RefreshCw, Brain, TrendingUp, Shield, Zap } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://43.98.164.203:8000'
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']

interface AnalyticsData {
  total_transactions: number
  total_commission: number
  by_type: Array<{ type: string; count: number; commission: number }>
  agent_usage: Array<{ agent: string; calls: number }>
  guardrail_blocks: number
  daily_trend: Array<{ day: string; commission: number; transactions: number }>
  top_tools: Array<{ tool_name: string; uses: number }>
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [insights, setInsights] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [generatingInsights, setGeneratingInsights] = useState(false)
  const [days, setDays] = useState(7)
  const reportRef = useRef<HTMLDivElement>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const summaryRes = await fetch(`${API_URL}/api/analytics/summary?days=${days}`)
      const summaryJson = await summaryRes.json()
      setData(summaryJson)
    } catch (e) {
      console.error('Failed to fetch analytics:', e)
    }
    setLoading(false)
  }

  const generateInsights = async () => {
    setGeneratingInsights(true)
    try {
      const r = await fetch(`${API_URL}/api/analytics/insights?days=${days}`)
      const json = await r.json()
      setInsights(json.insights || 'No se pudieron generar insights.')
    } catch (e) {
      setInsights('Error al conectar con el servicio de análisis.')
    }
    setGeneratingInsights(false)
  }

  const downloadReport = async () => {
    const { default: jsPDF } = await import('jspdf')
    const { default: html2canvas } = await import('html2canvas')

    if (!reportRef.current) return

    const canvas = await html2canvas(reportRef.current, { backgroundColor: '#1E293B', scale: 2 })
    const imgData = canvas.toDataURL('image/png')

    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width

    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight)
    pdf.save(`MyAgent_Report_${new Date().toISOString().split('T')[0]}.pdf`)
  }

  useEffect(() => { fetchData() }, [days])

  const typeLabels: Record<string, string> = {
    recarga: '📱 Recargas',
    paqueteria_recepcion: '📦 Recepción',
    paqueteria_entrega: '✅ Entregas',
    pin_digital: '🎮 PINs',
    energia_contrato: '⚡ Contratos',
    energia_analisis: '📊 Análisis',
  }

  return (
    <div className="min-h-screen bg-disa-dark text-white p-6">
      <div ref={reportRef} className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">📊 Analytics Dashboard</h1>
            <p className="text-slate-400 text-sm">MyAgent — Business intelligence for your enterprise</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm"
            >
              <option value={1}>Hoy</option>
              <option value={7}>7 días</option>
              <option value={30}>30 días</option>
            </select>
            <button onClick={fetchData} className="p-2 bg-slate-800 rounded-lg hover:bg-slate-700">
              <RefreshCw size={16} />
            </button>
            <button onClick={downloadReport} className="flex items-center gap-2 px-4 py-2 bg-disa-primary rounded-lg hover:bg-disa-secondary text-sm">
              <Download size={14} /> Descargar PDF
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard icon={<TrendingUp size={20} />} label="Comisiones" value={`€${data?.total_commission?.toFixed(2) || '0.00'}`} color="text-disa-accent" />
          <KPICard icon={<Zap size={20} />} label="Transacciones" value={String(data?.total_transactions || 0)} color="text-blue-400" />
          <KPICard icon={<Shield size={20} />} label="Ataques bloqueados" value={String(data?.guardrail_blocks || 0)} color="text-red-400" />
          <KPICard icon={<Brain size={20} />} label="Agentes activos" value="3" color="text-purple-400" />
        </div>

        {loading && (
          <div className="text-xs text-slate-500">Cargando analytics...</div>
        )}

        {/* Charts Row */}
        <div className="grid grid-cols-2 gap-4">
          {/* Commission Trend */}
          <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-medium mb-3">💰 Comisiones por día</h3>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data?.daily_trend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                <Line type="monotone" dataKey="commission" stroke="#10B981" strokeWidth={2} dot={{ fill: '#10B981' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Transactions by Type */}
          <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-medium mb-3">📊 Transacciones por tipo</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={(data?.by_type || []).map(t => ({ ...t, label: typeLabels[t.type] || t.type }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 9 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent Usage + Top Tools */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-medium mb-3">🤖 Uso por agente</h3>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={data?.agent_usage || []} dataKey="calls" nameKey="agent" cx="50%" cy="50%" outerRadius={70} label={({ name, value }: any) => `${name} (${value})`}>
                  {(data?.agent_usage || []).map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4">
            <h3 className="text-sm font-medium mb-3">🔧 Top herramientas</h3>
            <div className="space-y-2">
              {(data?.top_tools || []).map((tool, i) => (
                <div key={tool.tool_name} className="flex items-center justify-between">
                  <span className="text-xs text-slate-300">{tool.tool_name}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${Math.min(100, (tool.uses / Math.max(...(data?.top_tools || []).map(t => t.uses), 1)) * 100)}%`, background: COLORS[i] }} />
                    </div>
                    <span className="text-xs text-slate-500 w-6">{tool.uses}</span>
                  </div>
                </div>
              ))}
              {(!data?.top_tools || data.top_tools.length === 0) && (
                <p className="text-xs text-slate-500">Sin datos aún. Usa el copiloto para generar métricas.</p>
              )}
            </div>
          </div>
        </div>

        {/* AI Insights */}
        <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium flex items-center gap-2">
              <Brain size={16} className="text-purple-400" /> Agente de Inteligencia de Negocio
            </h3>
            <button
              onClick={generateInsights}
              disabled={generatingInsights}
              className="flex items-center gap-2 px-3 py-1.5 bg-purple-600/20 border border-purple-500/30 rounded-lg text-xs text-purple-300 hover:bg-purple-600/30 disabled:opacity-50"
            >
              {generatingInsights ? <RefreshCw size={12} className="animate-spin" /> : <Brain size={12} />}
              {generatingInsights ? 'Analizando...' : 'Generar Insights'}
            </button>
          </div>
          {insights ? (
            <div className="text-sm text-slate-300 leading-relaxed prose prose-invert prose-sm max-w-none
                          prose-p:my-1 prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5
                          prose-headings:text-slate-100 prose-headings:text-sm prose-headings:font-semibold prose-headings:mt-3 prose-headings:mb-1
                          prose-strong:text-white">
              <ReactMarkdown>{insights}</ReactMarkdown>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Haz click en "Generar Insights" para que el agente de negocio analice tus datos y detecte oportunidades.</p>
          )}
        </div>

        {/* Back to copilot */}
        <div className="text-center">
          <a href="/" className="text-sm text-disa-secondary hover:underline">← Volver al Copiloto</a>
        </div>
      </div>
    </div>
  )
}

function KPICard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={color}>{icon}</span>
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  )
}
