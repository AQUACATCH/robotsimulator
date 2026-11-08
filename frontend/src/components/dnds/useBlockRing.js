import { useEditor } from '../../editor/EditorContext.jsx'

export default function useBlockRing(id) {
  const { selectedId, highlight, emptyIds, drag } = useEditor()
  const selected = selectedId === id
  let ring = ''
  if (selected) ring = 'ring-2 ring-blue-600'
  if (emptyIds.has(id)) ring = selected ? 'ring-4 ring-red-500' : 'ring-2 ring-red-500'
  if (highlight.nodeId === id) ring = 'ring-4 ring-yellow-400'
  const dragging = drag?.src === 'canvas' && drag.id === id ? 'opacity-40' : ''
  return `${ring} ${dragging}`
}