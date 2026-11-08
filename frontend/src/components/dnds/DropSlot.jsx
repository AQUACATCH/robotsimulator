import { useState } from 'react'
import { slotState } from '../../editor/ast.js'
import { isOurs, readDrag } from '../../editor/dnd.js'
import { useEditor } from '../../editor/EditorContext.jsx'

export default function DropSlot({ targetId, where, big = false, fill = false, label }) {
  const { program, drag, drop } = useEditor()
  const [over, setOver] = useState(false)
  const st = slotState(program, drag, targetId, where)

  if (!drag && over) setOver(false)

  function allowed(e) {
    return slotState(program, readDrag(e), targetId, where) === 'ok'
  }

  function onDragOver(e) {
    if (!isOurs(e)) return
    e.stopPropagation()
    if (!over) setOver(true)
    if (!allowed(e)) {
      e.dataTransfer.dropEffect = 'none'
      return
    }
    e.preventDefault()
    e.dataTransfer.dropEffect = readDrag(e).src === 'palette' ? 'copy' : 'move'
  }

  function onDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setOver(false)
    if (allowed(e)) drop(readDrag(e), targetId, where)
  }

  let size = 'h-2'
  if (big) size = 'min-h-10 px-2 py-2 border-2 border-dashed text-xs text-gray-500'
  if (fill) size = 'flex-1 min-h-12'
  if (big && fill) size = 'flex-1 min-h-24 p-4 border-2 border-dashed text-sm text-gray-500'

  let color = big ? 'border-gray-300' : ''
  if (st === 'ok') color = over ? 'bg-blue-500/70 border-blue-500' : 'bg-blue-200/50 border-blue-300'
  if (st === 'deny') color = 'bg-red-300/70 border-red-400'

  const denyText = 'Max. 3 szint – ide nem tehető vezérlőblokk'

  const hit = drag && !big && !fill ? 'z-10 before:absolute before:inset-x-0 before:-inset-y-2' : ''

  return (
    <div
      data-slot={`${targetId ?? 'root'}:${where}`}
      data-state={st}
      onDragOver={onDragOver}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      title={st === 'deny' ? 'Ide nem tehető vezérlőblokk: legfeljebb 3 szint mélyen ágyazhatók.' : undefined}
      aria-label={st === 'deny' ? denyText : undefined}
      className={`relative rounded transition-colors ${size} ${color} ${hit}`}
    >
      {big && (
        <span className='pointer-events-none'>
          {st === 'deny' ? denyText : label}
        </span>
      )}
      {!big && over && st === 'deny' && (
        <span className='pointer-events-none absolute top-full left-2 z-30 mt-0.5 whitespace-nowrap rounded bg-red-600 px-1.5 py-0.5 text-xs text-white'>
          {denyText}
        </span>
      )}
    </div>
  )
}