export const COMMAND_CLS = 'bg-blue-100 border-blue-400'
export const CONTROL_CLS = 'bg-orange-100 border-orange-300'

export const PALETTE = [
  { group: 'command', kind: 'step', label: 'step forward …', cls: COMMAND_CLS },
  { group: 'command', kind: 'turn', label: 'turn by …', cls: COMMAND_CLS },
  { group: 'command', kind: 'mine', label: 'mine here', cls: COMMAND_CLS },
  { group: 'command', kind: 'print', label: 'print …', cls: COMMAND_CLS },
  { group: 'command', kind: 'set', label: 'set … to …', cls: COMMAND_CLS },
  { group: 'control', kind: 'if', label: 'if …', cls: CONTROL_CLS },
  { group: 'control', kind: 'ifelse', label: 'if … else', cls: CONTROL_CLS },
  { group: 'control', kind: 'while', label: 'while …', cls: CONTROL_CLS },
]

export const GROUPS = [
  { group: 'command', title: 'Parancsblokkok' },
  { group: 'control', title: 'Vezérlőblokkok' },
]