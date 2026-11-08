import { useEffect, useState } from 'react'
import MyHeader from './components/MyHeader'
import Toolbar from './components/Toolbar'
import Scratchbox from './components/Scratchbox'
import CodeShowcase from './components/CodeShowcase'
import Simulator from './components/Simulator'
import { getState, putProgram } from './api/api.js'
import {
  childLists, clickTarget, containsId, createBlock, emptyFieldIds, insertBlock, locate,
  moveBlock, removeBlock, slotState, updateBlock,
} from './editor/ast.js'
import { endDrag } from './editor/dnd.js'
import { EditorContext } from './editor/EditorContext.jsx'
import useSimulator from './sim/useSimulator.js'
import { SimContext } from './sim/SimContext.jsx'
import { ConsolePanel, LogDialog, NoticeBar, VariablesPanel } from './components/RunPanels.jsx'

function App() {
  const [program, setProgram] = useState([])
  const [loaded, setLoaded] = useState(false)
  const [drag, setDrag] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [focusId, setFocusId] = useState(null)
  const [source, setSource] = useState('')
  const [lineMap, setLineMap] = useState({})
  const [highlight, setHighlight] = useState({ line: null, nodeId: null })
  const [showEmpty, setShowEmpty] = useState(false)
  const [apiError, setApiError] = useState(null)
  const [loadedAst, setLoadedAst] = useState(null)

  const sim = useSimulator({
    beforeRun: async () => {
      if (!checkEmpty()) return false
      await saveNow()
      return true
    },
    onLine: (line, nodeId) => {
      const id = nodeId ?? lineMap[line] ?? null
      setHighlight({ line, nodeId: id })
      requestAnimationFrame(() => {
        if (id) document.querySelector(`[data-node-id="${id}"]`)?.scrollIntoView({ block: 'nearest' })
        document.querySelector(`[data-code-line="${line}"]`)?.scrollIntoView({ block: 'nearest' })
      })
    },
    onClearLine: () => setHighlight({ line: null, nodeId: null }),
  })
  const applySim = sim.apply

  useEffect(() => {
    let ignore = false
    getState()
      .then((s) => {
        if (ignore) return
        setLoadedAst(s.ast)
        setProgram(s.ast)
        setSource(s.source)
        setLineMap(s.lineMap)
        setLoaded(true)
        applySim(s)
      })
      .catch((e) => setApiError(String(e)))
    return () => { ignore = true }
  }, [applySim])

  useEffect(() => {
    if (!loaded || program === loadedAst) return
    let cancelled = false
    const timer = setTimeout(() => {
      putProgram(program)
        .then((r) => {
          if (cancelled) return
          setSource(r.source)
          setLineMap(r.lineMap)
          setApiError(null)
          applySim(r)
        })
        .catch((e) => { if (!cancelled) setApiError(String(e)) })
    }, 200)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [program, loaded, loadedAst, applySim])

  function select(id) {
    setSelectedId(id)
  }

  function clearFocus() {
    setFocusId(null)
  }

  function update(id, mutate) {
    setProgram((p) => updateBlock(p, id, mutate))
  }

  function insertNew(kind, targetId, where) {
    const block = createBlock(kind)
    setProgram((p) => insertBlock(p, targetId, where, block))
    setSelectedId(block.id)
    if (kind !== 'mine') setFocusId(block.id)
  }

  function drop(payload, targetId, where) {
    endDrag(setDrag)
    if (!payload || slotState(program, payload, targetId, where) !== 'ok') return
    if (payload.src === 'palette') {
      insertNew(payload.kind, targetId, where)
    } else {
      setProgram((p) => moveBlock(p, payload.id, targetId, where))
      setSelectedId(payload.id)
      setFocusId(null)
    }
  }

  function canClickInsert(kind) {
    const { targetId, where } = clickTarget(program, selectedId)
    return slotState(program, { src: 'palette', kind }, targetId, where) === 'ok'
  }

  function insertAtCursor(kind) {
    if (!canClickInsert(kind)) return
    const { targetId, where } = clickTarget(program, selectedId)
    insertNew(kind, targetId, where)
  }

  function deleteBlock(id) {
    const node = locate(program, id)?.node
    if (!node) return
    const hasChildren = childLists(node).some(([, list]) => list.length > 0)
    if (hasChildren && !window.confirm('A blokk a tartalmával együtt törlődik. Biztosan törlöd?')) return
    setProgram((p) => removeBlock(p, id))
    if (selectedId && containsId(node, selectedId)) setSelectedId(null)
  }

  async function saveNow() {
    if (!loaded) throw new Error('A program még nincs betöltve a backendről.')
    const r = await putProgram(program)
    setSource(r.source)
    setLineMap(r.lineMap)
    setApiError(null)
    sim.apply(r)
  }

  function checkEmpty() {
    const ids = emptyFieldIds(program)
    setShowEmpty(ids.length > 0)
    return ids.length === 0
  }

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') setSelectedId(null)
      const tag = e.target.tagName
      const typing = tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA'
      if (e.key === 'Delete' && selectedId && !typing) deleteBlock(selectedId)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const emptyIds = new Set(showEmpty ? emptyFieldIds(program) : [])

  const editor = {
    program, drag, setDrag, drop,
    selectedId, select, focusId, clearFocus, update, deleteBlock,
    canClickInsert, insertAtCursor, saveNow,
    source, lineMap, highlight, showEmpty, emptyIds, checkEmpty, apiError,
  }

  return (
    <EditorContext value={editor}>
      <SimContext value={sim}>
        <div className='flex min-h-screen flex-col bg-gray-200 xl:h-screen'>
          <MyHeader />
          <NoticeBar />
          <div className='grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-2 xl:grid-cols-[minmax(150px,0.6fr)_minmax(300px,1.5fr)_minmax(200px,0.9fr)_minmax(380px,1.6fr)]'>
            <div className='flex min-h-0 min-w-0 flex-col xl:h-full max-xl:h-[32rem]'><Toolbar /></div>
            <div className='flex min-h-0 min-w-0 flex-col xl:h-full max-xl:h-[32rem]'><Scratchbox /></div>
            <div className='flex min-h-0 min-w-0 flex-col xl:h-full max-xl:h-[32rem]'><CodeShowcase /></div>
            <div className='flex min-h-0 min-w-0 flex-col gap-4 xl:overflow-auto'>
              <Simulator />
              <div className='grid grid-cols-2 gap-4'>
                <ConsolePanel />
                <VariablesPanel />
              </div>
            </div>
          </div>
          <LogDialog />
        </div>
      </SimContext>
    </EditorContext>
  )
}

export default App