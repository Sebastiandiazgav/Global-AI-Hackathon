import '@testing-library/jest-dom/vitest'
import { streamChat } from '@/lib/sse-client'

describe('SSE Client', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('calls onError when fetch fails', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    const onEvent = vi.fn()
    const onComplete = vi.fn()
    const onError = vi.fn()

    await streamChat({
      message: 'test',
      onEvent,
      onComplete,
      onError,
    })

    expect(onError).toHaveBeenCalledWith('No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.')
  })

  it('calls onError when response is not ok', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    })

    const onError = vi.fn()

    await streamChat({
      message: 'test',
      onEvent: vi.fn(),
      onComplete: vi.fn(),
      onError,
    })

    expect(onError).toHaveBeenCalledWith('Error del servidor: 500')
  })

  it('calls onError when no response body', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: null,
    })

    const onError = vi.fn()

    await streamChat({
      message: 'test',
      onEvent: vi.fn(),
      onComplete: vi.fn(),
      onError,
    })

    expect(onError).toHaveBeenCalledWith('El servidor no devolvió datos')
  })

  it('sends correct request to API', async () => {
    const mockReader = {
      read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
    }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => mockReader },
    })

    await streamChat({
      message: 'Hola',
      sessionId: 'test-session',
      onEvent: vi.fn(),
      onComplete: vi.fn(),
      onError: vi.fn(),
    })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/stream/chat'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: 'Hola', session_id: 'test-session' }),
      })
    )
  })
})
