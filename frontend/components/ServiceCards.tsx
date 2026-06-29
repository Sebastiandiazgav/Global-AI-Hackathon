'use client'

import { Zap, Package, Phone, ShoppingBag, TrendingUp, BarChart3, Brain } from 'lucide-react'
import { Language, getTranslations } from '@/lib/i18n'

interface ServiceCardsProps {
  onQuickAction: (message: string) => void
  totalCommission?: number
  transactionCount?: number
  language?: Language
}

export default function ServiceCards({
  onQuickAction,
  totalCommission = 0,
  transactionCount = 0,
  language = 'es',
}: ServiceCardsProps) {
  const t = getTranslations(language)

  const services = [
    { icon: <Zap size={18} />, label: t.energy, color: 'text-yellow-400', bgColor: 'bg-yellow-500/10', borderColor: 'border-yellow-500/20', action: t.suggestBill },
    { icon: <Package size={18} />, label: t.logistics, color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/20', action: t.suggestPackages },
    { icon: <Phone size={18} />, label: t.recharges, color: 'text-green-400', bgColor: 'bg-green-500/10', borderColor: 'border-green-500/20', action: t.suggestRecharge },
    { icon: <ShoppingBag size={18} />, label: t.catalog, color: 'text-purple-400', bgColor: 'bg-purple-500/10', borderColor: 'border-purple-500/20', action: t.suggestEarnings },
    { icon: <BarChart3 size={18} />, label: t.analytics, color: 'text-cyan-400', bgColor: 'bg-cyan-500/10', borderColor: 'border-cyan-500/20', action: t.suggestEarnings },
    { icon: <Brain size={18} />, label: t.strategy, color: 'text-rose-400', bgColor: 'bg-rose-500/10', borderColor: 'border-rose-500/20', action: t.suggestGrow },
  ]

  return (
    <div className="bg-slate-900/50 rounded-xl border border-slate-700 p-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-white">{t.quickActions}</h3>
        <TrendingUp size={14} className="text-disa-accent" />
      </div>

      <div className="grid grid-cols-3 gap-2">
        {services.map((service) => (
          <button
            key={service.label}
            onClick={() => onQuickAction(service.action)}
            className={`service-card flex flex-col items-center gap-1.5 p-2 ${service.borderColor}`}
          >
            <div className={`p-1.5 rounded-lg ${service.bgColor}`}>
              <span className={service.color}>{service.icon}</span>
            </div>
            <span className="text-[10px] text-slate-300">{service.label}</span>
          </button>
        ))}
      </div>

      <div className="mt-3 pt-3 border-t border-slate-700/50 grid grid-cols-2 gap-2">
        <div className="text-center">
          <p className="text-lg font-semibold text-white">€{totalCommission.toFixed(2)}</p>
          <p className="text-[10px] text-slate-500">{t.commissionsToday}</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-semibold text-white">{transactionCount}</p>
          <p className="text-[10px] text-slate-500">{t.transactions}</p>
        </div>
      </div>
    </div>
  )
}
