// The state contract. `Status` is harness/scripts/status.py's JSON, unchanged:
// every amount is a string the script formatted; the display never derives one.

export type Meter = {
  category: string
  kind: 'envelope' | 'awareness'
  actual: string
  plan: string
  actual_display: string
  plan_display: string
  // only envelopes can be over; awareness targets are a reference ("full is not bad")
  over: boolean
}

export type OverlayItem = { name: string; amount: string; amount_display: string; done: boolean }

export type Situation = 'empty' | 'onboarding' | 'welcome_back' | 'rhythm' | 'unreadable'

export type Status = {
  schema: string
  today: string
  month?: string
  month_name?: string
  situation: Situation
  onboarding?: { next_stage: string } | null
  rhythm?: { plan_ready: boolean; previous_closed: boolean; last_closed: string | null } | null
  overlay?: OverlayItem[]
  closed_month?: { month: string; month_name: string; meters: Meter[] } | null
  next_step: { command: string; label: string }
}

export type Theme = 'light' | 'dark'

declare module 'claude-code' {
  interface PluginState {
    'belay-ui': { status: Status | null; theme: Theme }
  }
}
