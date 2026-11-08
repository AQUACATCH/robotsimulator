import { useEditor } from '../editor/EditorContext.jsx'

const CodeShowcase = () => {
  const { source, lineMap, highlight, select } = useEditor()
  const lines = source === '' ? [] : source.split('\n')

  return (
    <div className='bg-white p-4 flex flex-col gap-5 border border-gray-400 rounded flex-1 min-w-0 overflow-auto'>
      <h1 className='text-gray-400 font-bold text-xl uppercase'>Szöveges Nézet</h1>
      <div data-code className='font-mono text-sm'>
        {lines.length === 0 && <div className='text-gray-400'>A program üres.</div>}
        {lines.map((text, i) => {
          const no = i + 1
          const current = Number(highlight.line) === no
          return (
            <div
              key={no}
              data-code-line={no}
              onClick={() => { if (lineMap[no]) select(lineMap[no]) }}
              className={`flex cursor-pointer gap-3 rounded px-1 whitespace-pre hover:bg-gray-100 ${current ? 'bg-yellow-200' : ''}`}
            >
              <span className='w-6 shrink-0 select-none text-right text-gray-400'>{no}</span>
              <span data-line>{text}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default CodeShowcase