import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import WorkflowPanel from '@/components/WorkflowPanel'

const mockEvents = [
  { type: 'guardrails', data: { action: 'passed', stage: 'input' } },
  { type: 'thinking', data: { message: 'Analizando...', step: 'start' } },
  { type: 'routing', data: { agent_selected: 'energia', intent: 'Análisis de factura', confidence: 0.95 } },
  { type: 'agent_selected', data: { agent: 'energia', status: 'processing' } },
  { type: 'tool_call', data: { tool: 'calcular_ahorro_energetico', args: { consumo_kwh: 350 } } },
  { type: 'tool_result', data: { tool: 'calcular_ahorro_energetico', result: {} } },
  { type: 'response', data: { agent: 'energia', status: 'completed' } },
]

describe('WorkflowPanel', () => {
  it('renders empty state with business service info', () => {
    render(<WorkflowPanel events={[]} isProcessing={false} activeAgent={null} />)
    expect(screen.getByText('Workflow')).toBeInTheDocument()
    expect(screen.getByText(/Servicios disponibles/)).toBeInTheDocument()
  })

  it('shows processing indicator when active', () => {
    render(<WorkflowPanel events={[]} isProcessing={true} activeAgent={null} />)
    expect(screen.getByText('Ejecutando')).toBeInTheDocument()
  })

  it('renders workflow events', () => {
    render(<WorkflowPanel events={mockEvents} isProcessing={false} activeAgent="energia" />)
    // Should show tool name in workflow (appears in both tool_call and tool_result)
    const toolElements = screen.getAllByText(/calcular_ahorro/)
    expect(toolElements.length).toBeGreaterThanOrEqual(1)
  })

  it('shows event count', () => {
    render(<WorkflowPanel events={mockEvents} isProcessing={false} activeAgent="energia" />)
    // Should show step numbers (last event)
    expect(screen.getByText(/7\/7/)).toBeInTheDocument()
  })

  it('displays active agent in footer', () => {
    render(<WorkflowPanel events={mockEvents} isProcessing={false} activeAgent="energia" />)
    expect(screen.getByText('Energia')).toBeInTheDocument()
  })
})
