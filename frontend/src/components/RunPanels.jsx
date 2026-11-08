import { useEffect, useRef } from 'react'
import { useSim } from '../sim/SimContext.jsx'

export function NoticeBar() {
  const { notice, setNotice } = useSim()
  if (!notice) return null
  const cls = {
    error: 'border-red-600 bg-red-600 text-white',
    warn: 'border-amber-400 bg-amber-100 text-amber-900',
    info: 'border-blue-300 bg-blue-50 text-blue-900',
  }[notice.kind]
  return (
    <div role='alert' className={`mx-4 mt-3 flex items-center justify-between gap-3 rounded border-2 px-3 py-2 font-semibold ${cls}`}>
      <span>{notice.kind === 'error' ? '⚠ ' : ''}{notice.text}</span>
      <button onClick={() => setNotice(null)} className='px-2 opacity-70 hover:opacity-100' aria-label='Bezárás'>×</button>
    </div>
  )
}

function Panel({ title, children, className = '' }) {
  return (
    <div className={`flex min-h-0 min-w-0 flex-col gap-2 rounded border border-gray-400 bg-white p-3 ${className}`}>
      <h2 className='text-sm font-bold uppercase text-gray-400'>{title}</h2>
      {children}
    </div>
  )
}

export function ConsolePanel() {
  const { world } = useSim()
  const lines = world?.console ?? []
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ block: 'nearest' }) }, [lines.length])
  return (
    <Panel title='Konzol (print kimenete)'>
      <div className='h-32 overflow-auto rounded bg-gray-900 p-2 font-mono text-sm text-green-300'>
        {lines.length === 0 && <span className='text-gray-500'>Még nincs kimenet.</span>}
        {lines.map((l, i) => <div key={i}>{String(l)}</div>)}
        <div ref={endRef} />
      </div>
    </Panel>
  )
}

export function VariablesPanel() {
  const { world } = useSim()
  const vars = Object.entries(world?.variables ?? {})
  return (
    <Panel title='Változók'>
      <div className='h-32 overflow-auto'>
        {vars.length === 0 ? (
          <span className='text-sm text-gray-500'>Még nincs változó.</span>
        ) : (
          <table className='w-full text-sm'>
            <thead className='text-left text-xs uppercase text-gray-400'>
              <tr><th className='font-semibold'>Név</th><th className='font-semibold'>Típus</th><th className='font-semibold'>Érték</th></tr>
            </thead>
            <tbody className='font-mono'>
              {vars.map(([name, value]) => (
                <tr key={name} className='border-t border-gray-100'>
                  <td className='py-0.5'>{name}</td>
                  <td className='font-sans text-gray-500'>{typeof value === 'boolean' ? 'logikai' : 'egész'}</td>
                  <td className={typeof value === 'boolean' ? 'text-purple-700' : 'text-blue-700'}>{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Panel>
  )
}

export function LogDialog() {
  const { log, closeLog, refreshLog } = useSim()
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ block: 'nearest' }) }, [log.lines.length])
  if (!log.open) return null
  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6' onClick={closeLog}>
      <div className='flex max-h-full w-full max-w-xl flex-col gap-2 rounded bg-white p-4 shadow-2xl' onClick={(e) => e.stopPropagation()}>
        <div className='flex items-center justify-between gap-2'>
          <h2 className='text-lg font-bold'>Naplófájl</h2>
          <div className='flex gap-2'>
            <button className='rounded border px-2 py-1 text-sm hover:bg-gray-50' onClick={refreshLog}>Frissítés</button>
            <button className='rounded border px-2 py-1 text-sm hover:bg-gray-50' onClick={closeLog}>Bezárás</button>
          </div>
        </div>
        <div className='break-all font-mono text-xs text-gray-500'>{log.path}</div>
        <div className='min-h-40 overflow-auto rounded border bg-gray-50 p-2 font-mono text-sm'>
          {log.lines.length === 0 && <span className='text-gray-400'>A napló üres (még nem futott program).</span>}
          {log.lines.map((l, i) => (
            <div key={i} className={/E_|INSTRUCTION_COUNT/.test(l) ? 'font-bold text-red-600' : l === 'EOR' ? 'font-bold text-green-700' : ''}>{l}</div>
          ))}
          <div ref={endRef} />
        </div>
        <p className='text-xs text-gray-500'>A napló futás közben is frissül, amíg ez az ablak nyitva van.</p>
      </div>
    </div>
  )
}
