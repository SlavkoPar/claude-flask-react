import { useEffect, useState } from 'react'
import { Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import QuestionModal from './QuestionModal'
import qIcon from '../../assets/Q.png'
import aIcon from '../../assets/A.png'

async function fetchQuestions(groupId) {
  const res = await fetch(`${SERVER_URL}/api/questions?group_id=${groupId}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load questions')
  return res.json()
}

async function deleteQuestion(id) {
  const res = await fetch(`${SERVER_URL}/api/questions/${id}`, { method: 'DELETE', credentials: 'include' })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to delete question')
  }
}

export default function QuestionsSection({ groupId }) {
  const [questions, setQuestions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalQuestion, setModalQuestion] = useState(null) // null = closed, object = open (id present -> edit)
  const [scrollY, setScrollY] = useState(0)

  const load = () => {
    setLoading(true)
    fetchQuestions(groupId).then(setQuestions).finally(() => setLoading(false))
  }

  useEffect(load, [groupId])

  const openModal = question => {
    setScrollY(window.scrollY)
    setModalQuestion(question || { text: '', description: '' })
  }

  const closeModal = () => {
    setModalQuestion(null)
    load() // answers may have been assigned/unassigned while the modal was open
    requestAnimationFrame(() => window.scrollTo(0, scrollY))
  }

  const handleSaved = () => {
    closeModal()
  }

  const handleDelete = async id => {
    if (!window.confirm('Delete this question?')) return
    try {
      await deleteQuestion(id)
      load()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="questions">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h5 className="mb-0">Questions</h5>
        <Button type="button" variant="primary" size="sm" onClick={() => openModal(null)}>Add Question</Button>
      </div>
      {error && <div className="text-danger small mb-2">{error}</div>}
      {loading ? (
        <div className="question-spinner">Loading…</div>
      ) : questions.length === 0 ? (
        <div className="text-muted small">No questions yet.</div>
      ) : (
        questions.map(q => (
          <div key={q.id} className="question-row">
            <img src={qIcon} alt="Question" className="question-row-q-icon" />
            <button type="button" className="btn btn-link title p-0" onClick={() => openModal(q)}>
              {q.text}
            </button>
            <span className="question-row-answers">
              <img src={aIcon} alt="Assigned answers" className="question-row-answers-a-icon" />
              {q.num_of_assigned_answers}
            </span>
            <Button type="button" variant="outline-danger" size="sm" aria-label="Delete question" onClick={() => handleDelete(q.id)}>✕</Button>
          </div>
        ))
      )}
      {modalQuestion && (
        <QuestionModal
          groupId={groupId}
          question={modalQuestion.id ? modalQuestion : null}
          onSaved={handleSaved}
          onClose={closeModal}
        />
      )}
    </div>
  )
}
