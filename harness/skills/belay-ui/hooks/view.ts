// Fetch the view-model. No math and no decisions here: run the deterministic
// status script and hand its JSON on. The status line runs the same script.

import type { EngineInterface } from 'claude-code'

import type { Status } from '../types'

export async function load($: EngineInterface): Promise<Status> {
  const { exitCode, stdout } = await $.process.run(
    ['uv', 'run', '--quiet', 'harness/scripts/status.py', 'finance'],
    { timeoutMs: 30_000 },
  )
  if (exitCode !== 0) throw new Error(`status.py exited ${exitCode}`)
  return JSON.parse(stdout) as Status
}
