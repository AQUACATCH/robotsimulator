export const ERROR_TEXT = {
  E_TYPE_MISMATCH: 'Típust váltó értékadás',
  E_UNINITIALIZED: 'Nem inicializált változó olvasása',
  E_NON_BOOL_CONDITION: 'A feltétel nem logikai érték',
  E_BAD_OPERAND: 'Rossz operandustípus',
  E_BEDROCK_HIT: 'A robot falba ütközött vagy lelépett volna a térképről',
  E_NO_GOLD: 'Bányászás arany nélkül',
  E_BAD_ARG: 'Érvénytelen paraméter',
  INSTRUCTION_COUNT_LIMIT_EXCEEDED: 'Túllépte az 1000 utasításos limitet, a futás leállt',
}

export const MANUAL_TEXT = {
  E_BEDROCK_HIT: 'Fal van előtted – a robot a helyén maradt.',
  E_NO_GOLD: 'Ezen a mezőn nincs arany.',
}

export const SENSOR = {
  empty: { label: 'Üres kamra', cls: 'bg-stone-100 border-stone-300' },
  wall: { label: 'Fal', cls: 'bg-slate-700 border-slate-800' },
  gold: { label: 'Aranyrög', cls: 'bg-amber-400 border-amber-500' },
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
