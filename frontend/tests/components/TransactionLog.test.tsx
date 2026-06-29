import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import TransactionLog from '@/components/TransactionLog'

const mockTransactions = [
  {
    id: '1',
    type: 'recarga',
    description: 'Recarga +593 Ecuador',
    amount: '+1.20€',
    time: '10:30',
    icon: '📱',
  },
  {
    id: '2',
    type: 'paqueteria',
    description: 'Amazon Hub #7821',
    amount: '+0.30€',
    time: '10:31',
    icon: '📦',
  },
  {
    id: '3',
    type: 'pin',
    description: 'Netflix Premium',
    amount: '+2.00€',
    time: '10:32',
    icon: '🎮',
  },
]

describe('TransactionLog', () => {
  it('renders transaction list header', () => {
    render(<TransactionLog />)
    expect(screen.getByText('Últimas Transacciones')).toBeInTheDocument()
  })

  it('renders transaction items', () => {
    render(<TransactionLog transactions={mockTransactions} totalCommission={28.5} />)
    expect(screen.getByText('Recarga +593 Ecuador')).toBeInTheDocument()
    expect(screen.getByText('Amazon Hub #7821')).toBeInTheDocument()
    expect(screen.getByText('Netflix Premium')).toBeInTheDocument()
  })

  it('shows commission amounts', () => {
    render(<TransactionLog transactions={mockTransactions} totalCommission={28.5} />)
    expect(screen.getByText('+1.20€')).toBeInTheDocument()
    expect(screen.getByText('+0.30€')).toBeInTheDocument()
    expect(screen.getByText('+2.00€')).toBeInTheDocument()
  })

  it('shows accumulated benefit', () => {
    render(<TransactionLog transactions={mockTransactions} totalCommission={28.5} />)
    expect(screen.getByText('Beneficio acumulado')).toBeInTheDocument()
    expect(screen.getByText('+€28.50')).toBeInTheDocument()
  })
})
