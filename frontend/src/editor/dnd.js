export const MIME = 'application/x-minescript'

let current = null

export function beginDrag(e, payload, setDrag, effect) {
  e.dataTransfer.setData(MIME, JSON.stringify(payload))
  e.dataTransfer.effectAllowed = effect
  current = payload
  setTimeout(() => { if (current === payload) setDrag(payload) }, 0)
}

export function readDrag(e) {
  try {
    return JSON.parse(e.dataTransfer.getData(MIME))
  } catch {
    return current
  }
}

export function endDrag(setDrag) {
  current = null
  setDrag(null)
}

export function isOurs(e) {
  return [...e.dataTransfer.types].includes(MIME)
}