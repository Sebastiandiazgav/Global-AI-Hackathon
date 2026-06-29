/**
 * MyAgent SSE Client - Browser-compatible Server-Sent Events parser
 *
 * Uses fetch + ReadableStream with line-by-line parsing that correctly
 * handles the SSE protocol in browser environments.
 * Supports image upload for visual analysis.
 */

export interface SSEEvent {
  type: string
  data: Record<string, any>
}

export interface StreamChatOptions {
  message: string
  sessionId?: string
  image?: string
  onEvent: (event: SSEEvent) => void
  onComplete: (data: Record<string, any>) => void
  onError: (error: string) => void
  timeout?: number
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://43.98.164.203:8000'

function formatStreamError(error: unknown): string {
  if (!(error instanceof Error)) {
    return 'Could not connect to service. Try again in a few seconds.'
  }
  const raw = (error.message || '').toLowerCase()
  if (raw.includes('failed to fetch') || raw.includes('network') || raw.includes('load failed')) {
    return 'Could not connect to service. Try again in a few seconds.'
  }
  return error.message || 'Could not connect to service. Try again in a few seconds.'
}

export async function streamChat({
  message,
  sessionId = 'default',
  image,
  onEvent,
  onComplete,
  onError,
  timeout = 120000,
}: StreamChatOptions): Promise<void> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => {
    controller.abort()
    onError('Timeout: server did not respond in 120 seconds.')
  }, timeout)

  try {
    const body: Record<string, any> = { message, session_id: sessionId }
    if (image) {
      body.image = image
    }

    const response = await fetch(`${API_URL}/api/stream/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      clearTimeout(timeoutId)
      onError(`Server error: ${response.status}`)
      return
    }

    if (!response.body) {
      clearTimeout(timeoutId)
      onError('Server returned no data')
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    let buffer = ''
    let currentEvent = ''
    let currentData = ''
    let completed = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      let newlineIndex: number
      while ((newlineIndex = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newlineIndex)
        buffer = buffer.slice(newlineIndex + 1)

        if (line === '' || line === '\r') {
          if (currentEvent && currentData) {
            const parsed = tryParseEvent(currentEvent, currentData)
            if (parsed) {
              onEvent(parsed)
              if (parsed.type === 'complete') {
                completed = true
                onComplete(parsed.data)
              } else if (parsed.type === 'error') {
                completed = true
                onError(parsed.data.error || 'Agent error')
              }
            }
          }
          currentEvent = ''
          currentData = ''
        } else if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          const chunk = line.slice(5)
          currentData = currentData ? currentData + '\n' + chunk : chunk
        }
      }
    }

    // Process remaining event
    if (currentEvent && currentData) {
      const parsed = tryParseEvent(currentEvent, currentData)
      if (parsed) {
        onEvent(parsed)
        if (parsed.type === 'complete' && !completed) {
          completed = true
          onComplete(parsed.data)
        }
      }
    }

    if (!completed) {
      onError('Connection closed without completing. Try again.')
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') return
    onError(formatStreamError(error))
  } finally {
    clearTimeout(timeoutId)
  }
}

function tryParseEvent(eventType: string, dataStr: string): SSEEvent | null {
  const trimmed = dataStr.trim()
  if (!trimmed) return null
  try {
    const data = JSON.parse(trimmed)
    return { type: eventType, data }
  } catch {
    return { type: eventType, data: { raw: trimmed } }
  }
}
