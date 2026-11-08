import { useCallback, useEffect, useRef, useState } from 'react'
import { getLog, manual, resetWorld, runStep, startRun, stopRun } from '../api/api.js'
import { ERROR_TEXT, MANUAL_TEXT } from './messages.js'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

export default function useSimulator({ beforeRun, onLine, onClearLine }) {
  const [world, setWorld] = useState(null)
  const [speed, setSpeed] = useState(300)
  const [autoplay, setAutoplay] = useState(false)
  const [notice, setNotice] = useState(null)
  const [log, setLog] = useState({ open: false, path: '', lines: [] })

  const loopToken = useRef(0)
  const speedRef = useRef(speed)
  const logOpenRef = useRef(false)
  const manualQueue = useRef(Promise.resolve())

  function changeSpeed(ms) {
    speedRef.current = ms
    setSpeed(ms)
  }

  const refreshLog = useCallback(async () => {
    try {
      const l = await getLog()
      setLog({ open: true, path: l.path, lines: l.lines })
    } catch (e) {
      setNotice({ kind: 'error', text: 'A napló nem olvasható: ' + e.message })
    }
  }, [])

  const apply = useCallback((state) => {
    setWorld(state)
    if (logOpenRef.current) refreshLog()
  }, [refreshLog])

  function afterStep(state) {
    const ex = state.execution
    const ls = ex.last_step
    if (ls?.line) onLine(ls.line, ls.node_id)
    else onClearLine()
    if (ex.status === 'error' || ex.status === 'limit_exceeded') {
      const where = ls?.line ? ` (${ls.line}. sor)` : ''
      setNotice({ kind: 'error', text: `${ex.error}: ${ERROR_TEXT[ex.error] ?? ''}${where}` })
    } else if (ex.status === 'finished') {
      setNotice({ kind: 'info', text: 'A program hiba nélkül lefutott.' })
    }
  }

  function cancelLoop() {
    loopToken.current += 1
    setAutoplay(false)
  }

  async function runLoop() {
    const token = ++loopToken.current
    setAutoplay(true)
    try {
      while (token === loopToken.current) {
        const s = await runStep()
        if (token !== loopToken.current) break
        apply(s)
        afterStep(s)
        if (s.execution.status !== 'running') break
        await sleep(speedRef.current)
      }
    } catch (e) {
      if (e.status !== 409) setNotice({ kind: 'error', text: e.message })
    } finally {
      if (token === loopToken.current) setAutoplay(false)
    }
  }

  async function start(mode) {
    cancelLoop()
    if (!(await beforeRun())) {
      setNotice({ kind: 'warn', text: 'Futtatás előtt töltsd ki a pirossal jelölt mezőket!' })
      return
    }
    try {
      const s = await startRun(mode)
      onClearLine()
      setNotice(mode === 'debug'
        ? { kind: 'info', text: 'Nyomkövetés: a Lépés gombbal hajthatod végre a következő sort.' }
        : null)
      apply(s)
      if (mode === 'run') runLoop()
    } catch (e) {
      setNotice({ kind: 'warn', text: e.message })
    }
  }

  async function step() {
    if (autoplay) return
    try {
      const s = await runStep()
      apply(s)
      afterStep(s)
    } catch (e) {
      setNotice({ kind: 'error', text: e.message })
    }
  }

  function resume() {
    if (world?.execution.running && !autoplay) runLoop()
  }

  async function stop() {
    cancelLoop()
    const s = await stopRun()
    apply(s)
    setNotice({ kind: 'info', text: 'A futás leállítva.' })
  }

  async function reset() {
    cancelLoop()
    const s = await resetWorld()
    apply(s)
    onClearLine()
    setNotice(null)
  }

  function manualAction(action) {
    const wasRunning = world?.execution.running
    cancelLoop()
    manualQueue.current = manualQueue.current.then(() => doManual(action, wasRunning))
    return manualQueue.current
  }

  async function doManual(action, wasRunning) {
    try {
      const s = await manual(action)
      apply(s)
      onClearLine()
      const err = s.manual_result?.error
      if (err) setNotice({ kind: 'warn', text: MANUAL_TEXT[err] ?? err })
      else if (wasRunning) setNotice({ kind: 'info', text: 'Kézi vezérlés: a program futása megszakadt.' })
      else setNotice(null)
    } catch (e) {
      setNotice({ kind: 'error', text: e.message })
    }
  }

  async function openLog() {
    logOpenRef.current = true
    await refreshLog()
  }

  function closeLog() {
    logOpenRef.current = false
    setLog((l) => ({ ...l, open: false }))
  }

  useEffect(() => {
    function onKey(e) {
      const tag = e.target.tagName
      if (['INPUT', 'SELECT', 'TEXTAREA', 'BUTTON'].includes(tag) || e.ctrlKey || e.altKey || e.metaKey) return
      if (e.key === 'ArrowUp') { e.preventDefault(); manualAction('step') }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); manualAction('turn') }
      else if (e.key === 'm' || e.key === 'M') { e.preventDefault(); manualAction('mine') }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const ex = world?.execution
  return {
    world, apply, speed, changeSpeed, autoplay, notice, setNotice, log,
    start, step, resume, stop, reset, manualAction, openLog, closeLog, refreshLog,
    running: !!ex?.running,
    debugging: !!ex?.running && ex.mode === 'debug',
  }
}
