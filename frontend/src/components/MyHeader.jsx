import { useEditor } from '../editor/EditorContext.jsx'
import { useSim } from '../sim/SimContext.jsx'
import { statusText } from '../sim/messages.js'

function Btn({ onClick, disabled, title, cls = 'border border-gray-300 bg-white hover:bg-gray-50', children }) {
  return (
    <button onClick={onClick} disabled={disabled} title={title}
      className={`rounded px-3 py-1.5 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40 ${cls}`}>
      {children}
    </button>
  )
}

const MyHeader = () => {
  const { apiError } = useEditor()
  const sim = useSim()
  const ex = sim.world?.execution

  return (
    <div className='flex flex-wrap items-center justify-between gap-3 bg-white px-4 py-3 shadow-md'>
      <h1 className='text-2xl font-bold text-blue-800'>
        Robot<span className='text-yellow-500'>szimulátor</span>
      </h1>

      <div className='flex flex-wrap items-center gap-2'>
        <Btn cls='bg-green-600 text-white hover:bg-green-700' onClick={() => sim.start('run')}
          title='A program futtatása nyomkövetés nélkül, lassítva. A térkép és a robot előtte alaphelyzetbe kerül.'>
          ▶ Futtatás
        </Btn>
        <Btn cls='bg-indigo-600 text-white hover:bg-indigo-700' onClick={() => sim.start('debug')}
          title='Nyomkövetés: a programot soronként, a Lépés gombbal hajthatod végre, közben látod a változókat.'>
          ⏯ Nyomkövetés
        </Btn>
        <Btn onClick={sim.step} disabled={!sim.debugging || sim.autoplay}
          title='Nyomkövetésben a következő programsor végrehajtása.'>
          ⤵ Lépés
        </Btn>
        <Btn onClick={sim.resume} disabled={!sim.debugging || sim.autoplay}
          title='Nyomkövetésből tovább futtatja a programot automatikusan.'>
          ⏩ Folytatás
        </Btn>
        <Btn onClick={sim.stop} disabled={!sim.running}
          title='A futó program leállítása.'>
          ■ Leállítás
        </Btn>
        <Btn onClick={sim.reset}
          title='A térkép és a robot visszaállítása a kezdőállapotba.'>
          ⟲ Alaphelyzet
        </Btn>

        <label className='flex items-center gap-2 text-xs text-gray-600'
          title='Mennyit várjon két programsor között a futtatás (0 = a lehető leggyorsabban).'>
          Sebesség
          <input type='range' min={0} max={1000} step={50} value={1000 - sim.speed}
            onChange={(e) => sim.changeSpeed(1000 - Number(e.target.value))} />
          <span className='w-14 tabular-nums'>{sim.speed} ms</span>
        </label>

        <Btn onClick={sim.openLog} title='A naplófájl aktuális tartalmának megjelenítése.'>
          📄 Napló megnyitása
        </Btn>
      </div>

      <div className='flex w-full flex-wrap items-center gap-3 text-sm'>
        <span className='rounded bg-gray-100 px-2 py-0.5 text-gray-700'>
          Állapot: <b>{statusText(ex)}</b>
          {ex && ex.instruction_count > 0 && <span className='text-gray-500'> · {ex.instruction_count} végrehajtott sor</span>}
        </span>
        {apiError && <span className='text-red-600'>Backend hiba: {apiError}</span>}
      </div>
    </div>
  )
}

export default MyHeader
