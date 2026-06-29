'use client'

import { Clock, Activity } from 'lucide-react'
import { Language, getTranslations } from '@/lib/i18n'

interface Transaction {
  id: string
  type: string
  description: string
  amount: string
  time: string
  icon: string
}

interface TransactionLogProps {
  transactions?: Transaction[]
  totalCommission?: number
  language?: Language
}

export default function TransactionLog({
  transactions = [],
  totalCommission = 0,
  language = 'es',
}: TransactionLogProps) {
  const t = getTranslations(language)

  return (
    <div className="flex-1 bg-slate-900/50 rounded-xl border border-slate-700 p-3 overflow-hidden flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-white">{t.lastTransactions}</h3>
        <Clock size={14} className="text-slate-500" />
      </div>

      <div className="flex-1 overflow-y-auto space-y-2">
        {transactions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8">
            <Activity size={20} className="text-slate-600 mb-2" />
            <p className="text-xs text-slate-500">{t.noTransactions}</p>
          </div>
        ) : (
          transactions.map((tx) => (
            <div key={tx.id} className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-slate-800/50 transition-colors">
              <span className="text-lg">{tx.icon}</span>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-300 truncate">{tx.description}</p>
                <p className="text-[10px] text-slate-500">{tx.time}</p>
              </div>
              <span className="text-xs font-medium text-disa-accent">{tx.amount}</span>
            </div>
          ))
        )}
      </div>

      <div className="mt-2 pt-2 border-t border-slate-700/50 flex items-center justify-between">
        <span className="text-[10px] text-slate-500">{t.accumulatedBenefit}</span>
        <span className="text-sm font-semibold text-disa-accent">+€{totalCommission.toFixed(2)}</span>
      </div>
    </div>
  )
}
