export const COMMAND_CLS = 'bg-blue-100 border-blue-400'
export const MINING_CLS = 'bg-amber-100 border-amber-500'
export const LIST_CLS = 'bg-teal-100 border-teal-500'
export const CONTROL_CLS = 'bg-orange-100 border-orange-300'

export const PALETTE = [
  { group: 'command', kind: 'step', label: 'step forward …', cls: COMMAND_CLS },
  { group: 'command', kind: 'turn', label: 'turn by …', cls: COMMAND_CLS },
  { group: 'command', kind: 'mine', label: 'mine here', cls: COMMAND_CLS },
  { group: 'command', kind: 'print', label: 'print …', cls: COMMAND_CLS },
  { group: 'command', kind: 'set', label: 'set … to …', cls: COMMAND_CLS },
  { group: 'mining', kind: 'drill', label: 'drill forward', cls: MINING_CLS },
  { group: 'mining', kind: 'place', label: 'place here', cls: MINING_CLS },
  { group: 'mining', kind: 'charge', label: 'charge', cls: MINING_CLS },
  { group: 'list', kind: 'add', label: 'add … to …', cls: LIST_CLS },
  { group: 'list', kind: 'remove', label: 'remove … @ …', cls: LIST_CLS },
  { group: 'control', kind: 'if', label: 'if …', cls: CONTROL_CLS },
  { group: 'control', kind: 'ifelse', label: 'if … else', cls: CONTROL_CLS },
  { group: 'control', kind: 'while', label: 'while …', cls: CONTROL_CLS },
]

const CLS_BY_TYPE = Object.fromEntries(
  PALETTE.filter((item) => item.group === 'mining' || item.group === 'list').map((item) => [item.kind, item.cls]))

export function commandCls(type) {
  return CLS_BY_TYPE[type] ?? COMMAND_CLS
}

export const GROUPS = [
  { group: 'command', title: 'Parancsblokkok' },
  { group: 'mining', title: 'Bányászblokkok' },
  { group: 'list', title: 'Listablokkok' },
  { group: 'control', title: 'Vezérlőblokkok' },
]
