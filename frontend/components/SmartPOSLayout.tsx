'use client'

import { useEffect, useState } from 'react'
import { Zap, Package, Phone, Shield, Wifi, BarChart3, Globe, Brain } from 'lucide-react'
import { Language, getTranslations } from '@/lib/i18n'

interface SmartPOSLayoutProps {
  children: React.ReactNode
  language?: Language
  onLanguageChange?: (lang: string) => void
}

const LANGUAGES: { code: Language; label: string; name: string }[] = [
  { code: 'es', label: '🇪🇸 ES', name: 'Español' },
  { code: 'en', label: '🇬🇧 EN', name: 'English' },
  { code: 'fr', label: '🇫🇷 FR', name: 'Français' },
  { code: 'pt', label: '🇵🇹 PT', name: 'Português' },
  { code: 'de', label: '🇩🇪 DE', name: 'Deutsch' },
  { code: 'it', label: '🇮🇹 IT', name: 'Italiano' },
  { code: 'zh', label: '🇨🇳 ZH', name: '中文' },
]

export default function SmartPOSLayout({ children, language = 'es', onLanguageChange }: SmartPOSLayoutProps) {
  const t = getTranslations(language)
  const [currentTime, setCurrentTime] = useState('--:--')
  const [showLangMenu, setShowLangMenu] = useState(false)

  useEffect(() => {
    const updateTime = () => setCurrentTime(new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }))
    updateTime()
    const timer = setInterval(updateTime, 30000)
    return () => clearInterval(timer)
  }, [])

  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0]

  return (
    <div className="h-screen flex flex-col bg-disa-dark overflow-hidden">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-disa-primary rounded-lg flex items-center justify-center">
              <Brain size={18} className="text-white" />
            </div>
            <div>
              <h1 className="text-white font-semibold text-lg leading-tight">{t.appName}</h1>
              <p className="text-slate-400 text-xs">{t.appSubtitle}</p>
            </div>
          </div>
          <div className="w-px h-8 bg-slate-700" />
          <div className="flex items-center gap-2">
            <StatusBadge icon={<Zap size={11} />} label={t.energy} color="yellow" />
            <StatusBadge icon={<Package size={11} />} label={t.logistics} color="blue" />
            <StatusBadge icon={<Phone size={11} />} label={t.recharges} color="green" />
            <StatusBadge icon={<BarChart3 size={11} />} label={t.analytics} color="cyan" />
            <StatusBadge icon={<Brain size={11} />} label="Society" color="rose" />
          </div>
        </div>

        <div className="flex items-center gap-4 text-slate-400 text-sm">
          {/* Language selector */}
          <div className="relative">
            <button onClick={() => setShowLangMenu(!showLangMenu)}
              className="flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-slate-800 transition-colors">
              <Globe size={14} /><span className="text-xs">{currentLang.label}</span>
            </button>
            {showLangMenu && (
              <div className="absolute right-0 top-full mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 py-1 min-w-[140px]">
                {LANGUAGES.map(lang => (
                  <button key={lang.code}
                    onClick={() => { onLanguageChange?.(lang.code); setShowLangMenu(false) }}
                    className={`w-full text-left px-3 py-1.5 text-xs hover:bg-slate-700 transition-colors ${language === lang.code ? 'text-disa-secondary' : 'text-slate-300'}`}>
                    {lang.label} {lang.name}
                  </button>
                ))}
              </div>
            )}
          </div>
          <a href="/analytics" className="flex items-center gap-1 hover:text-disa-secondary transition-colors">
            <BarChart3 size={14} /><span className="text-xs">{t.analytics}</span>
          </a>
          <div className="flex items-center gap-1">
            <Shield size={14} className="text-disa-accent" /><span className="text-xs">{t.guardrailsOn}</span>
          </div>
          <Wifi size={14} className="text-disa-accent" />
          <span className="text-white font-mono" suppressHydrationWarning>{currentTime}</span>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">{children}</main>

      <footer className="bg-slate-900 border-t border-slate-700 px-6 py-2 flex items-center justify-between text-xs text-slate-500 shrink-0">
        <span>{t.footerLeft}</span>
        <span>{t.footerRight}</span>
      </footer>
    </div>
  )
}

function StatusBadge({ icon, label, color }: { icon: React.ReactNode; label: string; color: 'yellow' | 'blue' | 'green' | 'cyan' | 'rose' }) {
  const colors: Record<string, string> = {
    yellow: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
    blue: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    green: 'bg-green-500/10 text-green-400 border-green-500/30',
    cyan: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    rose: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
  }
  const dotColors: Record<string, string> = {
    yellow: 'bg-yellow-400', blue: 'bg-blue-400', green: 'bg-green-400', cyan: 'bg-cyan-400', rose: 'bg-rose-400',
  }
  return (
    <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full border ${colors[color]}`}>
      {icon}<span className="text-[10px] font-medium">{label}</span>
      <div className={`w-1.5 h-1.5 rounded-full ${dotColors[color]} animate-pulse`} />
    </div>
  )
}
