import * as A from '../src/editor/ast.js'
import assert from 'node:assert/strict'

function valueToText(v) {
  if (v.kind === 'simple') return v.a
  if (v.kind === 'isThere') return `isThere ${v.a}`
  if (v.kind === 'unop') return `not ${v.a}`
  return `${v.a} ${v.op} ${v.b}`
}

function toText(program) {
  const lines = []
  const lineMap = {}
  const emit = (text, depth, id) => {
    lines.push('  '.repeat(depth) + text)
    lineMap[lines.length] = id
  }
  const walk = (list, depth) => {
    for (const n of list) {
      switch (n.type) {
        case 'set': emit(`set ${n.ident} to ${valueToText(n.value)}`, depth, n.id); break
        case 'step': emit(`step forward ${n.arg}`, depth, n.id); break
        case 'turn': emit(`turn by ${n.arg}`, depth, n.id); break
        case 'mine': emit('mine here', depth, n.id); break
        case 'print': emit(`print ${n.arg}`, depth, n.id); break
        case 'while':
          emit(`while ${n.cond}`, depth, n.id)
          walk(n.body, depth + 1)
          break
        case 'if':
          emit(`if ${n.cond}`, depth, n.id)
          walk(n.then, depth + 1)
          if (n.else) {
            emit('else', depth, n.id)
            walk(n.else, depth + 1)
          }
          break
        default: break
      }
    }
  }
  walk(program, 0)
  return { source: lines.join('\n'), lineMap }
}

let p = []
const ins = (target, where, kind, fill) => { const b = A.createBlock(kind); fill?.(b); p = A.insertBlock(p, target, where, b); return b.id }
const w = ins(null, 'end', 'while', b => b.cond = 'megy')
ins(w, 'after', 'print', b => b.arg = 'count')
const ie = ins(w, 'body', 'ifelse', b => b.cond = 'arany')
const s1 = ins(ie, 'then', 'step', b => b.arg = '1'); ins(ie, 'else', 'step', b => b.arg = '1')
const m = ins(s1, 'after', 'mine')
ins(m, 'after', 'set', b => { b.ident = 'count'; b.value = { kind: 'binop', op: '+', a: 'count', b: '1' } })
ins(ie, 'before', 'set', b => { b.ident = 'arany'; b.value = { kind: 'isThere', a: '2' } })
const f = ins(ie, 'after', 'set', b => { b.ident = 'fal'; b.value = { kind: 'isThere', a: '1' } })
ins(f, 'after', 'set', b => { b.ident = 'megy'; b.value = { kind: 'unop', op: 'not', a: 'fal' } })
const mt = ins(w, 'before', 'set', b => { b.ident = 'megy'; b.value = { kind: 'simple', a: 'true' } })
ins(mt, 'before', 'set', b => { b.ident = 'count'; b.value = { kind: 'simple', a: '0' } })

const expected = `set count to 0
set megy to true
while megy
  set arany to isThere 2
  if arany
    step forward 1
    mine here
    set count to count + 1
  else
    step forward 1
  set fal to isThere 1
  set megy to not fal
print count`
const { source, lineMap } = toText(p)
assert.equal(source, expected)
assert.equal(Object.keys(lineMap).length, 13)

assert.ok(A.identError('while')); assert.ok(A.identError('9lives')); assert.ok(A.identError('IsThere'))
assert.equal(A.identError('arany'), null); assert.equal(A.identError('x9'), null)
assert.equal(A.simplevalError('100'), null); assert.ok(A.simplevalError('101')); assert.ok(A.simplevalError('True'))

const it = ins(s1, 'after', 'if', b => b.cond = 'true')
assert.equal(A.canInsertControl(p, it, 'then'), false)
assert.equal(A.canInsertControl(p, it, 'after'), true)
ins(it, 'then', 'print', b => b.arg = '1')
p = A.removeBlock(p, it)
assert.equal(toText(p).source, expected)

const e = ins(null, 'end', 'step')
assert.deepEqual(A.emptyFieldIds(p), [e])

p = A.removeBlock(p, e)
assert.equal(toText(p).source, expected)
const canvas = (id) => ({ src: 'canvas', id })
const palette = (kind) => ({ src: 'palette', kind })

assert.equal(A.slotState(p, null, w, 'after'), 'idle')

assert.equal(A.slotState(p, canvas(w), w, 'body'), 'inert')
assert.equal(A.slotState(p, canvas(w), ie, 'then'), 'inert')
assert.equal(A.slotState(p, canvas(w), w, 'after'), 'inert')
assert.equal(A.moveBlock(p, w, ie, 'then'), p)

const wNode = A.locate(p, w).node
assert.equal(A.controlDepth(wNode), 2)
assert.equal(A.controlDepth(A.locate(p, s1).node), 0)

let q = A.insertBlock(p, null, 'end', A.createBlock('while'))
const w2 = q[q.length - 1].id
q = A.insertBlock(q, w2, 'body', A.createBlock('while'))
const w3 = A.locate(q, w2).node.body[0].id
assert.equal(A.slotState(q, canvas(w), w2, 'body'), 'ok')
assert.equal(A.slotState(q, canvas(w), w3, 'body'), 'deny')
assert.equal(A.slotState(q, canvas(w), w3, 'before'), 'ok')

q = A.insertBlock(q, w3, 'body', A.createBlock('if'))
const i4 = A.locate(q, w3).node.body[0].id
assert.equal(A.slotState(q, palette('while'), i4, 'then'), 'deny')
assert.equal(A.slotState(q, palette('ifelse'), i4, 'then'), 'deny')
assert.equal(A.slotState(q, palette('step'), i4, 'then'), 'ok')
assert.equal(A.slotState(q, palette('if'), i4, 'after'), 'ok')

const printId = p[p.length - 1].id
const moved = A.moveBlock(p, printId, ie, 'else')
assert.equal(A.locate(moved, printId).node.id, printId)
assert.equal(A.locate(moved, printId).ancestors, 2)
assert.equal(moved.length, p.length - 1)
assert.notEqual(moved, p)
assert.equal(A.locate(p, printId).ancestors, 0)
const movedW = A.moveBlock(p, w, p[0].id, 'before')
assert.equal(movedW[0].id, w)
assert.equal(A.locate(movedW, s1).node.id, s1)

const loc4 = A.locate(p, s1)
const mineId = loc4.list[1].id
assert.equal(A.slotState(p, canvas(mineId), s1, 'after'), 'inert')
assert.equal(A.slotState(p, canvas(printId), w, 'after'), 'inert')
assert.equal(A.slotState(p, canvas(printId), null, 'end'), 'inert')
assert.equal(A.slotState(p, canvas(w), null, 'end'), 'ok')
assert.equal(A.slotState(p, canvas(mineId), s1, 'before'), 'ok')

const setNode = A.locate(p, A.locate(p, ie).list[0].id).node
assert.equal(setNode.type, 'set')
assert.equal(A.controlDepth(setNode), 0)
assert.equal(A.slotState(q, palette('set'), i4, 'then'), 'ok')
assert.equal(A.slotState(q, canvas(A.locate(q, setNode.id).node.id), i4, 'then'), 'ok')

assert.deepEqual(A.clickTarget(p, null), { targetId: null, where: 'end' })
assert.deepEqual(A.clickTarget(p, w), { targetId: w, where: 'body' })
assert.deepEqual(A.clickTarget(p, ie), { targetId: ie, where: 'then' })
assert.deepEqual(A.clickTarget(p, s1), { targetId: s1, where: 'after' })
assert.deepEqual(A.clickTarget(p, 'nincs-ilyen'), { targetId: null, where: 'end' })

console.log('OK – minden teszt átment')