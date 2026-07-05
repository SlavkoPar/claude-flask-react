import { useEffect, useState } from 'react'
import { Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import AnswerPickerModal from './AnswerPickerModal'
import aIcon from '../../assets/A.png'

async function fetchAssigned(questionId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load assigned answers')
  return res.json()
}

async function unassign(questionId, answerId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers/${answerId}/unassign`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to unassign answer')
}

export default function AssignedAnswersSection({ questionId }) {
  const [assigned, setAssigned] = useState([])
  const [error, setError] = useState(null)
  const [pickerOpen, setPickerOpen] = useState(false)

  const load = () => {
    fetchAssigned(questionId).then(setAssigned).catch(e => setError(e.message))
  }

  useEffect(load, [questionId])

  const handleUnassign = async answerId => {
    try {
      await unassign(questionId, answerId)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="assigned-answers-section">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h6 className="mb-0">Assigned answers</h6>
        <Button type="button" variant="outline-primary" size="sm" onClick={() => setPickerOpen(true)}>
          Assign answer
        </Button>
      </div>
      {error && <div className="text-danger small mb-2">{error}</div>}
      {assigned.length === 0 ? (
        <div className="text-muted small">No answers assigned yet.</div>
      ) : (
        <div className="assigned-answers-list">
          {assigned.map(a => (
            <div key={a.id} className="assigned-answer-row">
              <img src={aIcon} alt="Answer" className="answer-row-a-icon" />
              <span className="answer-row-title">{a.short_desc}</span>
              <Button variant="outline-danger" size="sm" onClick={() => handleUnassign(a.id)}>Remove</Button>
            </div>
          ))}
        </div>
      )}
      {pickerOpen && (
        <AnswerPickerModal
          questionId={questionId}
          onAssigned={load}
          onClose={() => setPickerOpen(false)}
        />
      )}
    </div>
  )
}
