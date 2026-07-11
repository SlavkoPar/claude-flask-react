import { useState } from 'react'
import Row from './Row'
import folderIcon from '../../assets/folder.svg'

export default function GroupSection({ group, currentUserId, onEdit, onDelete }) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="document-group-row">
      <div className="document-group-row-content">
        <img src={folderIcon} alt="Group" className="document-group-row-icon" />
        <span className="document-group-row-name">{group.name}</span>
        <button
          type="button"
          className="document-group-row-toggle btn btn-lg p-1"
          onClick={() => setExpanded(e => !e)}
          aria-label={expanded ? 'Collapse' : 'Expand'}
        >
          {expanded ? '▾' : '▸'}
        </button>
        <span className="document-group-row-count">{group.documents.length}</span>
      </div>
      {expanded && (
        <div className="document-children">
          {group.documents.map(document => (
            <Row
              key={document.id}
              document={document}
              isOwner={document.user_id === currentUserId}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  )
}
