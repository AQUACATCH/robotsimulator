import { beginDrag, endDrag } from '../../editor/dnd.js'
import { useEditor } from '../../editor/EditorContext.jsx'

export function Kw({ children }) {
  return <span className='font-bold'>{children}</span>
}

export function Handle({ id, blockRef }) {
  const { setDrag } = useEditor()

  function onDragStart(e) {
    e.stopPropagation()
    if (blockRef.current) e.dataTransfer.setDragImage(blockRef.current, 12, 12)
    beginDrag(e, { src: 'canvas', id }, setDrag, 'move')
  }

  return (
    <span
      draggable
      onDragStart={onDragStart}
      onDragEnd={() => endDrag(setDrag)}
      data-handle={id}
      title='Fogd meg és húzd'
      className='cursor-grab select-none px-0.5 text-lg leading-none text-gray-500 hover:text-gray-900'
    >
      ⠿
    </span>
  )
}

export function DeleteButton({ id }) {
  const { deleteBlock } = useEditor()
  return (
    <button
      type='button'
      title='Blokk törlése'
      aria-label='Blokk törlése'
      onClick={(e) => { e.stopPropagation(); deleteBlock(id) }}
      className='ml-auto rounded px-1.5 leading-none text-gray-500 hover:bg-red-100 hover:text-red-600'
    >
      ×
    </button>
  )
}