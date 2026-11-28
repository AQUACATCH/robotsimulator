import { useSim } from '../sim/SimContext.jsx'
import { COST_FIELDS, SENSOR_TILE, TILE } from '../sim/messages.js'

const ROBOT_ROTATION = { '>': 0, v: 90, '<': 180, '^': 270 }
const DIR_NAME = { '>': 'kelet', v: 'dél', '<': 'nyugat', '^': 'észak' }
const ROBOT_BG = { '~': 'bg-emerald-200', T: 'bg-amber-100', '@': 'bg-amber-300' }
const STANDS_ON = { '~': ' – töltőállomáson áll', T: ' – támaszon áll', '@': ' – aranyat tartalmazó kőzeten áll' }

const FOG = 'pointer-events-none absolute inset-0 rounded-sm bg-white/60 bg-[repeating-linear-gradient(45deg,transparent_0_3px,rgba(100,116,139,0.35)_3px_5px)]'
const RUBBLE = 'pointer-events-none absolute inset-0 rounded-sm bg-[repeating-linear-gradient(-45deg,rgba(185,28,28,0.5)_0_3px,transparent_3px_6px)]'
const ROCK_GRAIN = 'absolute inset-0 rounded-sm bg-[radial-gradient(circle,rgba(41,37,36,0.45)_1px,transparent_1.5px)] bg-[length:6px_6px]'
const CELL = 'relative aspect-square min-h-0 min-w-0 overflow-hidden rounded-sm'

// Minden jel a mező közepén, a mező méretéhez arányosan: soha nem nyújtja meg a mezőt.
function Icon({ size = 70, rotate = 0, className = '', children }) {
  return (
    <span className='pointer-events-none absolute inset-0 flex items-center justify-center'>
      <svg viewBox='0 0 24 24' aria-hidden='true' className={className}
        style={{ width: `${size}%`, height: `${size}%`, transform: rotate ? `rotate(${rotate}deg)` : undefined }}>
        {children}
      </svg>
    </span>
  )
}

const ARROW = <path d='M3 3.5 21 12 3 20.5 7.5 12Z' fill='currentColor' />
const CROSS = <path d='M5 5 19 19M19 5 5 19' stroke='currentColor' strokeWidth='3.5' strokeLinecap='round' fill='none' />

function TileFace({ tile }) {
  if (tile === '@') {
    return <Icon size={40}><path d='M12 3 21 12 12 21 3 12Z' fill='#fef9c3' stroke='#d97706' strokeWidth='1' /></Icon>
  }
  if (tile === '+') return <span className={ROCK_GRAIN} />
  if (tile === 'T') {
    return <Icon className='text-amber-800'><path d='M3 4h18v4H3ZM5.5 8h4v13h-4ZM14.5 8h4v13h-4Z' fill='currentColor' /></Icon>
  }
  if (tile === '~') {
    return <Icon className='text-emerald-600'><path d='M13.5 2 4 14h6.5L9 22l11-13h-6.5Z' fill='currentColor' /></Icon>
  }
  return null
}

function Cell({ tile, discovered, robot, rubble }) {
  if (robot) {
    const { direction, destroyed } = robot
    return (
      <div className={`${CELL} border-2 ${destroyed ? 'border-red-700 bg-red-200' : `border-blue-700 ${ROBOT_BG[tile] ?? 'bg-blue-100'}`}`}
        title={destroyed ? 'A robot megsemmisült' : `Robot (${DIR_NAME[direction]} felé néz)${STANDS_ON[tile] ?? ''}`}>
        {destroyed
          ? <Icon size={65} className='text-red-700'>{CROSS}</Icon>
          : <Icon size={72} rotate={ROBOT_ROTATION[direction]} className='text-blue-700'>{ARROW}</Icon>}
      </div>
    )
  }
  return (
    <div className={`${CELL} border ${TILE[tile]?.cls ?? 'bg-white'}`}
      title={`${TILE[tile]?.name ?? ''}${discovered ? '' : ' – még felfedezetlen'}${rubble ? ' – beomlott' : ''}`}>
      <TileFace tile={tile} />
      {!discovered && <span className={FOG} />}
      {rubble && <span className={RUBBLE} />}
    </div>
  )
}

function Swatch({ tile, className = 'h-3.5 w-3.5', children }) {
  return (
    <span className={`relative inline-block shrink-0 overflow-hidden rounded-sm border ${TILE[tile]?.cls ?? ''} ${className}`}>
      {children ?? <TileFace tile={tile} />}
    </span>
  )
}

function Legend({ collapsed }) {
  const item = (swatch, text) => (
    <span className='flex items-center gap-1'>{swatch}{text}</span>
  )
  return (
    <div className='flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500'>
      {item(<Swatch tile='.' />, 'üres kamra')}
      {item(<Swatch tile='#' />, 'nem átfúrható kőzet (fal)')}
      {item(<Swatch tile='@' />, 'aranyat tartalmazó kőzet')}
      {item(<Swatch tile='+' />, 'átfúrható kőzet')}
      {item(<Swatch tile='T' />, 'támasz')}
      {item(<Swatch tile='~' />, 'töltőállomás')}
      {item(<span className='relative inline-block h-3.5 w-3.5 rounded-sm border border-blue-700 bg-blue-100'><Icon size={80} className='text-blue-700'>{ARROW}</Icon></span>, 'robot')}
      {item(<Swatch tile='#'><span className={FOG} /></Swatch>, 'halvány, csíkos = még felfedezetlen')}
      {collapsed && item(<span className='relative inline-block h-3.5 w-3.5 rounded-sm border border-red-700'><span className={RUBBLE} /></span>, 'beomlott terület')}
    </div>
  )
}

function SensorPanel({ sensor }) {
  const tile = SENSOR_TILE[sensor.type] ?? '#'
  return (
    <div className='flex items-center gap-3 rounded border border-gray-200 p-2'
      title='Mi van közvetlenül a robot előtt. A kijelzés nem fogyaszt energiát, és nem tesz felfedezetté mezőt.'>
      <Swatch tile={tile} className='h-8 w-8 border-2'>
        <TileFace tile={tile} />
      </Swatch>
      <div>
        <div className='text-xs font-bold uppercase text-gray-400'>Szenzor – a robot előtt</div>
        <div className='font-semibold'>{TILE[tile].name}</div>
        {sensor.type === 'drillable' && (sensor.safe_to_drill
          ? <div className='text-xs font-semibold text-green-700'>✔ Biztonságos fúrni</div>
          : <div className='text-xs font-semibold text-red-700'>⚠ A fúrás után beomlana a bánya</div>)}
      </div>
    </div>
  )
}

function EnergyPanel({ energy, settings, onStation }) {
  const current = energy.currentenergy
  const max = energy.maxenergy
  const ratio = max > 0 ? current / max : 0
  const bar = ratio <= 0.1 ? 'bg-red-600' : ratio <= 0.3 ? 'bg-amber-500' : 'bg-green-600'
  return (
    <div className='col-span-2 flex flex-col gap-2 rounded border border-gray-200 p-2'>
      <div className='flex items-center justify-between gap-2'>
        <span className='text-xs font-bold uppercase text-gray-400'>Akkumulátor</span>
        <span className='font-semibold tabular-nums'>{current} / {max}</span>
      </div>
      <div className='h-3 overflow-hidden rounded-full bg-gray-200' role='meter' aria-label='Akkumulátor töltöttsége'
        aria-valuemin={0} aria-valuemax={max} aria-valuenow={current}>
        <div className={`h-full ${bar} transition-[width] duration-200`} style={{ width: `${Math.round(ratio * 100)}%` }} />
      </div>
      {current === 0 && (
        <div className='text-xs font-semibold text-red-700'>
          Elfogyott az energia. {onStation ? 'A robot a töltőállomáson áll: tölthet.' : 'Csak a töltőállomáson lehet tölteni.'}
        </div>
      )}
      <div title='Egy utasítás egyszer fogyaszt, a lépések vagy fordulások számától függetlenül. A ⚙ Beállítások gombbal módosítható.'>
        <div className='text-xs font-bold uppercase text-gray-400'>Műveletek energiaigénye</div>
        <div className='mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs sm:grid-cols-3'>
          {COST_FIELDS.map(([key, label]) => (
            <span key={key} className='flex justify-between gap-2'>
              <code>{label}</code><b className='tabular-nums'>{settings?.[key] ?? '–'}</b>
            </span>
          ))}
          <span className='flex justify-between gap-2'><code>charge</code><b>0</b></span>
        </div>
        <div className='mt-1 text-xs text-gray-500'>
          <code>isThere 3–5</code>: <b>{settings?.isThere_extended ? 'engedélyezve' : 'kikapcsolva'}</b>
        </div>
      </div>
    </div>
  )
}

function ManualControls({ disabled, onStation }) {
  const { manualAction } = useSim()
  const btn = 'flex flex-col items-center rounded border border-gray-300 bg-white px-3 py-1.5 text-sm font-semibold hover:bg-blue-50 active:bg-blue-100 disabled:cursor-not-allowed disabled:opacity-40'
  const mining = 'flex flex-col items-center rounded border border-amber-400 bg-amber-50 px-3 py-1.5 text-sm font-semibold hover:bg-amber-100 active:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-40'
  const key = (k) => <kbd className='text-[10px] font-normal text-gray-400'>{k}</kbd>
  return (
    <div className='flex flex-col gap-1.5'>
      <h2 className='text-xs font-bold uppercase text-gray-400'>Kézi vezérlés</h2>
      <div className='flex flex-wrap gap-2'>
        <button className={btn} disabled={disabled} onClick={() => manualAction('turn')} title='turn by 1 – billentyű: ←'>
          ↺ Fordulás balra {key('←')}
        </button>
        <button className={btn} disabled={disabled} onClick={() => manualAction('step')} title='step forward 1 – billentyű: ↑'>
          ↑ Előre 1 {key('↑')}
        </button>
        <button className={btn} disabled={disabled} onClick={() => manualAction('mine')} title='mine here – billentyű: M'>
          ⛏ Bányászás {key('M')}
        </button>
        <button className={mining} disabled={disabled} onClick={() => manualAction('drill')}
          title='drill forward – kifúrja az előtte lévő átfúrható kőzetet, és rálép. Billentyű: D'>
          ⛏ Fúrás {key('D')}
        </button>
        <button className={mining} disabled={disabled} onClick={() => manualAction('place')}
          title='place here – támaszt tesz a robot mezőjére. Billentyű: T'>
          Π Támasz {key('T')}
        </button>
        <button className={mining} disabled={disabled || !onStation} onClick={() => manualAction('charge')}
          title={onStation ? 'charge – teljesen feltölti az akkumulátort. Billentyű: C' : 'Tölteni csak a töltőállomáson lehet.'}>
          ⚡ Töltés {key('C')}
        </button>
      </div>
      <p className='text-xs text-gray-500'>
        {disabled
          ? 'A beomlott bányában nem lehet kézzel irányítani. Az Alaphelyzet gombbal vagy új futtatással állíthatod vissza.'
          : 'A kézi vezérlés megszakítja a futó programot, és nem kerül a naplóba. Ugyanúgy fogyaszt energiát, és ugyanúgy beomolhat a bánya, mint a programból.'}
      </p>
    </div>
  )
}

const Simulator = () => {
  const { world } = useSim()
  if (!world?.loaded) {
    return <div className='rounded border border-gray-400 bg-white p-4 text-gray-400'>Szimulátor betöltése…</div>
  }
  const { map, robot, sensor, gold } = world
  const destroyed = robot.destroyed
  const near = (x, y) => Math.abs(x - robot.x) <= 1 && Math.abs(y - robot.y) <= 1

  return (
    <div className='flex min-w-0 flex-col gap-3 rounded border border-gray-400 bg-white p-4'>
      <h1 className='text-xl font-bold uppercase text-gray-400'>Szimulátor</h1>

      <div className='mx-auto w-full' style={{ maxWidth: `${map.width * 2.6}rem` }}>
        <div className='grid gap-0.5' style={{ gridTemplateColumns: `repeat(${map.width}, minmax(0, 1fr))` }}>
          {map.tiles.flatMap((row, y) => [...row].map((tile, x) => {
            const isRobot = robot.x === x && robot.y === y
            return (
              <Cell key={`${x}-${y}`} tile={tile} discovered={map.discovered[y][x]}
                robot={isRobot ? robot : null} rubble={destroyed && !isRobot && near(x, y)} />
            )
          }))}
        </div>
      </div>
      {destroyed && (
        <div role='alert' className='rounded border-2 border-red-700 bg-red-50 px-3 py-2 text-sm font-semibold text-red-800'>
          A bánya beomlott, a robot megsemmisült. Az Alaphelyzet gombbal vagy új futtatással állíthatod vissza.
        </div>
      )}
      <Legend collapsed={destroyed} />

      <div className='grid grid-cols-2 gap-3'>
        <EnergyPanel energy={world.energy} settings={world.settings} onStation={robot.on_station} />
        <SensorPanel sensor={sensor} />
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

      <ManualControls disabled={destroyed} onStation={robot.on_station} />
    </div>
  )
}

export default Simulator
