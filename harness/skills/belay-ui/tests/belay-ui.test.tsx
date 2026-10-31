// What these tests prove:
// 1. Provenance: every digit on screen is a string status.py wrote.
// 2. Tone: the ambient band shows no amounts at all; welcome-back shows no
//    month, list or number; only an ENVELOPE over its plan turns warm, an
//    awareness target over its reference never does ("full is not bad").
// 3. Fallback: where no pane can be drawn, /belay answers as markdown.
// The fixtures are status.py's real output for examples/demo-workspace.

import { describe, expect, test } from 'claude-code/testing'
import type { Engine } from 'claude-code/testing'
import type { On } from 'claude-code'

const PLUGIN = 'belay-ui'

const JUNE_METERS = [
  { category: 'groceries', kind: 'awareness', actual: '313.77', plan: '329.0', actual_display: '314', plan_display: '329', over: false },
  { category: 'car', kind: 'awareness', actual: '61.67', plan: '82.0', actual_display: '62', plan_display: '82', over: false },
  { category: 'eating_out', kind: 'awareness', actual: '77.25', plan: '28.0', actual_display: '77', plan_display: '28', over: false },
  { category: 'subscriptions', kind: 'awareness', actual: '24.24', plan: '22.0', actual_display: '24', plan_display: '22', over: false },
]

// --today 2026-07-20
const JULY = {
  schema: 'belay-status/1', today: '2026-07-20', month: '2026-07', month_name: 'July', situation: 'rhythm', onboarding: null,
  rhythm: { plan_ready: true, previous_closed: true, last_closed: '2026-06' },
  overlay: [
    { name: 'Annual car insurance', amount: '420.0', amount_display: '420', done: false },
    { name: "Sister's birthday weekend (dinner + gift)", amount: '80.0', amount_display: '80', done: false },
  ],
  closed_month: { month: '2026-06', month_name: 'June', meters: JUNE_METERS },
  next_step: { command: '/purchase-check', label: 'thinking about a buy? a quick, factual picture' },
}

// --today 2026-10-16
const OCTOBER = {
  schema: 'belay-status/1', today: '2026-10-16', month: '2026-10', month_name: 'October', situation: 'welcome_back',
  onboarding: null, rhythm: null, overlay: [], closed_month: null,
  next_step: { command: '/welcome-back', label: 'a five-minute catch-up, whenever you like' },
}

// the same June, with groceries as an envelope that ran over (status.py sets `over`)
const ENVELOPE_OVER = {
  ...JULY,
  closed_month: {
    month: '2026-06', month_name: 'June',
    meters: [{ category: 'groceries', kind: 'envelope', actual: '351.20', plan: '332.96', actual_display: '351', plan_display: '333', over: true }, ...JUNE_METERS.slice(1)],
  },
}

const BANNED = /missed|overdue|behind|\blate\b|fail|should have|again|sorry|unfortunately|\bonly\b/i
const WARM = '#ec835a'

function base(on: On, opts: { status?: object; placed?: boolean } = {}) {
  const toasts: string[] = []
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('command.register', ($, e) => ({ value: { command: e.name } }))
  on('config.list', () => ({ value: [] }))
  on('ui.toast', ($, e) => {
    toasts.push(e.text)
    return { value: undefined }
  })
  on('ui.open', () => ({ value: opts.placed === false ? { isPlaced: false, reason: 'no-surface' } : { isPlaced: true } }) as never)
  on('process.run', ($, e) => {
    expect(e.argv).toEqual(['uv', 'run', '--quiet', 'harness/scripts/status.py', 'finance'])
    const stdout = JSON.stringify(opts.status ?? JULY)
    return { value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>{''}</Text>
  })
  return toasts
}

const BAND = {
  plugin: PLUGIN, component: 'AbovePrompt' as const,
  props: { hasSurvey: false, isWorking: false, maxRows: 8, bodyColumns: 110, scroll: { offset: 0, bodyRows: 8 }, view: {} },
}
const PANE = {
  plugin: PLUGIN, component: 'Pane' as const, requestId: 'belay',
  props: { title: 'Belay', isFocused: false, bodyColumns: 70, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 30 }, view: {} },
}

const start = ($: { session: { start: (e: { cwd: string; surface: 'terminal'; isInteractive: boolean }) => Promise<unknown> } }) =>
  $.session.start({ cwd: '/finance-repo', surface: 'terminal', isInteractive: true })

const allowed = (s: unknown): Set<string> => {
  const out = new Set<string>()
  const walk = (v: unknown) => {
    if (typeof v === 'string' && /^-?\d+(\.\d+)?$/.test(v)) out.add(v.replace(/^-/, ''))
    else if (Array.isArray(v)) v.forEach(walk)
    else if (v && typeof v === 'object') Object.values(v).forEach(walk)
  }
  walk(s)
  return out
}

// digits on screen, minus dates and the script names' digits (none today)
const figures = (text: string): string[] =>
  text.replace(/\d{4}-\d{2}(-\d{2})?/g, ' ').match(/\d+(\.\d+)?/g) ?? []

const allText = async (ui: { findAll: (q: object) => Promise<{ text: string; props: Record<string, unknown> }[]> }) =>
  (await ui.findAll({})).map(t => `${t.text} ${String(t.props.alt ?? '')}`).join('\n')

describe('the band above the prompt', () => {
  test('rhythm: month, what is done, the next small step, planned extras by name', async ($, on) => {
    base(on)
    await start($)
    for (const surface of ['terminal', 'desktop'] as const) {
      const ui = await $.ui.mount({ ...BAND, surface })
      const text = await allText(ui)
      expect(text).toContain('Belay')
      expect(text).toContain('July')
      expect(text).toContain('plan ✓')
      expect(text).toContain('June closed ✓')
      expect(text).toContain('/purchase-check')
      expect(text).toContain('Annual car insurance')
      await ui.unmount()
    }
  })

  for (const [name, status] of [['rhythm', JULY], ['envelope over', ENVELOPE_OVER], ['welcome back', OCTOBER]] as const) {
    test(`ambient means no amounts: no figure in the band (${name})`, async ($, on) => {
      base(on, { status })
      await start($)
      const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
      expect(figures(await allText(ui))).toEqual([])
      await ui.unmount()
    })
  }

  test('welcome back: warm first sentence, no month, no list, no number', async ($, on) => {
    base(on, { status: OCTOBER })
    await start($)
    const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
    const text = await allText(ui)
    expect(text).toContain('Good to see you.')
    expect(text).toContain('/welcome-back')
    expect(text).not.toContain('October')
    expect(BANNED.test(text)).toBe(false)
    await ui.unmount()
  })
})

describe('the /belay month view', () => {
  test('provenance: every figure on screen is a string status.py wrote', async ($, on) => {
    base(on)
    await start($)
    const ok = allowed(JULY)
    for (const surface of ['terminal', 'desktop', 'mobile'] as const) {
      const ui = await $.ui.mount({ ...PANE, surface })
      const nums = figures(await allText(ui))
      expect(nums.length).toBeGreaterThan(7)
      for (const n of nums) expect(ok.has(n)).toBe(true)
      await ui.unmount()
    }
  })

  const barColors = async ($: Engine) => {
    const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })
    const colors = (await ui.findAll({ type: 'Text' })).filter(t => t.text.includes('█')).map(t => t.props.color)
    await ui.unmount()
    return colors
  }

  test('awareness over its reference stays calm (eating_out 77 vs 28 is not a limit)', async ($, on) => {
    base(on)
    await start($)
    expect(await barColors($)).not.toContain(WARM)
  })

  test('an envelope over its plan, and only that, turns warm', async ($, on) => {
    base(on, { status: ENVELOPE_OVER })
    await start($)
    expect((await barColors($)).filter(c => c === WARM)).toHaveLength(1)
  })

  test('tone: no banned words on any surface', async ($, on) => {
    base(on)
    await start($)
    for (const cel of [BAND, PANE]) {
      const ui = await $.ui.mount({ ...cel, surface: 'terminal' } as never)
      expect(BANNED.test(await allText(ui))).toBe(false)
      await ui.unmount()
    }
  })

  test('/belay without a surface answers as markdown with the same figures', async ($, on) => {
    base(on, { placed: false })
    await start($)
    const out = await $.command.run({
      command: 'belay', args: '', origin: { kind: 'person' } as never,
      presentation: { isFullscreen: false, columns: 100 } as never,
    })
    expect(out.text ?? '').toContain('| eating_out | 77 | 28 | reference |')
    expect(out.text ?? '').toContain('○ Annual car insurance (420)')
  })

  test('a receipt after a deterministic script runs, without figures', async ($, on) => {
    const toasts = base(on)
    on('tool.call', () => ({ result: {}, text: 'ok' }) as never)
    await start($)
    await $.tool.call({ tool: 'Bash', command: 'uv run harness/scripts/reconcile.py finance 2026-07' } as never)
    expect(toasts).toEqual(['Checked by the scripts · /belay to see the month'])
  })
})
