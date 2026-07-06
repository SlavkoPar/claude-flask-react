import { useState } from 'react'
import { Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import AsyncAutocomplete from '../common/AsyncAutocomplete'

async function searchQuestions(q) {
  const params = new URLSearchParams({ q })
  const res = await fetch(`${SERVER_URL}/api/questions/search?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to search questions')
  const data = await res.json()
  return data.map(q => ({ id: q.id, label: q.text }))
}

async function fetchCandidateAnswers(questionId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/candidate-answers`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load candidate answers')
  return res.json()
}

async function markFixed(questionId, answerId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers/${answerId}/fixed`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to mark answer fixed')
}

async function markNotFixed(questionId, answerId) {
  const res = await fetch(`${SERVER_URL}/api/questions/${questionId}/answers/${answerId}/not-fixed`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to mark answer not fixed')
}

export default function SideBar({ open, onClose }) {
  const [question, setQuestion] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [index, setIndex] = useState(0)
  const [error, setError] = useState(null)

  const handleSelectQuestion = option => {
    if (!option) return
    setQuestion(option)
    setIndex(0)
    fetchCandidateAnswers(option.id).then(setCandidates).catch(e => setError(e.message))
  }

  const current = candidates[index]

  const handleNotFixed = async () => {
    try {
      await markNotFixed(question.id, current.id)
      setIndex(i => (i + 1) % candidates.length)
    } catch (e) {
      setError(e.message)
    }
  }

  const handleFixed = async () => {
    try {
      await markFixed(question.id, current.id)
      setIndex(i => (i + 1) % candidates.length)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <>
      {open && <div className="sidebar-backdrop" onClick={onClose} />}
      <div className={`sidebar-panel ${open ? 'sidebar-panel-open' : ''}`}>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5 className="mb-0">Search</h5>
          <Button variant="outline-secondary" size="sm" onClick={onClose}>Close</Button>
        </div>
        {error && <div className="text-danger small mb-2">{error}</div>}
        <AsyncAutocomplete
          className="form-input mb-3"
          placeholder="Filter questions"
          fetchOptions={searchQuestions}
          onSelect={handleSelectQuestion}
          requireSelection
        />

        {question && (
          <div className="small mb-2">
            <strong>Answer for question:</strong> {question.label}
          </div>
        )}

        {!question ? (
          <div className="text-muted small">Select a question above.</div>
        ) : candidates.length === 0 ? (
          <div className="text-muted small">No matching answers found.</div>
        ) : (
          <div className="sidebar-answer-card">
            <div className="text-muted small mb-1">
              Answer {index + 1} of {candidates.length}
            </div>
            <div className="answer-row-title mb-2">
              {current.short_desc}
              {current.link && (
                <a href={current.link} target="_blank" rel="noreferrer" className="answer-row-link">↗</a>
              )}
            </div>
            {current.description && <div className="small mb-2">{current.description}</div>}
            <div className="d-flex gap-2">
              <Button variant="success" size="sm" onClick={handleFixed}>Fixed</Button>
              <Button variant="outline-danger" size="sm" onClick={handleNotFixed}>Not Fixed</Button>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
