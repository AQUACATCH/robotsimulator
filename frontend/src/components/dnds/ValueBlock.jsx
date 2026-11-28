import Field from '../../editor/Field.jsx'
import { identError, simplevalError } from '../../editor/ast.js'
import { useEditor } from '../../editor/EditorContext.jsx'
import { Kw } from './BlockParts.jsx'

const OPS = ['+', '-', '*', '=', '<>', '<', '<=', '>', '>=', 'and', 'or', '@']
const UNARY = ['not', 'length']

export default function ValueBlock({ node }) {
  const { update } = useEditor()
  const v = node.value
  const choice = v.kind === 'unop' ? v.op : v.kind

  const setValue = (mutate) => update(node.id, (n) => mutate(n.value))

  function changeKind(kind) {
    update(node.id, (n) => {
      const a = n.value.a ?? ''
      if (kind === 'simple') n.value = { kind, a }
      if (kind === 'isThere') n.value = { kind, a }
      if (kind === 'safeToDrill' || kind === 'list') n.value = { kind }
      if (UNARY.includes(kind)) n.value = { kind: 'unop', op: kind, a }
      if (kind === 'binop') n.value = { kind, op: '+', a, b: n.value.b ?? '' }
    })
  }

  const field = (key, check = simplevalError, placeholder) => (
    <Field value={v[key]} check={check} placeholder={placeholder}
      onCommit={(x) => setValue((val) => { val[key] = x })} />
  )

  const selectCls = 'rounded border border-green-500 bg-white px-0.5 text-xs'

  return (
    <span
      className='inline-flex items-center gap-1.5 rounded border-2 border-green-500 bg-green-100 px-1.5 py-0.5'
    >
      <select className={selectCls} value={choice} onChange={(e) => changeKind(e.target.value)}
        title='Érték-blokk fajtája' aria-label='Érték-blokk fajtája'>
        <option value='simple'>érték</option>
        <option value='isThere'>isThere</option>
        <option value='safeToDrill'>safeToDrill</option>
        <option value='binop'>művelet</option>
        <option value='not'>not</option>
        <option value='list'>üres lista</option>
        <option value='length'>length</option>
      </select>
      {v.kind === 'simple' && field('a')}
      {v.kind === 'isThere' && <><Kw>isThere</Kw>{field('a')}</>}
      {v.kind === 'safeToDrill' && <Kw>safeToDrill</Kw>}
      {v.kind === 'list' && <Kw>list</Kw>}
      {v.kind === 'unop' && (
        <><Kw>{v.op}</Kw>{v.op === 'length' ? field('a', identError, 'lista') : field('a')}</>
      )}
      {v.kind === 'binop' && (
        <>
          {v.op === '@' ? field('a', identError, 'lista') : field('a')}
          <select className={selectCls} value={v.op} aria-label='Művelet'
            title={v.op === '@' ? 'Listaelem: a lista adott indexű eleme (0-tól számozva)' : 'Művelet'}
            onChange={(e) => setValue((val) => { val.op = e.target.value })}>
            {OPS.map((op) => <option key={op} value={op}>{op}</option>)}
          </select>
          {field('b')}
        </>
      )}
    </span>
  )
}
