import Block from './Block.jsx'
import DropSlot from './DropSlot.jsx'

export default function BlockList({ list, parentId = null, branch = 'end', emptyLabel }) {
  if (list.length === 0) {
    return <DropSlot targetId={parentId} where={branch} big label={emptyLabel} />
  }
  return (
    <div className='flex flex-col'>
      <DropSlot targetId={list[0].id} where='before' />
      {list.map((node) => (
        <div key={node.id}>
          <Block node={node} />
          <DropSlot targetId={node.id} where='after' />
        </div>
      ))}
    </div>
  )
}