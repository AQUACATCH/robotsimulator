import CommandBlock from './CommandBlock.jsx'
import ControllerBlock from './ControllerBlock.jsx'

export default function Block({ node }) {
  if (node.type === 'if' || node.type === 'while') return <ControllerBlock node={node} />
  return <CommandBlock node={node} />
}