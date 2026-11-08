import { useRef } from 'react'
import Field from '../../editor/Field.jsx'
import { identError, simplevalError } from '../../editor/ast.js'
import { useEditor } from '../../editor/EditorContext.jsx'
import { DeleteButton, Handle, Kw } from './BlockParts.jsx'
import useBlockRing from './useBlockRing.js'
import ValueBlock from './ValueBlock.jsx'

export default function CommandBlock({ node }) {
  const { select, update, focusId, clearFocus } = useEditor()
  const blockRef = useRef(null)
  const ring = useBlockRing(node.id)
  const first = focusId === node.id

  const argField = (
    <Field
      value={node.arg}
      check={simplevalError}
      onCommit={(v) => update(node.id, (n) => { n.arg = v })}
      autoFocus={first}
      onFocus={clearFocus}
    />
  )

  let content
  if (node.type === 'step') content = <><Kw>step forward</Kw>{argField}</>
  else if (node.type === 'turn') content = <><Kw>turn by</Kw>{argField}</>
  else if (node.type === 'print') content = <><Kw>print</Kw>{argField}</>
  else if (node.type === 'mine') content = <Kw>mine here</Kw>
  else if (node.type === 'set') {
    content = (
      <>
        <Kw>set</Kw>
        <Field
          value={node.ident}
          check={identError}
          onCommit={(v) => update(node.id, (n) => { n.ident = v })}
          placeholder='név'
          autoFocus={first}
          onFocus={clearFocus}
        />
        <Kw>to</Kw>
        <ValueBlock node={node} />
      </>
    )
  } else content = <span>ismeretlen blokk: {node.type}</span>

  return (
    <div
      ref={blockRef}
      data-node-id={node.id}
      onClick={(e) => { e.stopPropagation(); select(node.id) }}
      className={`flex flex-wrap items-center gap-1.5 rounded border-[0.15rem] border-blue-400 bg-blue-100 px-1.5 py-1 ${ring}`}
    >
      <Handle id={node.id} blockRef={blockRef} />
      {content}
      <DeleteButton id={node.id} />
    </div>
  )
}
