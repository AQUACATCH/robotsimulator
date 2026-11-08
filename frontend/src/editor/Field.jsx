import { useState } from 'react'
import { useEditor } from './EditorContext.jsx'

export default function Field({ value, check, onCommit, placeholder = '…', autoFocus = false, onFocus }) {
  const { showEmpty } = useEditor()
  const [draft, setDraft] = useState(value)

  const toAst = (text) => (check(text) ? '' : text)

  const [prevValue, setPrevValue] = useState(value)
  if (value !== prevValue) {
    setPrevValue(value)
    if (value !== toAst(draft)) setDraft(value)
  }

  const error = check(draft)

  function handleChange(e) {
    const v = e.target.value.replace(/\s/g, '')
    setDraft(v)
    if (toAst(v) !== value) onCommit(toAst(v))
  }

  let color = 'border-gray-400 bg-white'
  if (draft === '') color = showEmpty ? 'border-red-500 bg-red-100' : 'border-gray-400 bg-amber-50'
  if (error) color = 'border-red-600 bg-red-50'

  return (
    <span className='relative inline-flex flex-col'>
      <input
        className={`rounded border px-1.5 py-0.5 font-mono text-sm ${color}`}
        value={draft}
        placeholder={placeholder}
        size={Math.max(3, draft.length + 1)}
        spellCheck={false}
        aria-invalid={error ? true : undefined}
        title={error ?? undefined}
        autoFocus={autoFocus}
        onFocus={onFocus}
        onChange={handleChange}
      />
      {error && (
        <span className='absolute top-full left-0 z-20 mt-0.5 whitespace-nowrap rounded bg-red-600 px-1.5 py-0.5 text-xs text-white'>
          {error}
        </span>
      )}
    </span>
  )
}