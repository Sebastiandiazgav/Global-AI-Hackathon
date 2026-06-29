import { render, screen } from '@testing-library/react'
import SmartPOSLayout from '@/components/SmartPOSLayout'

describe('SmartPOSLayout', () => {
  it('renders the header with MyAgent branding', () => {
    render(<SmartPOSLayout><div>content</div></SmartPOSLayout>)
    expect(screen.getByText('MyAgent')).toBeInTheDocument()
    expect(screen.getByText('Enterprise AI Copilot v2.0')).toBeInTheDocument()
  })

  it('renders children content', () => {
    render(<SmartPOSLayout><div>test child</div></SmartPOSLayout>)
    expect(screen.getByText('test child')).toBeInTheDocument()
  })

  it('shows agent status badges', () => {
    render(<SmartPOSLayout><div>content</div></SmartPOSLayout>)
    expect(screen.getByText('Energy')).toBeInTheDocument()
    expect(screen.getByText('Logistics')).toBeInTheDocument()
    expect(screen.getByText('Support')).toBeInTheDocument()
    expect(screen.getByText('Analytics')).toBeInTheDocument()
    expect(screen.getByText('Society')).toBeInTheDocument()
  })

  it('shows footer with infrastructure info', () => {
    render(<SmartPOSLayout><div>content</div></SmartPOSLayout>)
    expect(screen.getByText(/Qwen Cloud/)).toBeInTheDocument()
    expect(screen.getByText(/hackaton-enterprise/)).toBeInTheDocument()
  })
})
