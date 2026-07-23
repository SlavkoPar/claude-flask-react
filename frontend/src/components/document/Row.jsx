import { Button } from 'react-bootstrap'
import docIcon from '../../assets/Doc.svg'
import { SERVER_URL } from '../../config'

export default function Row({ document, isOwner, onEdit, onDelete }) {
  return (
    <div className="document-row">
      <img src={docIcon} alt="Document" className="document-row-doc-icon" />
      <button type="button" className="btn btn-link document-row-title p-0" onClick={() => onEdit(document)}>
        {document.description}
      </button>
      {document.link && (
        <a href={document.link} target="_blank" rel="noreferrer" className="document-row-link">↗</a>
      )}
      {document.has_pdf && (
        <a
          href={`${SERVER_URL}/api/documents/${document.id}/pdf`}
          target="_blank"
          rel="noreferrer"
          className="document-row-link"
        >
          Download original PDF
        </a>
      )}
      {isOwner && (
        <Button type="button" variant="outline-danger" size="sm" aria-label="Delete document" onClick={() => onDelete(document.id)}>✕</Button>
      )}
    </div>
  )
}
