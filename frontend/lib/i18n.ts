/**
 * MyAgent - Internationalization (i18n)
 * Translations for all supported languages.
 */

export type Language = 'es' | 'en' | 'fr' | 'pt' | 'de' | 'it' | 'zh'

export interface Translations {
  // Header
  appName: string
  appSubtitle: string
  guardrailsOn: string

  // Quick Actions
  quickActions: string
  energy: string
  logistics: string
  recharges: string
  catalog: string
  analytics: string
  strategy: string
  commissionsToday: string
  transactions: string

  // Chat
  copilotTitle: string
  welcomeTitle: string
  welcomeSubtitle: string
  placeholder: string
  listening: string
  processing: string
  uploadImage: string
  imageAttached: string
  newConversation: string

  // Quick suggestions
  suggestBill: string
  suggestPackages: string
  suggestRecharge: string
  suggestEarnings: string
  suggestGrow: string

  // Workflow
  workflow: string
  running: string
  availableAgents: string
  activeAgent: string
  steps: string
  toolsExecuted: string

  // Transaction Log
  lastTransactions: string
  accumulatedBenefit: string
  noTransactions: string

  // Agents
  agentEnergy: string
  agentLogistics: string
  agentSupport: string
  agentVisual: string
  agentAnalytics: string
  agentSociety: string

  // Footer
  footerLeft: string
  footerRight: string
}

const translations: Record<Language, Translations> = {
  es: {
    appName: 'MyAgent',
    appSubtitle: 'Enterprise AI Copilot v2.0',
    guardrailsOn: 'Guardrails ON',
    quickActions: 'Acciones Rápidas',
    energy: 'Energía',
    logistics: 'Logística',
    recharges: 'Recargas',
    catalog: 'Catálogo',
    analytics: 'Analítica',
    strategy: 'Estrategia',
    commissionsToday: 'Comisiones hoy',
    transactions: 'Transacciones',
    copilotTitle: 'MyAgent Copilot',
    welcomeTitle: '¡Hola! Soy MyAgent, tu Copiloto IA',
    welcomeSubtitle: 'Puedo ayudarte con energía, logística, recargas, analítica y consultoría estratégica. Escribe, habla o sube una imagen para empezar.',
    placeholder: 'Escribe tu mensaje...',
    listening: '🎤 Escuchando...',
    processing: 'Procesando...',
    uploadImage: 'Subir imagen para análisis',
    imageAttached: 'Imagen adjunta',
    newConversation: 'Nueva conversación',
    suggestBill: 'Analizar factura: 350 kWh tarifa plana',
    suggestPackages: 'Llegó Amazon con 5 paquetes',
    suggestRecharge: 'Recarga 15€ a Ecuador',
    suggestEarnings: '¿Cuánto gané hoy?',
    suggestGrow: '¿Cómo puedo aumentar mis ventas?',
    workflow: 'Flujo de Trabajo',
    running: 'Ejecutando',
    availableAgents: 'Agentes disponibles:',
    activeAgent: 'Agente activo:',
    steps: 'pasos',
    toolsExecuted: 'tools ejecutadas',
    lastTransactions: 'Últimas Transacciones',
    accumulatedBenefit: 'Beneficio acumulado',
    noTransactions: 'Las transacciones aparecerán aquí cuando uses los servicios.',
    agentEnergy: '⚡ Agente Energía',
    agentLogistics: '📦 Agente Logística',
    agentSupport: '💬 Agente Soporte',
    agentVisual: '👁️ Agente Visual',
    agentAnalytics: '📊 Agente Analítica',
    agentSociety: '🏛️ Agent Society',
    footerLeft: 'Terminal: SMART-POS-001 | Demo Enterprise | 7 Agentes • 20 MCP Tools • 5 Servidores',
    footerRight: 'Powered by Qwen Cloud + Alibaba Cloud | hackaton-enterprise © 2026',
  },
  en: {
    appName: 'MyAgent',
    appSubtitle: 'Enterprise AI Copilot v2.0',
    guardrailsOn: 'Guardrails ON',
    quickActions: 'Quick Actions',
    energy: 'Energy',
    logistics: 'Logistics',
    recharges: 'Recharges',
    catalog: 'Catalog',
    analytics: 'Analytics',
    strategy: 'Strategy',
    commissionsToday: 'Commissions today',
    transactions: 'Transactions',
    copilotTitle: 'MyAgent Copilot',
    welcomeTitle: 'Hi! I\'m MyAgent, your AI Copilot',
    welcomeSubtitle: 'I can help with energy, logistics, recharges, analytics, and strategic consulting. Type, speak, or upload an image to start.',
    placeholder: 'Type your message...',
    listening: '🎤 Listening...',
    processing: 'Processing...',
    uploadImage: 'Upload image for analysis',
    imageAttached: 'Image attached',
    newConversation: 'New conversation',
    suggestBill: 'Analyze bill: 350 kWh flat rate',
    suggestPackages: 'Amazon arrived with 5 packages',
    suggestRecharge: 'Recharge 15€ to Ecuador',
    suggestEarnings: 'How much did I earn today?',
    suggestGrow: 'How can I grow my sales?',
    workflow: 'Workflow',
    running: 'Running',
    availableAgents: 'Available Agents:',
    activeAgent: 'Active agent:',
    steps: 'steps',
    toolsExecuted: 'tools executed',
    lastTransactions: 'Last Transactions',
    accumulatedBenefit: 'Accumulated benefit',
    noTransactions: 'Transactions will appear here when you use the services.',
    agentEnergy: '⚡ Energy Agent',
    agentLogistics: '📦 Logistics Agent',
    agentSupport: '💬 Support Agent',
    agentVisual: '👁️ Visual Agent',
    agentAnalytics: '📊 Analytics Agent',
    agentSociety: '🏛️ Agent Society',
    footerLeft: 'Terminal: SMART-POS-001 | Enterprise Demo | 7 Agents • 20 MCP Tools • 5 Servers',
    footerRight: 'Powered by Qwen Cloud + Alibaba Cloud | hackaton-enterprise © 2026',
  },
  fr: {
    appName: 'MyAgent',
    appSubtitle: 'Copilote IA Entreprise v2.0',
    guardrailsOn: 'Guardrails ON',
    quickActions: 'Actions Rapides',
    energy: 'Énergie',
    logistics: 'Logistique',
    recharges: 'Recharges',
    catalog: 'Catalogue',
    analytics: 'Analytique',
    strategy: 'Stratégie',
    commissionsToday: 'Commissions aujourd\'hui',
    transactions: 'Transactions',
    copilotTitle: 'MyAgent Copilote',
    welcomeTitle: 'Bonjour! Je suis MyAgent, votre Copilote IA',
    welcomeSubtitle: 'Je peux vous aider avec l\'énergie, la logistique, les recharges, l\'analytique et le conseil stratégique.',
    placeholder: 'Écrivez votre message...',
    listening: '🎤 Écoute...',
    processing: 'Traitement...',
    uploadImage: 'Télécharger image pour analyse',
    imageAttached: 'Image jointe',
    newConversation: 'Nouvelle conversation',
    suggestBill: 'Analyser facture: 350 kWh tarif fixe',
    suggestPackages: 'Amazon est arrivé avec 5 colis',
    suggestRecharge: 'Recharge 15€ vers Équateur',
    suggestEarnings: 'Combien ai-je gagné aujourd\'hui?',
    suggestGrow: 'Comment augmenter mes ventes?',
    workflow: 'Flux de Travail',
    running: 'En cours',
    availableAgents: 'Agents disponibles:',
    activeAgent: 'Agent actif:',
    steps: 'étapes',
    toolsExecuted: 'outils exécutés',
    lastTransactions: 'Dernières Transactions',
    accumulatedBenefit: 'Bénéfice accumulé',
    noTransactions: 'Les transactions apparaîtront ici lorsque vous utiliserez les services.',
    agentEnergy: '⚡ Agent Énergie',
    agentLogistics: '📦 Agent Logistique',
    agentSupport: '💬 Agent Support',
    agentVisual: '👁️ Agent Visuel',
    agentAnalytics: '📊 Agent Analytique',
    agentSociety: '🏛️ Société d\'Agents',
    footerLeft: 'Terminal: SMART-POS-001 | Démo Enterprise | 7 Agents • 20 Outils MCP • 5 Serveurs',
    footerRight: 'Propulsé par Qwen Cloud + Alibaba Cloud | hackaton-enterprise © 2026',
  },
  pt: {
    appName: 'MyAgent',
    appSubtitle: 'Copiloto IA Empresarial v2.0',
    guardrailsOn: 'Guardrails ON',
    quickActions: 'Ações Rápidas',
    energy: 'Energia',
    logistics: 'Logística',
    recharges: 'Recargas',
    catalog: 'Catálogo',
    analytics: 'Analítica',
    strategy: 'Estratégia',
    commissionsToday: 'Comissões hoje',
    transactions: 'Transações',
    copilotTitle: 'MyAgent Copiloto',
    welcomeTitle: 'Olá! Sou o MyAgent, seu Copiloto IA',
    welcomeSubtitle: 'Posso ajudar com energia, logística, recargas, analítica e consultoria estratégica.',
    placeholder: 'Digite sua mensagem...',
    listening: '🎤 Ouvindo...',
    processing: 'Processando...',
    uploadImage: 'Enviar imagem para análise',
    imageAttached: 'Imagem anexada',
    newConversation: 'Nova conversa',
    suggestBill: 'Analisar fatura: 350 kWh tarifa fixa',
    suggestPackages: 'Amazon chegou com 5 pacotes',
    suggestRecharge: 'Recarga 15€ para Equador',
    suggestEarnings: 'Quanto ganhei hoje?',
    suggestGrow: 'Como posso aumentar minhas vendas?',
    workflow: 'Fluxo de Trabalho',
    running: 'Executando',
    availableAgents: 'Agentes disponíveis:',
    activeAgent: 'Agente ativo:',
    steps: 'passos',
    toolsExecuted: 'ferramentas executadas',
    lastTransactions: 'Últimas Transações',
    accumulatedBenefit: 'Benefício acumulado',
    noTransactions: 'As transações aparecerão aqui quando usar os serviços.',
    agentEnergy: '⚡ Agente Energia',
    agentLogistics: '📦 Agente Logística',
    agentSupport: '💬 Agente Suporte',
    agentVisual: '👁️ Agente Visual',
    agentAnalytics: '📊 Agente Analítica',
    agentSociety: '🏛️ Sociedade de Agentes',
    footerLeft: 'Terminal: SMART-POS-001 | Demo Empresarial | 7 Agentes • 20 Ferramentas MCP • 5 Servidores',
    footerRight: 'Powered by Qwen Cloud + Alibaba Cloud | hackaton-enterprise © 2026',
  },
  de: {
    appName: 'MyAgent',
    appSubtitle: 'Enterprise KI-Copilot v2.0',
    guardrailsOn: 'Guardrails AN',
    quickActions: 'Schnellaktionen',
    energy: 'Energie',
    logistics: 'Logistik',
    recharges: 'Aufladungen',
    catalog: 'Katalog',
    analytics: 'Analytik',
    strategy: 'Strategie',
    commissionsToday: 'Provisionen heute',
    transactions: 'Transaktionen',
    copilotTitle: 'MyAgent Copilot',
    welcomeTitle: 'Hallo! Ich bin MyAgent, Ihr KI-Copilot',
    welcomeSubtitle: 'Ich kann bei Energie, Logistik, Aufladungen, Analytik und strategischer Beratung helfen.',
    placeholder: 'Nachricht eingeben...',
    listening: '🎤 Hört zu...',
    processing: 'Verarbeitung...',
    uploadImage: 'Bild für Analyse hochladen',
    imageAttached: 'Bild angehängt',
    newConversation: 'Neues Gespräch',
    suggestBill: 'Rechnung analysieren: 350 kWh Festtarif',
    suggestPackages: 'Amazon mit 5 Paketen angekommen',
    suggestRecharge: 'Aufladung 15€ nach Ecuador',
    suggestEarnings: 'Wie viel habe ich heute verdient?',
    suggestGrow: 'Wie kann ich meinen Umsatz steigern?',
    workflow: 'Arbeitsablauf',
    running: 'Läuft',
    availableAgents: 'Verfügbare Agenten:',
    activeAgent: 'Aktiver Agent:',
    steps: 'Schritte',
    toolsExecuted: 'Tools ausgeführt',
    lastTransactions: 'Letzte Transaktionen',
    accumulatedBenefit: 'Kumulierter Gewinn',
    noTransactions: 'Transaktionen erscheinen hier, wenn Sie die Dienste nutzen.',
    agentEnergy: '⚡ Energie-Agent',
    agentLogistics: '📦 Logistik-Agent',
    agentSupport: '💬 Support-Agent',
    agentVisual: '👁️ Visueller Agent',
    agentAnalytics: '📊 Analytik-Agent',
    agentSociety: '🏛️ Agenten-Gesellschaft',
    footerLeft: 'Terminal: SMART-POS-001 | Enterprise Demo | 7 Agenten • 20 MCP-Tools • 5 Server',
    footerRight: 'Betrieben von Qwen Cloud + Alibaba Cloud | hackaton-enterprise © 2026',
  },
  it: {
    appName: 'MyAgent',
    appSubtitle: 'Copilota IA Aziendale v2.0',
    guardrailsOn: 'Guardrails ON',
    quickActions: 'Azioni Rapide',
    energy: 'Energia',
    logistics: 'Logistica',
    recharges: 'Ricariche',
    catalog: 'Catalogo',
    analytics: 'Analitica',
    strategy: 'Strategia',
    commissionsToday: 'Commissioni oggi',
    transactions: 'Transazioni',
    copilotTitle: 'MyAgent Copilota',
    welcomeTitle: 'Ciao! Sono MyAgent, il tuo Copilota IA',
    welcomeSubtitle: 'Posso aiutarti con energia, logistica, ricariche, analitica e consulenza strategica.',
    placeholder: 'Scrivi il tuo messaggio...',
    listening: '🎤 Ascolto...',
    processing: 'Elaborazione...',
    uploadImage: 'Carica immagine per analisi',
    imageAttached: 'Immagine allegata',
    newConversation: 'Nuova conversazione',
    suggestBill: 'Analizza bolletta: 350 kWh tariffa fissa',
    suggestPackages: 'Amazon arrivato con 5 pacchi',
    suggestRecharge: 'Ricarica 15€ per Ecuador',
    suggestEarnings: 'Quanto ho guadagnato oggi?',
    suggestGrow: 'Come posso aumentare le vendite?',
    workflow: 'Flusso di Lavoro',
    running: 'In esecuzione',
    availableAgents: 'Agenti disponibili:',
    activeAgent: 'Agente attivo:',
    steps: 'passi',
    toolsExecuted: 'strumenti eseguiti',
    lastTransactions: 'Ultime Transazioni',
    accumulatedBenefit: 'Beneficio accumulato',
    noTransactions: 'Le transazioni appariranno qui quando utilizzi i servizi.',
    agentEnergy: '⚡ Agente Energia',
    agentLogistics: '📦 Agente Logistica',
    agentSupport: '💬 Agente Supporto',
    agentVisual: '👁️ Agente Visivo',
    agentAnalytics: '📊 Agente Analitica',
    agentSociety: '🏛️ Società di Agenti',
    footerLeft: 'Terminal: SMART-POS-001 | Demo Aziendale | 7 Agenti • 20 Strumenti MCP • 5 Server',
    footerRight: 'Alimentato da Qwen Cloud + Alibaba Cloud | hackaton-enterprise © 2026',
  },
  zh: {
    appName: 'MyAgent',
    appSubtitle: '企业AI副驾驶 v2.0',
    guardrailsOn: '安全护栏 开启',
    quickActions: '快速操作',
    energy: '能源',
    logistics: '物流',
    recharges: '充值',
    catalog: '目录',
    analytics: '分析',
    strategy: '策略',
    commissionsToday: '今日佣金',
    transactions: '交易',
    copilotTitle: 'MyAgent 副驾驶',
    welcomeTitle: '你好！我是MyAgent，你的AI副驾驶',
    welcomeSubtitle: '我可以帮助处理能源、物流、充值、分析和战略咨询。输入、说话或上传图片开始。',
    placeholder: '输入你的消息...',
    listening: '🎤 听取中...',
    processing: '处理中...',
    uploadImage: '上传图片进行分析',
    imageAttached: '图片已附加',
    newConversation: '新对话',
    suggestBill: '分析账单：350千瓦时固定费率',
    suggestPackages: '亚马逊到货5个包裹',
    suggestRecharge: '充值15€到厄瓜多尔',
    suggestEarnings: '我今天赚了多少？',
    suggestGrow: '如何增加销售额？',
    workflow: '工作流程',
    running: '运行中',
    availableAgents: '可用代理：',
    activeAgent: '活跃代理：',
    steps: '步骤',
    toolsExecuted: '工具已执行',
    lastTransactions: '最近交易',
    accumulatedBenefit: '累计收益',
    noTransactions: '使用服务时交易将显示在这里。',
    agentEnergy: '⚡ 能源代理',
    agentLogistics: '📦 物流代理',
    agentSupport: '💬 支持代理',
    agentVisual: '👁️ 视觉代理',
    agentAnalytics: '📊 分析代理',
    agentSociety: '🏛️ 代理社会',
    footerLeft: '终端: SMART-POS-001 | 企业演示 | 7代理 • 20 MCP工具 • 5服务器',
    footerRight: '由 Qwen Cloud + 阿里巴巴云驱动 | hackaton-enterprise © 2026',
  },
}

export function getTranslations(lang: Language): Translations {
  return translations[lang] || translations.en
}

export function getAgentLabel(agent: string | undefined, lang: Language): string {
  const t = getTranslations(lang)
  switch (agent) {
    case 'energia': return t.agentEnergy
    case 'logistica': return t.agentLogistics
    case 'soporte': return t.agentSupport
    case 'visual': return t.agentVisual
    case 'analytics': return t.agentAnalytics
    case 'society': return t.agentSociety
    default: return '🤖 MyAgent'
  }
}
