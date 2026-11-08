export const KEYWORDS = new Set([
  'and', 'by', 'else', 'false', 'forward', 'here', 'if', 'isthere', 'mine',
  'not', 'or', 'print', 'set', 'step', 'to', 'true', 'turn', 'while',
])

const IDENT_RE = /^[A-Za-z][A-Za-z0-9]*$/
const NUMBER_RE = /^[0-9]+$/

export const MAX_CONTROL_DEPTH = 3

export function identError(s) {
  if (s === '') return null
  if (!IDENT_RE.test(s)) return 'Betűvel kell kezdődnie, és csak betűt és számjegyet tartalmazhat.'
  if (KEYWORDS.has(s.toLowerCase())) return `A(z) „${s}” kulcsszó, nem lehet változónév.`
  return null
}

export function simplevalError(s) {
  if (s === '') return null
  if (s === 'true' || s === 'false') return null
  if (NUMBER_RE.test(s)) {
    return Number(s) <= 100 ? null : 'A szám 0 és 100 között lehet.'
  }
  return identError(s)
}

let counter = 0
export function newId() {
  counter += 1
  return `c${Date.now().toString(36)}${counter}`
}

export const CONTROL_TYPES = new Set(['if', 'ifelse', 'while'])

export function createBlock(kind) {
  const id = newId()
  switch (kind) {
    case 'step': return { id, type: 'step', arg: '' }
    case 'turn': return { id, type: 'turn', arg: '' }
    case 'mine': return { id, type: 'mine' }
    case 'print': return { id, type: 'print', arg: '' }
    case 'set': return { id, type: 'set', ident: '', value: { kind: 'simple', a: '' } }
    case 'if': return { id, type: 'if', cond: '', then: [], else: null }
    case 'ifelse': return { id, type: 'if', cond: '', then: [], else: [] }
    case 'while': return { id, type: 'while', cond: '', body: [] }
    default: throw new Error(`Ismeretlen blokk: ${kind}`)
  }
}

export function isControl(node) {
  return node.type === 'if' || node.type === 'while'
}

export function childLists(node) {
  if (node.type === 'while') return [['body', node.body]]
  if (node.type === 'if') {
    return node.else ? [['then', node.then], ['else', node.else]] : [['then', node.then]]
  }
  return []
}

export function locate(program, id, ancestors = 0) {
  for (let i = 0; i < program.length; i++) {
    const node = program[i]
    if (node.id === id) return { node, list: program, index: i, ancestors }
    for (const [, list] of childLists(node)) {
      const found = locate(list, id, ancestors + 1)
      if (found) return found
    }
  }
  return null
}

export function ancestorsAt(program, targetId, where) {
  if (!targetId || where === 'end') return 0
  const loc = locate(program, targetId)
  if (!loc) return 0
  return where === 'before' || where === 'after' ? loc.ancestors : loc.ancestors + 1
}

export function canInsertControl(program, targetId, where) {
  return ancestorsAt(program, targetId, where) + 1 <= MAX_CONTROL_DEPTH
}

export function insertPositions(node) {
  if (!node) return ['end']
  const pos = ['before', 'after']
  if (node.type === 'while') pos.push('body')
  if (node.type === 'if') pos.push('then')
  if (node.type === 'if' && node.else) pos.push('else')
  return pos
}

const clone = (program) => structuredClone(program)

export function insertBlock(program, targetId, where, block) {
  const next = clone(program)
  if (!targetId || where === 'end') {
    next.push(block)
    return next
  }
  const loc = locate(next, targetId)
  if (!loc) return program
  if (where === 'before') loc.list.splice(loc.index, 0, block)
  else if (where === 'after') loc.list.splice(loc.index + 1, 0, block)
  else if (where === 'body') loc.node.body.push(block)
  else if (where === 'then') loc.node.then.push(block)
  else if (where === 'else' && loc.node.else) loc.node.else.push(block)
  return next
}

export function removeBlock(program, id) {
  const next = clone(program)
  const loc = locate(next, id)
  if (!loc) return program
  loc.list.splice(loc.index, 1)
  return next
}

export function updateBlock(program, id, mutate) {
  const next = clone(program)
  const loc = locate(next, id)
  if (!loc) return program
  mutate(loc.node)
  return next
}

export function emptyFieldIds(program) {
  const ids = []
  const walk = (list) => {
    for (const n of list) {
      const fields = []
      if ('arg' in n) fields.push(n.arg)
      if ('cond' in n) fields.push(n.cond)
      if (n.type === 'set') {
        fields.push(n.ident, n.value.a)
        if (n.value.kind === 'binop') fields.push(n.value.b)
      }
      if (fields.some((f) => f === '')) ids.push(n.id)
      for (const [, l] of childLists(n)) walk(l)
    }
  }
  walk(program)
  return ids
}

export function controlDepth(node) {
  if (!isControl(node)) return 0
  let deepest = 0
  for (const [, list] of childLists(node)) {
    for (const child of list) deepest = Math.max(deepest, controlDepth(child))
  }
  return 1 + deepest
}

export function containsId(node, id) {
  if (node.id === id) return true
  return childLists(node).some(([, list]) => list.some((child) => containsId(child, id)))
}

function isSamePlace(program, loc, targetId, where) {
  const prev = loc.list[loc.index - 1]
  if (where === 'after' && prev && prev.id === targetId) return true
  return where === 'end' && loc.list === program && loc.index === program.length - 1
}

export function slotState(program, drag, targetId, where) {
  if (!drag) return 'idle'
  let depth
  if (drag.src === 'palette') {
    depth = CONTROL_TYPES.has(drag.kind) ? 1 : 0
  } else {
    const loc = locate(program, drag.id)
    if (!loc) return 'inert'
    if (targetId && containsId(loc.node, targetId)) return 'inert'
    if (isSamePlace(program, loc, targetId, where)) return 'inert'
    depth = controlDepth(loc.node)
  }
  return ancestorsAt(program, targetId, where) + depth <= MAX_CONTROL_DEPTH ? 'ok' : 'deny'
}

export function moveBlock(program, id, targetId, where) {
  const loc = locate(program, id)
  if (!loc) return program
  if (targetId && containsId(loc.node, targetId)) return program
  const block = structuredClone(loc.node)
  return insertBlock(removeBlock(program, id), targetId, where, block)
}

export function clickTarget(program, selectedId) {
  const loc = selectedId ? locate(program, selectedId) : null
  if (!loc) return { targetId: null, where: 'end' }
  if (loc.node.type === 'while') return { targetId: selectedId, where: 'body' }
  if (loc.node.type === 'if') return { targetId: selectedId, where: 'then' }
  return { targetId: selectedId, where: 'after' }
}