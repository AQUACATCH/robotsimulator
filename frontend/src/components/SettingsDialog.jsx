import { useEffect, useState } from 'react'
import { getSettings, putSettings } from '../api/api.js'
import { useSim } from '../sim/SimContext.jsx'
import { COST_FIELDS } from '../sim/messages.js'

function toForm(settings) {
  return Object.fromEntries(Object.entries(settings).map(([k, v]) => [k, typeof v === 'boolean' ? v : String(v)]))
}

function validate(form) {
  const settings = {}
  for (const [key, value] of Object.entries(form)) {
    if (typeof value === 'boolean') { settings[key] = value; continue }
    if (!/^[0-9]+$/.test(value)) return { error: 'Minden érték nemnegatív egész szám legyen.' }
    settings[key] = Number(value)
  }
  if (settings.battery_cap < 1) return { error: 'Az akkumulátor kapacitása legalább 1 legyen.' }
  return { settings }
}

function NumberField({ label, value, onChange, hint }) {
  return (
    <label className='flex items-center justify-between gap-3 text-sm'>
      <span>{label}{hint && <span className='ml-1 text-xs text-gray-400'>{hint}</span>}</span>
      <input type='number' min={0} step={1} value={value} onChange={(e) => onChange(e.target.value)}
        className='w-20 rounded border border-gray-400 px-1.5 py-0.5 text-right font-mono' />
    </label>
  )
}

export default function SettingsDialog({ onClose }) {
  const sim = useSim()
  const [form, setForm] = useState(() => (sim.world?.settings ? toForm(sim.world.settings) : null))
  const [defaults, setDefaults] = useState(null)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let ignore = false
    getSettings()
      .then((s) => {
        if (ignore) return
        setDefaults(s.defaults)
        setForm((f) => f ?? toForm(s.settings))
      })
      .catch((e) => { if (!ignore) setError(e.message) })
    return () => { ignore = true }
  }, [])

  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }))

  async function save() {
    const { settings, error: invalid } = validate(form)
    if (invalid) { setError(invalid); return }
    setSaving(true)
    sim.halt()
    try {
      const s = await putSettings(settings)
      sim.apply(s)
      sim.setNotice({
        kind: 'info',
        text: s.loaded ? 'Beállítások mentve. A bánya alaphelyzetbe került.' : 'Beállítások mentve.',
      })
      onClose()
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-6' onClick={onClose}>
      <div role='dialog' aria-label='Beállítások' className='flex max-h-full w-full max-w-md flex-col gap-3 overflow-auto rounded bg-white p-4 shadow-2xl'
        onClick={(e) => e.stopPropagation()}>
        <h2 className='text-lg font-bold'>Beállítások</h2>
        {!form ? <p className='text-sm text-gray-500'>Betöltés…</p> : (
          <>
            <NumberField label='Akkumulátor kapacitása' value={form.battery_cap} onChange={set('battery_cap')} />
            <div className='flex flex-col gap-1.5 rounded border border-gray-200 p-2'>
              <div className='text-xs font-bold uppercase text-gray-400'>Műveletek energiaigénye</div>
              {COST_FIELDS.map(([key, label]) => (
                <NumberField key={key} label={<code>{label}</code>} value={form[key]} onChange={set(key)} />
              ))}
              <p className='text-xs text-gray-500'>Egy utasítás egyszer fogyaszt, a lépések vagy fordulások számától függetlenül. A <code>charge</code> nem fogyaszt.</p>
            </div>
            <label className='flex items-start gap-2 text-sm'>
              <input type='checkbox' className='mt-0.5' checked={form.isThere_extended}
                onChange={(e) => set('isThere_extended')(e.target.checked)} />
              <span>
                <code>isThere 3–5</code> engedélyezése
                <span className='block text-xs text-gray-500'>3 = átfúrható kőzet, 4 = támasz, 5 = töltőállomás. Kikapcsolva ezekre E_BAD_ARG a válasz.</span>
              </span>
            </label>
            {error && <p role='alert' className='rounded bg-red-50 px-2 py-1 text-sm font-semibold text-red-700'>{error}</p>}
            <p className='text-xs text-gray-500'>Mentéskor a bánya alaphelyzetbe kerül, a futó program leáll.</p>
            <div className='flex justify-between gap-2'>
              <button type='button' disabled={!defaults} onClick={() => { setForm(toForm(defaults)); setError(null) }}
                className='rounded border px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-40'>Alapértékek</button>
              <div className='flex gap-2'>
                <button type='button' onClick={onClose} className='rounded border px-3 py-1.5 text-sm hover:bg-gray-50'>Mégse</button>
                <button type='button' onClick={save} disabled={saving}
                  className='rounded bg-blue-700 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-40'>Mentés</button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
