import { useSim } from '../sim/SimContext.jsx'
import { SENSOR } from '../sim/messages.js'

const ROBOT_ROTATION = { '>': 0, v: 90, '<': 180, '^': 270 }
const DIR_NAME = { '>': 'kelet', v: 'dél', '<': 'nyugat', '^': 'észak' }

const TILE_CLS = {
  '.': 'bg-stone-50 border-stone-300',
  '#': 'bg-slate-700 border-slate-800',
  '@': 'bg-amber-400 border-amber-500',
}
const TILE_NAME = { '.': 'Üres kamra', '#': 'Fal', '@': 'Aranyrög' }

const FOG = 'pointer-events-none absolute inset-0 rounded-sm bg-white/60 bg-[repeating-linear-gradient(45deg,transparent_0_3px,rgba(100,116,139,0.35)_3px_5px)]'

function Cell({ tile, discovered, robot, onGold }) {
  if (robot) {
    return (
      <div className={`relative flex aspect-square items-center justify-center rounded-sm border-2 border-blue-700 ${onGold ? 'bg-amber-300' : 'bg-blue-100'}`}
        title={`Robot (${DIR_NAME[robot]} felé néz)${onGold ? ' – aranyon áll' : ''}`}>
        <span className='text-[min(2.2vw,1.6rem)] leading-none font-black text-blue-700'
          style={{ transform: `rotate(${ROBOT_ROTATION[robot]}deg)` }}>➤</span>
      </div>
    )
  }
  return (
    <div className={`relative flex aspect-square items-center justify-center rounded-sm border ${TILE_CLS[tile] ?? 'bg-white'}`}
      title={`${TILE_NAME[tile] ?? ''}${discovered ? '' : ' – még felfedezetlen'}`}>
      {tile === '@' && <span className='h-1/3 w-1/3 rotate-45 rounded-sm bg-yellow-100 shadow' />}
      {!discovered && <span className={FOG} />}
    </div>
  )
}

function Legend() {
  const item = (cls, text, fog = false) => (
    <span className='flex items-center gap-1'>
      <span className={`relative inline-block h-3.5 w-3.5 rounded-sm border ${cls}`}>{fog && <span className={FOG} />}</span>
      {text}
    </span>
  )
  return (
    <div className='flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500'>
      {item(TILE_CLS['.'], 'üres')}
      {item(TILE_CLS['#'], 'fal')}
      {item(TILE_CLS['@'], 'arany')}
      {item('bg-blue-100 border-blue-700', 'robot')}
      {item(TILE_CLS['#'], 'halvány, csíkos = még felfedezetlen', true)}
    </div>
  )
}

function ManualControls() {
  const { manualAction } = useSim()
  const btn = 'flex flex-col items-center rounded border border-gray-300 bg-white px-3 py-1.5 text-sm font-semibold hover:bg-blue-50 active:bg-blue-100'
  return (
    <div className='flex flex-col gap-1.5'>
      <h2 className='text-xs font-bold uppercase text-gray-400'>Kézi vezérlés</h2>
      <div className='flex flex-wrap gap-2'>
        <button className={btn} onClick={() => manualAction('turn')} title='turn by 1 – billentyű: ←'>
          ↺ Fordulás balra <kbd className='text-[10px] font-normal text-gray-400'>←</kbd>
        </button>
        <button className={btn} onClick={() => manualAction('step')} title='step forward 1 – billentyű: ↑'>
          ↑ Előre 1 <kbd className='text-[10px] font-normal text-gray-400'>↑</kbd>
        </button>
        <button className={btn} onClick={() => manualAction('mine')} title='mine here – billentyű: M'>
          ⛏ Bányászás <kbd className='text-[10px] font-normal text-gray-400'>M</kbd>
        </button>
      </div>
      <p className='text-xs text-gray-500'>A kézi vezérlés megszakítja a futó programot, és nem kerül a naplóba.</p>
    </div>
  )
}

const Simulator = () => {
  const { world } = useSim()
  if (!world) {
    return <div className='rounded border border-gray-400 bg-white p-4 text-gray-400'>Szimulátor betöltése…</div>
  }
  const { map, robot, sensor, gold } = world
  const sensorInfo = SENSOR[sensor.type]

  return (
    <div className='flex min-w-0 flex-col gap-3 rounded border border-gray-400 bg-white p-4'>
      <h1 className='text-xl font-bold uppercase text-gray-400'>Szimulátor</h1>

      <div className='mx-auto w-full' style={{ maxWidth: `${map.width * 2.6}rem` }}>
        <div className='grid gap-0.5' style={{ gridTemplateColumns: `repeat(${map.width}, minmax(0, 1fr))` }}>
          {map.tiles.flatMap((row, y) => [...row].map((tile, x) => {
            const isRobot = robot.x === x && robot.y === y
            return (
              <Cell key={`${x}-${y}`} tile={tile} discovered={map.discovered[y][x]}
                robot={isRobot ? robot.direction : null} onGold={isRobot && robot.on_gold} />
            )
          }))}
        </div>
      </div>
      <Legend />

      <div className='grid grid-cols-2 gap-3'>
        <div className='flex items-center gap-3 rounded border border-gray-200 p-2' title='Mi van közvetlenül a robot előtt (ezt adná vissza most az isThere)'>
          <span className={`h-8 w-8 shrink-0 rounded border-2 ${sensorInfo.cls}`} />
          <div>
            <div className='text-xs font-bold uppercase text-gray-400'>Szenzor – a robot előtt</div>
            <div className='font-semibold'>{sensorInfo.label}</div>
          </div>
        </div>
        <div className='flex items-center gap-3 rounded border border-gray-200 p-2'>
          <span className='flex h-8 w-8 shrink-0 items-center justify-center rounded border-2 border-amber-500 bg-amber-400'>
            <span className='h-3 w-3 rotate-45 rounded-sm bg-yellow-100' />
          </span>
          <div>
            <div className='text-xs font-bold uppercase text-gray-400'>Kibányászott arany</div>
            <div className='font-semibold'>{gold.collected} db <span className='text-sm font-normal text-gray-500'>/ {gold.total} összesen</span></div>
          </div>
        </div>
      </div>

      <ManualControls />
    </div>
  )
}

export default Simulator
