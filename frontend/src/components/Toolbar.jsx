import { GROUPS, PALETTE } from '../tools.js'
import { beginDrag, endDrag, isOurs, readDrag } from '../editor/dnd.js'
import { useEditor } from '../editor/EditorContext.jsx'

function PaletteItem({ item }) {
  const { setDrag, insertAtCursor, canClickInsert } = useEditor()
  const clickOk = canClickInsert(item.kind)

  return (
    <div
      role='button'
      tabIndex={0}
      aria-disabled={!clickOk}
      draggable
      data-kind={item.kind}
      onDragStart={(e) => beginDrag(e, { src: 'palette', kind: item.kind }, setDrag, 'copy')}
      onDragEnd={() => endDrag(setDrag)}
      onClick={() => insertAtCursor(item.kind)}
      onKeyDown={(e) => {
        if (e.key !== 'Enter' && e.key !== ' ') return
        e.preventDefault()
        insertAtCursor(item.kind)
      }}
      title={clickOk
        ? 'Húzd a Program Tervezőbe, vagy kattints rá'
        : 'A kijelölt helyre nem tehető (max. 3 szint) – húzd máshová'}
      className={`${item.cls} cursor-grab select-none rounded border-[0.15rem] p-1 ${clickOk ? '' : 'opacity-50'}`}
    >
      {item.label}
    </div>
  )
}

const Toolbar = () => {
  const { drag, setDrag, deleteBlock } = useEditor()
  const trash = drag?.src === 'canvas'

  function onDragOver(e) {
    if (!isOurs(e) || readDrag(e)?.src !== 'canvas') return
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  function onDrop(e) {
    e.preventDefault()
    const payload = readDrag(e)
    endDrag(setDrag)
    if (payload?.src === 'canvas') deleteBlock(payload.id)
  }

  const frame = trash ? 'border-red-400 bg-red-50' : 'border-gray-400 bg-white'

  return (
    <div
      data-trash
      onDragOver={onDragOver}
      onDrop={onDrop}
      className={`p-4 flex flex-col gap-5 border rounded flex-1 min-w-0 overflow-auto ${frame}`}
    >
      <h1 className='text-gray-400 font-bold text-xl uppercase'>{trash ? 'Ejtsd ide a törléshez' : 'Blokkok'}</h1>
      <p className='-mt-3 text-xs text-gray-500'>Húzd a blokkot a Program Tervezőbe, vagy kattints rá.</p>

      {GROUPS.map((g) => (
        <div key={g.group} className='flex flex-col gap-2'>
          <h2 className='text-gray-400 font-bold uppercase'>{g.title}</h2>
          {PALETTE.filter((item) => item.group === g.group).map((item) => (
            <PaletteItem key={item.kind} item={item} />
          ))}
        </div>
      ))}

      <div className='flex flex-col gap-2'>
        <h2 className='text-gray-400 font-bold uppercase'>Érték-blokkok</h2>
        <p className='rounded border-2 border-green-500 bg-green-100 p-1 text-sm'>
          A set blokk „to” utáni részén, a legördülőből választhatók: érték, isThere, művelet, not.
        </p>
      </div>
    </div>
  )
}

export default Toolbar