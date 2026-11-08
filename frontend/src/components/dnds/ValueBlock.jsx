import Field from '../../editor/Field.jsx'
import { simplevalError } from '../../editor/ast.js'
import { useEditor } from '../../editor/EditorContext.jsx'
import { Kw } from './BlockParts.jsx'

const OPS = ['+', '-', '*', '=', '<>', '<', '<=', '>', '>=', 'and', 'or']

export default function ValueBlock({ node }) {
  const { update } = useEditor()
  const v = node.value

  const setValue = (mutate) => update(node.id, (n) => mutate(n.value))

  function changeKind(kind) {
    update(node.id, (n) => {
      const a = n.value.a ?? ''
      if (kind === 'simple') n.value = { kind, a }
      if (kind === 'isThere') n.value = { kind, a }
      if (kind === 'unop') n.value = { kind, op: 'not', a }
      if (kind === 'binop') n.value = { kind, op: '+', a, b: n.value.b ?? '' }
    })
  }

  const field = (key) => (
    <Field value={v[key]} check={simplevalError} onCommit={(x) => setValue((val) => { val[key] = x })} />
  )

  const selectCls = 'rounded border border-green-500 bg-white px-0.5 text-xs'

  return (
    <span
      className='inline-flex items-center gap-1.5 rounded border-2 border-green-500 bg-green-100 px-1.5 py-0.5'
    >
      <select className={selectCls} value={v.kind} onChange={(e) => changeKind(e.target.value)}
        title='Érték-blokk fajtája' aria-label='Érték-blokk fajtája'>
        <option value='simple'>érték</option>
        <option value='isThere'>isThere</option>
        <option value='binop'>művelet</option>
        <option value='unop'>not</option>
      </select>
      {v.kind === 'simple' && field('a')}
      {v.kind === 'isThere' && <><Kw>isThere</Kw>{field('a')}</>}
      {v.kind === 'unop' && <><Kw>not</Kw>{field('a')}</>}
      {v.kind === 'binop' && (
        <>
          {field('a')}
          <select className={selectCls} value={v.op} aria-label='Művelet'
            onChange={(e) => setValue((val) => { val.op = e.target.value })}>
            {OPS.map((op) => <option key={op} value={op}>{op}</option>)}
          </select>
          {field('b')}
        </>
      )}
    </span>
  )
}