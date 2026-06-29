import { expect } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

// Mock scrollIntoView (not available in jsdom)
Element.prototype.scrollIntoView = () => {}

// Mock window.webkitSpeechRecognition
Object.defineProperty(window, 'webkitSpeechRecognition', { value: undefined })
Object.defineProperty(window, 'SpeechRecognition', { value: undefined })
