import { useRef, useState } from 'react'
import { Button } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import AsyncAutocomplete from '../common/AsyncAutocomplete'
import { withLineBreaks } from '../../utils/textFormat'

async function searchQuestions(q) {
  const params = new URLSearchParams({ q })
  const res = await fetch(`${SERVER_URL}/api/questions/search?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to search questions')
  const data = await res.json()
  return data.map(q => ({ id: q.id, label: q.text }))
}

async function searchDocuments(q) {
  const params = new URLSearchParams({ q })
  const res = await fetch(`${SERVER_URL}/api/documents/search?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to search documents')
  return res.json()
}

async function createQuestionFromFilter(text) {
  const res = await fetch(`${SERVER_URL}/api/questions/from-filter`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error('Failed to save question')
  return res.json()
}

async function askChat(message, documentId) {
  const res = await fetch(`${SERVER_URL}/api/chat`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages: [{ role: 'user', content: message }], document_id: documentId }),
  })
  if (!res.ok) throw new Error('Failed to get a chat answer')
  const data = await res.json()
  return data.reply
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
  const [chatReply, setChatReply] = useState(null)
  const [chatLoading, setChatLoading] = useState(false)
  const filterRef = useRef('')

  // Last resort when the structured Q&A search comes up empty: ask Claude
  // directly (grounded on the matched document's PDF via /api/chat when one
  // is known) instead of just showing "No matching answers found."
  const tryChatFallback = (message, documentId) => {
    setChatReply(null)
    setChatLoading(true)
    askChat(message, documentId)
      .then(setChatReply)
      .catch(() => setChatReply(null))
      .finally(() => setChatLoading(false))
  }

  const handleSelectQuestion = option => {
    if (!option) return
    setQuestion(option)
    setIndex(0)
    setChatReply(null)
    fetchCandidateAnswers(option.id)
      .then(result => {
        setCandidates(result)
        if (result.length === 0) {
          // Ground the chat fallback on a matching document's PDF (via the
          // Files API) when one exists, same as the from-filter path below.
          searchDocuments(option.label)
            .then(docs => tryChatFallback(option.label, docs[0]?.id ?? null))
            .catch(() => tryChatFallback(option.label, null))
        }
      })
      .catch(e => setError(e.message))
  }

  // No question matched the typed filter — fall back to a document match, and
  // if one satisfies the search, save the filter itself as a new question so
  // its (vector-searched) candidate answers can be shown and acted on normally.
  const handleQuestionResults = options => {
    const filter = filterRef.current
    if (options.length > 0 || !filter) return
    searchDocuments(filter)
      .then(docs => {
        if (docs.length === 0) return
        const documentId = docs[0].id
        return createQuestionFromFilter(filter).then(newQuestion => {
          setQuestion({ id: newQuestion.id, label: newQuestion.text })
          setIndex(0)
          setChatReply(null)
          return fetchCandidateAnswers(newQuestion.id).then(result => {
            setCandidates(result)
            if (result.length === 0) tryChatFallback(filter, documentId)
          })
        })
      })
      .catch(e => setError(e.message))
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
          onInputChange={q => { filterRef.current = q }}
          onResults={handleQuestionResults}
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
          chatLoading ? (
            <div className="text-muted small">Asking Claude…</div>
          ) : chatReply ? (
            <div className="sidebar-answer-card">
              <div className="text-muted small mb-1">Claude's answer</div>
              <div className="small">{withLineBreaks(chatReply)}</div>
            </div>
          ) : (
            <div className="text-muted small">No matching answers found.</div>
          )
        ) : (
          <div className="sidebar-answer-card">
            <div className="text-muted small mb-1">
              Answer {index + 1} of {candidates.length}
            </div>
            <div className="answer-row-title mb-2">
              {current.description}
              {current.link && (
                <a href={current.link} target="_blank" rel="noreferrer" className="answer-row-link">↗</a>
              )}
            </div>
            <div className="d-flex gap-2">
              <Button variant="success" size="sm" onClick={handleFixed}>Fixed</Button>
              <Button variant="outline-danger" size="sm" onClick={handleNotFixed}>Not Fixed</Button>
            </div>
            {current.related_documents?.length > 0 && (
              <div className="sidebar-related-documents">
                <div className="text-muted small mb-1">Related documents</div>
                {current.related_documents.map(doc => (
                  <div key={doc.id} className="sidebar-related-document small">
                    <div>
                      <span className="title">{doc.description}</span>
                      {doc.link && (
                        <a href={doc.link} target="_blank" rel="noreferrer" className="answer-row-link"> ↗</a>
                      )}
                    </div>
                    <div className="sidebar-related-document-snippet">{withLineBreaks(doc.snippet)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}
