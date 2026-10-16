// Belay's colours: the logo's teal, the report's aqua fill and warm "over".
// Warm is used for one thing only: an ENVELOPE that ran over. Awareness
// targets never turn warm (D2a: a reference, not a limit). No red anywhere.

import type { Theme } from '../types'

export type Colors = { teal: string; fill: string; warm: string; track: string; tick: string }

export const COLORS: Record<Theme, Colors> = {
  light: { teal: '#2f9e92', fill: '#1baf7a', warm: '#ec835a', track: '#c3c2b7', tick: '#191817' },
  dark: { teal: '#2f9e92', fill: '#199e70', warm: '#ec835a', track: '#4a4945', tick: '#eceae2' },
}

export const themeOf = (value: unknown): Theme =>
  typeof value === 'string' && value.includes('light') ? 'light' : 'dark'
