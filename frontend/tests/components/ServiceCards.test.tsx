import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import ServiceCards from '@/components/ServiceCards'

describe('ServiceCards', () => {
  it('renders all 4 service cards', () => {
    render(<ServiceCards onQuickAction={vi.fn()} />)
    expect(screen.getByText('Energía')).toBeInTheDocument()
    expect(screen.getByText('Paquetería')).toBeInTheDocument()
    expect(screen.getByText('Recargas')).toBeInTheDocument()
    expect(screen.getByText('Catálogo')).toBeInTheDocument()
  })

  it('renders quick stats', () => {
    render(<ServiceCards onQuickAction={vi.fn()} />)
    expect(screen.getByText('Comisiones hoy')).toBeInTheDocument()
    expect(screen.getByText('Transacciones')).toBeInTheDocument()
  })

  it('calls onQuickAction when a card is clicked', () => {
    const onAction = vi.fn()
    render(<ServiceCards onQuickAction={onAction} />)

    const energiaCard = screen.getByText('Energía').closest('button')!
    fireEvent.click(energiaCard)

    expect(onAction).toHaveBeenCalledWith('¿Qué tarifas de energía hay disponibles?')
  })

  it('renders services header', () => {
    render(<ServiceCards onQuickAction={vi.fn()} />)
    expect(screen.getByText('Servicios')).toBeInTheDocument()
  })
})
