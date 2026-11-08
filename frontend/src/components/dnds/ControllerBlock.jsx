import { useRef } from 'react'
import Field from '../../editor/Field.jsx'
import { simplevalError } from '../../editor/ast.js'
import { useEditor } from '../../editor/EditorContext.jsx'
import BlockList from './BlockList.jsx'
import { DeleteButton, Handle, Kw } from './BlockParts.jsx'
import useBlockRing from './useBlockRing.js'

export default function ControllerBlock({ node }) {
  const { select, update, focusId, clearFocus } = useEditor()
  const blockRef = useRef(null)
  const ring = useBlockRing(node.id)

  const body = (list, branch, emptyLabel) => (
    <div className='ml-3 border-l-4 border-orange-300 pl-2 py-0.5'>
      <BlockList list={list} parentId={node.id} branch={branch} emptyLabel={emptyLabel} />
    </div>
  )

  return (
    <div
      ref={blockRef}
      data-node-id={node.id}
      onClick={(e) => { e.stopPropagation(); select(node.id) }}
      className={`flex flex-col gap-0.5 rounded border-[0.15rem] border-orange-300 bg-orange-100 px-1.5 py-1 ${ring}`}
    >
      <div className='flex items-center gap-1.5'>
        <Handle id={node.id} blockRef={blockRef} />
        <Kw>{node.type}</Kw>
        <Field
          value={node.cond}
          check={simplevalError}
          onCommit={(v) => update(node.id, (n) => { n.cond = v })}
          placeholder='feltétel'
          autoFocus={focusId === node.id}
          onFocus={clearFocus}
        />
        <DeleteButton id={node.id} />
      </div>

      {node.type === 'while' && body(node.body, 'body', 'üres törzs – húzz ide egy blokkot')}
      {node.type === 'if' && body(node.then, 'then', 'üres törzs – húzz ide egy blokkot')}
      {node.type === 'if' && node.else && (
        <>
          <div className='flex items-center gap-1.5 pl-5'><Kw>else</Kw></div>
          {body(node.else, 'else', 'üres törzs – húzz ide egy blokkot')}
        </>
      )}
    </div>
  )
}