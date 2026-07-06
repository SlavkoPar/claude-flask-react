import { Button } from 'react-bootstrap'
import aIcon from '../../assets/A.png'

export default function Row({ answer, onEdit, onDelete }) {
  return (
    <div className="answer-row">
      <img src={aIcon} alt="Answer" className="answer-row-a-icon" />
      <button type="button" className="btn btn-link answer-row-title p-0" onClick={() => onEdit(answer)}>
        {answer.short_desc}
      </button>
      {answer.link && (
        <a href={answer.link} target="_blank" rel="noreferrer" className="answer-row-link">↗</a>
      )}
      <Button type="button" variant="outline-danger" size="sm" aria-label="Delete answer" onClick={() => onDelete(answer.id)}>✕</Button>
    </div>
  )
}
