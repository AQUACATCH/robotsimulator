import { useEditor } from '../editor/EditorContext.jsx'
import BlockList from './dnds/BlockList.jsx'
import DropSlot from './dnds/DropSlot.jsx'

const Scratchbox = () => {
  const { program, select, emptyIds } = useEditor()

  return (
    <div
      onClick={() => select(null)}
      className='bg-white p-4 flex flex-col gap-3 border border-gray-400 rounded flex-2 min-w-0 overflow-auto bg-[radial-gradient(#e5e7eb_2px,transparent_2px)] bg-size-[16px_16px]'
    >
      <h1 className='text-gray-400 font-bold text-xl uppercase'>Program Tervező</h1>

      {emptyIds.size > 0 && (
        <div className='rounded bg-red-100 p-2 text-sm text-red-700'>
          Kitöltetlen mezők vannak (pirossal jelölve) – a programot így nem lehet futtatni.
        </div>
      )}

      {program.length === 0 ? (
        <DropSlot targetId={null} where='end' big fill
          label='A program üres. Húzz ide egy blokkot a bal oldalról, vagy kattints egy blokkra!' />
      ) : (
        <div className='flex flex-1 flex-col'>
          <BlockList list={program} />
          <DropSlot targetId={null} where='end' fill />
        </div>
      )}
    </div>
  )
}

export default Scratchbox