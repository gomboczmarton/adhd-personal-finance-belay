// Drawing: pure functions from the view-model to a tree. Two rules the tests
// hold: GEOMETRY may be derived (how long a bar is), a DISPLAYED FIGURE may
// not — every digit on screen is a string status.py wrote. And the ambient
// band carries rhythm, never amounts.

import type { BoxProps, ElementConstructor, RenderElement, TextProps } from 'claude-code'

import type { Meter, Status } from '../types'
import type { Colors } from './palette'

export type Base = {
  Box: ElementConstructor<BoxProps>
  Text: ElementConstructor<TextProps>
}

export const SOURCE_LINE = 'Numbers: harness/scripts/status.py ← reconcile.py · the display does no math'

// Bar cells for one meter: [fill, warm, track, tickAt] — geometry only.
// Envelope: capacity bar, warm past the plan. Awareness: a reference tick at
// the target, the fill may pass it and stays the same colour.
export const bar = (m: Meter, width: number): [number, number, number, number] => {
  const actual = Math.max(0, Number(m.actual))
  const plan = Number(m.plan)
  if (!(plan > 0)) return [0, 0, width, -1]
  const scale = Math.max(actual, plan)
  const planAt = Math.round((plan / scale) * width)
  const fillTo = Math.round((actual / scale) * width)
  if (m.kind === 'envelope') {
    return m.over
      ? [planAt, width - planAt, 0, -1]
      : [fillTo, 0, width - fillTo, -1]
  }
  return [fillTo, 0, width - fillTo, Math.min(width - 1, Math.max(0, planAt - 1))]
}

// ── the band above the prompt: rhythm only ───────────────────────────────

export const band = ({ Box, Text }: Base, s: Status, c: Colors): RenderElement => {
  const head = <Text color={c.teal} weight="bold">◉ Belay</Text>
  if (s.situation === 'welcome_back') {
    return (
      <Box flexDirection="row" gap={2}>
        {head}
        <Text wrap="truncate-end">Good to see you. <Text dimColor>{s.next_step.command} is a five-minute catch-up — whenever you like.</Text></Text>
      </Box>
    )
  }
  if (s.situation !== 'rhythm' || !s.rhythm) {
    return (
      <Box flexDirection="row" gap={2}>
        {head}
        <Text dimColor wrap="truncate-end">{s.next_step.label} · {s.next_step.command}</Text>
      </Box>
    )
  }
  const r = s.rhythm
  const lastClosed = s.closed_month?.month_name
  const done = [
    r.plan_ready ? 'plan ✓' : null,
    r.previous_closed && lastClosed ? `${lastClosed} closed ✓` : null,
  ].filter((x): x is string => x !== null)
  const open = (s.overlay ?? []).filter(o => !o.done).map(o => o.name)
  return (
    <Box flexDirection="column">
      <Box flexDirection="row" gap={2}>
        {head}
        <Text>{s.month_name ?? ''}</Text>
        {done.length > 0 ? <Text color={c.teal}>{done.join('  ')}</Text> : null}
        <Text dimColor wrap="truncate-end">next {s.next_step.command} — {s.next_step.label}</Text>
      </Box>
      {open.length > 0
        ? <Box paddingLeft={2}><Text dimColor wrap="truncate-end">this month: {open.join(' · ')}</Text></Box>
        : null}
    </Box>
  )
}

// ── the /belay pane: the pull surface, where numbers live ─────────────────

const LABEL = 14
const FIG = 11 // "1314 / 1329"
const KIND = 9 // "reference" / "envelope"

export const paneTerminal = ({ Box, Text }: Base, s: Status, c: Colors, columns: number): RenderElement => {
  const cm = s.closed_month
  if (s.situation !== 'rhythm' || !cm) {
    return (
      <Box flexDirection="column">
        <Text>The month view fills in once a month is closed.</Text>
        <Text dimColor>{s.next_step.command} — {s.next_step.label}</Text>
      </Box>
    )
  }
  // the bar gets what the fixed columns leave of the pane's inner width
  const width = Math.max(6, Math.min(30, columns - LABEL - FIG - KIND - 4))
  return (
    <Box flexDirection="column">
      <Box flexDirection="row" justifyContent="space-between">
        <Text weight="bold">{cm.month_name} · closed</Text>
        <Text color={c.teal}>✓ reconcile.py</Text>
      </Box>
      {cm.meters.map(m => {
        const [fill, warm, track, tick] = bar(m, width)
        const cells = (from: number, n: number, ch: string) =>
          Array.from({ length: n }, (_, i) => (from + i === tick ? '│' : ch)).join('')
        return (
          <Box flexDirection="row" gap={1}>
            <Box flexShrink={0} width={LABEL}><Text wrap="truncate-end">{m.category}</Text></Box>
            <Box flexShrink={0} width={width}>
              <Text>
                <Text color={c.fill}>{cells(0, fill, '█')}</Text>
                <Text color={c.warm}>{cells(fill, warm, '█')}</Text>
                <Text color={c.track}>{cells(fill + warm, track, '░')}</Text>
              </Text>
            </Box>
            <Box flexShrink={0} width={FIG}>
              <Text wrap="truncate-start">{`${m.actual_display} / ${m.plan_display}`.padStart(FIG)}</Text>
            </Box>
            <Box flexShrink={0} width={KIND}>
              <Text dimColor wrap="truncate-end">{m.kind === 'envelope' ? 'envelope' : 'reference'}</Text>
            </Box>
          </Box>
        )
      })}
      {(s.overlay ?? []).length > 0 ? (
        <Box flexDirection="column" marginTop={1}>
          <Text weight="bold">{s.month_name ?? ''} · planned extras</Text>
          {(s.overlay ?? []).map(o => (
            <Text>
              <Text color={o.done ? c.teal : undefined}>{o.done ? '✓' : '○'}</Text> {o.name} <Text dimColor>{o.amount_display}</Text>
            </Text>
          ))}
        </Box>
      ) : null}
      <Box marginTop={1}><Text dimColor>{SOURCE_LINE}</Text></Box>
    </Box>
  )
}

const esc = (x: string): string =>
  x.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

export const paneSvg = (s: Status): { source: string; alt: string } => {
  const cm = s.closed_month
  const ms = cm?.meters ?? []
  const W = 600
  const H = 64 + ms.length * 30 + 12
  const X = 140
  const BW = 300
  const rows = ms.map((m, i) => {
    const y = 56 + i * 30
    const [fill, warm, , tick] = bar(m, BW)
    return [
      `<text x="16" y="${y + 13}" font-family="system-ui, sans-serif" font-size="13" fill="#191817">${esc(m.category)}</text>`,
      `<rect x="${X}" y="${y + 2}" width="${BW}" height="14" rx="7" fill="#e1e0d9"/>`,
      `<rect x="${X}" y="${y + 2}" width="${fill}" height="14" rx="7" fill="#1baf7a"/>`,
      warm > 0 ? `<rect x="${X + fill}" y="${y + 2}" width="${warm}" height="14" rx="7" fill="#ec835a"/>` : '',
      tick >= 0 ? `<rect x="${X + tick}" y="${y - 1}" width="2" height="20" fill="#191817"/>` : '',
      `<text x="${X + BW + 12}" y="${y + 13}" font-family="ui-monospace, Menlo, monospace" font-size="12" fill="#5c5a54">${esc(`${m.actual_display} / ${m.plan_display}`)}</text>`,
    ].join('')
  })
  const source =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">` +
    `<rect width="${W}" height="${H}" rx="12" fill="#f7f6f2"/>` +
    `<text x="16" y="32" font-family="system-ui, sans-serif" font-size="18" font-weight="600" fill="#191817">${esc(cm?.month_name ?? '')} · closed</text>` +
    `<text x="${W - 16}" y="32" text-anchor="end" font-family="ui-monospace, Menlo, monospace" font-size="11" fill="#2f9e92">✓ reconcile.py</text>` +
    rows.join('') +
    `</svg>`
  const alt =
    `${cm?.month_name ?? ''} closed: ` +
    ms.map(m => `${m.category} ${m.actual_display} of ${m.plan_display} (${m.kind === 'envelope' ? 'envelope' : 'reference'})`).join('; ')
  return { source, alt }
}

export const paneMarkdown = (s: Status): string => {
  const cm = s.closed_month
  if (s.situation !== 'rhythm' || !cm) return `The month view fills in once a month is closed. Next: ${s.next_step.command} — ${s.next_step.label}.`
  return [
    `**${cm.month_name} · closed**`,
    '',
    '| category | actual | plan | kind |',
    '|---|---:|---:|---|',
    ...cm.meters.map(m => `| ${m.category} | ${m.actual_display} | ${m.plan_display} | ${m.kind === 'envelope' ? 'envelope' : 'reference'} |`),
    '',
    ...(s.overlay ?? []).map(o => `- ${o.done ? '✓' : '○'} ${o.name} (${o.amount_display})`),
    '',
    `_${SOURCE_LINE}_`,
  ].join('\n')
}
