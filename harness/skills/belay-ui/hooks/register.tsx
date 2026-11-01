// Belay's terminal surface (a Claude Code mod).
//
// Optional equipment, never the rope: Belay works fully without it (mods are
// early access and can be switched off remotely). So it gates nothing, does
// no math, and does not repeat the stable layer in .claude/settings.json
// (status line, spinner verbs, tips). It adds the rhythm band, the /belay
// month view and a quiet receipt after the scripts run.

import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Status, Theme } from '../types'
import { band, paneMarkdown, paneSvg, paneTerminal, SOURCE_LINE } from './draw'
import { COLORS, themeOf } from './palette'
import { load } from './view'

const PANE = 'belay'
const SCRIPT_RUN = /harness\/scripts\/(reconcile|plan_month|ingest|render_report)\.py/

const statusAtom = atom({ plugin: 'belay-ui', key: 'status' } as const, null as Status | null)
const themeAtom = atom({ plugin: 'belay-ui', key: 'theme' } as const, 'dark' as Theme)

async function refresh($: EngineInterface): Promise<Status | null> {
  try {
    const s = await load($)
    await update($, statusAtom, () => s)
    return s
  } catch {
    // no uv / no workspace yet: stay quiet, the conversation path still works
    await update($, statusAtom, () => null)
    return null
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'belay',
      description: 'The month at a glance: last closed month, planned extras (numbers from status.py)',
    })
    try {
      const row = (await $.config.list()).find(r => r.key === 'theme')
      await update($, themeAtom, () => themeOf(row?.value))
    } catch {
      // keep the dark palette; it reads on light backgrounds too
    }
    await refresh($)
    return next(e)
  })

  // A deterministic script just ran: refresh, and a quiet receipt naming it.
  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    const command = (e as { command?: unknown }).command
    if (typeof command === 'string' && SCRIPT_RUN.test(command) && ran.deny === undefined) {
      const s = await refresh($)
      if (s?.situation === 'rhythm') $.ui.toast('Checked by the scripts · /belay to see the month')
    }
    return ran
  }).catch(($, e, next) => next(e)) // not a gate: on failure the call goes on unchanged

  on('turn.complete', async ($, e, next) => {
    await refresh($)
    return next(e)
  })

  on('command.run', { command: 'belay' }, async ($, e) => {
    const s = await refresh($)
    const { isPlaced } = await $.ui.open({ id: PANE, title: 'Belay' })
    // Text where nothing draws, and when asked from a phone or claude.ai over Remote
    // Control: the pane would open in the machine's terminal, which nobody is watching
    const fromBridge = e.origin.kind === 'bridge'
    return isPlaced && !fromBridge
      ? { text: 'Month view opened.' }
      : { text: s ? paneMarkdown(s) : SOURCE_LINE }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey) return next(e)
    const s = await read($, statusAtom)
    if (s === null) return next(e)
    return band($.ui.resolve(e), s, COLORS[await read($, themeAtom)])
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const s = await read($, statusAtom)
    const c = COLORS[await read($, themeAtom)]
    if (e.surface === 'terminal') {
      const t = $.ui.resolve(e)
      return s === null
        ? <t.Text dimColor>The month view draws from harness/scripts/status.py — it did not run.</t.Text>
        : paneTerminal(t, s, c, e.props.bodyColumns)
    }
    const { Box, Svg, Text } = $.ui.resolve(e)
    if (s === null || s.situation !== 'rhythm' || !s.closed_month) {
      return <Text>The month view fills in once a month is closed.</Text>
    }
    const { source, alt } = paneSvg(s)
    return (
      <Box flexDirection="column" gap={1}>
        <Svg source={source} alt={alt} />
        <Text size="footnote" dimColor>{SOURCE_LINE}</Text>
      </Box>
    )
  })

  on('ui.render', { component: 'PromptHint' }, async ($, e, next) =>
    e.props.isDraft || e.props.isWorking
      ? next(e)
      : next({ ...e, props: { ...e.props, tail: '/belay · /purchase-check' } }),
  )
}
