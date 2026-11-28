export const ERROR_TEXT = {
  E_TYPE_MISMATCH: 'Típust váltó értékadás',
  E_UNINITIALIZED: 'Nem inicializált változó olvasása',
  E_NON_BOOL_CONDITION: 'A feltétel nem logikai érték',
  E_BAD_OPERAND: 'Rossz operandustípus',
  E_BEDROCK_HIT: 'A robot kőzetbe ütközött vagy lelépett volna a térképről',
  E_NO_GOLD: 'Bányászás arany nélkül',
  E_BAD_ARG: 'Érvénytelen paraméter (az isThere 3–5 csak a Beállításokban engedélyezve használható)',
  E_NOT_DRILLABLE: 'A robot előtt nincs átfúrható kőzet',
  E_OUT_OF_ENERGY: 'Elfogyott a robot energiája',
  E_CANNOT_CHARGE: 'Tölteni csak a töltőállomáson lehet',
  E_MINE_COLLAPSE: 'A bánya beomlott, a robot megsemmisült',
  E_CANNOT_PLACE: 'A töltőállomásra nem tehető támasz',
  E_NOT_LIST: 'A változó nem lista',
  E_OUT_OF_BOUNDS: 'A listaindex kívül esik a listán',
  E_LIST_OVERFLOW: 'A lista elérte a 100 elemes korlátot',
  SYNTAX_ERROR: 'Szintaktikai hiba',
  INSTRUCTION_COUNT_LIMIT_EXCEEDED: 'Túllépte az 1000 utasításos limitet, a futás leállt',
}

export const MANUAL_TEXT = {
  E_BEDROCK_HIT: 'Kőzet van előtted – a robot a helyén maradt.',
  E_NO_GOLD: 'Ezen a mezőn nincs arany.',
  E_NOT_DRILLABLE: 'Előtted nincs átfúrható kőzet.',
  E_OUT_OF_ENERGY: 'Elfogyott az energia. Töltsd fel a töltőállomáson, vagy állítsd alaphelyzetbe a bányát.',
  E_CANNOT_CHARGE: 'Tölteni csak a töltőállomáson lehet.',
  E_CANNOT_PLACE: 'A töltőállomásra nem tehetsz támaszt.',
  E_MINE_COLLAPSE: 'A bánya beomlott, a robot megsemmisült. Az Alaphelyzet gombbal állíthatod vissza.',
}

export const TILE = {
  '.': { name: 'Üres kamra', cls: 'bg-stone-50 border-stone-300' },
  '#': { name: 'Nem átfúrható kőzet (fal)', cls: 'bg-slate-700 border-slate-800' },
  '@': { name: 'Aranyat tartalmazó kőzet', cls: 'bg-amber-400 border-amber-500' },
  '+': { name: 'Átfúrható kőzet', cls: 'bg-stone-400 border-stone-500' },
  T: { name: 'Támasz', cls: 'bg-stone-50 border-stone-300' },
  '~': { name: 'Töltőállomás', cls: 'bg-emerald-100 border-emerald-400' },
}

export const SENSOR_TILE = {
  empty: '.', wall: '#', gold: '@', drillable: '+', support: 'T', station: '~',
}

export const COST_FIELDS = [
  ['drill_usage', 'drill forward'], ['step_usage', 'step forward'], ['turn_usage', 'turn by'],
  ['mine_usage', 'mine here'], ['place_usage', 'place here'], ['isThere_usage', 'isThere'],
  ['safeToDrill_usage', 'safeToDrill'], ['print_usage', 'print'],
]

export function formatValue(value) {
  if (Array.isArray(value)) return `[${value.map(formatValue).join(',')}]`
  return String(value)
}

export function typeName(value) {
  if (Array.isArray(value)) return `lista (${value.length} elem)`
  return typeof value === 'boolean' ? 'logikai' : 'egész'
}

export function statusText(execution) {
  if (!execution) return ''
  const line = execution.last_step?.line
  switch (execution.status) {
    case 'running':
      return execution.mode === 'debug'
        ? (line ? `Nyomkövetés – utoljára a(z) ${line}. sor futott` : 'Nyomkövetés – nyomd meg a Lépés gombot')
        : 'Fut…'
    case 'finished': return 'A program befejeződött (EOR)'
    case 'error': return 'A program hibával leállt'
    case 'limit_exceeded': return 'Utasításlimit túllépve'
    case 'stopped': return 'Leállítva'
    default: return 'Kész a futtatásra'
  }
}
