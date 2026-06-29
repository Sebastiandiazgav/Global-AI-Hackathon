import { render, screen, fireEvent } from '@testing-library/react'
import ChatPanel from '@/components/ChatPanel'

const defaultProps = {
  messages: [],
  onSendMessage: jest.fn(),
  onClearChat: jest.fn(),
  isProcessing: false,
  activeAgent: null,
}

describe('ChatPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders empty state with welcome message', () => {
    render(<ChatPanel {...defaultProps} />)
    expect(screen.getByText(/MyAgent, your AI Copilot/)).toBeInTheDocument()
  })

  it('renders quick action suggestions', () => {
    render(<ChatPanel {...defaultProps} />)
    expect(screen.getByText(/Analyze bill/)).toBeInTheDocument()
    expect(screen.getByText(/Amazon arrived/)).toBeInTheDocument()
    expect(screen.getByText(/grow my sales/)).toBeInTheDocument()
  })

  it('shows image upload button', () => {
    render(<ChatPanel {...defaultProps} />)
    const imageBtn = screen.getByTitle('Upload image for analysis')
    expect(imageBtn).toBeInTheDocument()
  })

  it('disables send when input is empty', () => {
    render(<ChatPanel {...defaultProps} />)
    const sendBtn = screen.getByRole('button', { name: '' }) // Send button has no text
    // The button with Send icon should be disabled
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons.find(btn => btn.getAttribute('type') === 'submit')
    expect(sendButton).toBeDisabled()
  })

  it('shows processing state', () => {
    render(<ChatPanel {...defaultProps} isProcessing={true} />)
    expect(screen.getByText('Processing...')).toBeInTheDocument()
  })

  it('shows active agent badge', () => {
    render(<ChatPanel {...defaultProps} activeAgent="society" />)
    expect(screen.getByText('🏛️ Agent Society')).toBeInTheDocument()
  })

  it('renders messages', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Hello', timestamp: new Date().toISOString() },
      { id: '2', role: 'agent' as const, content: 'Hi there!', agent: 'soporte', timestamp: new Date().toISOString(), tools: ['buscar_en_manuales'] },
    ]
    render(<ChatPanel {...defaultProps} messages={messages} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
    expect(screen.getByText('💬 Support Agent')).toBeInTheDocument()
  })
})
