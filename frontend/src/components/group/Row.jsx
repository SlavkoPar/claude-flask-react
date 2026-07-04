import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from 'react-bootstrap'
import List from './List'
import { SERVER_URL } from '../../config'
import qIcon from '../../assets/Q.png'

async function deleteGroup(id) {
  const res = await fetch(`${SERVER_URL}/api/groups/${id}`, { method: 'DELETE', credentials: 'include' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to delete group')
  }
}

export default function Row({ group, onChange }) {
  const [expanded, setExpanded] = useState(false)
  const [error, setError] = useState(null)

  const handleDelete = async () => {
    if (!window.confirm(`Delete group "${group.name}"?`)) return
    try {
      await deleteGroup(group.id)
      setError(null)
      onChange?.()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="group-row">
      <div className="group-row-content">
        {group.has_child_groups ? (
          <button
            type="button"
            className="group-row-toggle btn btn-lg p-1"
            onClick={() => setExpanded(e => !e)}
            aria-label={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? '▾' : '▸'}
          </button>
        ) : (
          <span className="group-row-spacer" />
        )}
        <Link to={`/groups/${group.id}/edit`} className="title">{group.name}</Link>
        {group.description && <span className="group-row-description">{group.description}</span>}
        <span className="group-row-questions">
          <img src={qIcon} alt="Questions" className="group-row-q-icon" />
          {group.num_of_questions}
        </span>
        <div className="group-row-actions">
          {group.num_of_questions === 0 && (
            <Link to={`/groups/add?parent=${group.id}`} className="group-row-add-link">add group</Link>
          )}
          {!group.has_child_groups && (
            <Link to={`/groups/${group.id}/edit`} className="group-row-add-link">add question</Link>
          )}
          <Button variant="outline-danger" size="sm" onClick={handleDelete}>Delete</Button>
        </div>
      </div>
      {error && <div className="group-row-error">{error}</div>}
      {expanded && group.has_child_groups && (
        <div className="group-children">
          <List parentId={group.id} />
        </div>
      )}
    </div>
  )
}
