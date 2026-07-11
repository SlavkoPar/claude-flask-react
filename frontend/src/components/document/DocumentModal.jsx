import { useEffect, useRef, useState } from 'react'
import { Modal, Form, Button, Alert, Spinner } from 'react-bootstrap'
import { SERVER_URL } from '../../config'

async function fetchDocument(id) {
  const res = await fetch(`${SERVER_URL}/api/documents/${id}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load document')
  return res.json()
}

async function saveDocument(document, values, pdfFile) {
  const isEdit = Boolean(document?.id)
  const formData = new FormData()
  formData.append('description', values.description)
  formData.append('content', values.content)
  formData.append('link', values.link)
  formData.append('group_id', values.group_id)
  if (pdfFile) formData.append('file', pdfFile)
  const res = await fetch(
    isEdit ? `${SERVER_URL}/api/documents/${document.id}` : `${SERVER_URL}/api/documents`,
    {
      method: isEdit ? 'PUT' : 'POST',
      credentials: 'include',
      body: formData,
    }
  )
  const data = await res.json()
  if (!res.ok) throw Object.assign(new Error(data.error), { values: data.values })
  return data
}

async function extractPdf(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${SERVER_URL}/api/documents/extract-pdf`, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Failed to read PDF')
  return data.content
}

export default function DocumentModal({ document, readOnly = false, onSaved, onClose }) {
  const [values, setValues] = useState({ description: '', content: '', link: '', group_id: '' })
  const [groupOptions, setGroupOptions] = useState([])
  const [hasPdf, setHasPdf] = useState(false)
  const [pdfFile, setPdfFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const initialValuesRef = useRef(values)
  const isDirty = pdfFile || JSON.stringify(values) !== JSON.stringify(initialValuesRef.current)

  useEffect(() => {
    fetch(`${SERVER_URL}/api/groups/options`, { credentials: 'include' })
      .then(r => r.json())
      .then(setGroupOptions)
  }, [])

  useEffect(() => {
    if (!document?.id) {
      setLoading(false)
      return
    }
    fetchDocument(document.id)
      .then(full => {
        const next = {
          description: full.description || '',
          content: full.content || '',
          link: full.link || '',
          group_id: full.group_id != null ? String(full.group_id) : '',
        }
        initialValuesRef.current = next
        setValues(next)
        setHasPdf(full.has_pdf)
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [document])

  const handleSubmit = async e => {
    e.preventDefault()
    e.stopPropagation()
    setSaving(true)
    setError(null)
    try {
      await saveDocument(document, values, pdfFile)
      onSaved()
    } catch (err) {
      setError(err.message)
      if (err.values) setValues(v => ({ ...v, ...err.values }))
    } finally {
      setSaving(false)
    }
  }

  const handleFileChange = async e => {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setPdfFile(file)
    setExtracting(true)
    setError(null)
    try {
      const content = await extractPdf(file)
      setValues(v => ({ ...v, content }))
    } catch (err) {
      setError(err.message)
    } finally {
      setExtracting(false)
    }
  }

  return (
    <Modal show onHide={onClose} dialogClassName="document-modal" centered>
      <Modal.Header closeButton>
        <Modal.Title>{readOnly ? 'View document' : document ? 'Edit document' : 'Add document'}</Modal.Title>
      </Modal.Header>
      <Form onSubmit={handleSubmit}>
        <Modal.Body className="document-modal-body">
          {error && <Alert variant="danger">{error}</Alert>}
          {loading ? (
            <Spinner animation="border" size="sm" />
          ) : (
            <>
              <Form.Group className="mb-3">
                <Form.Label>Description</Form.Label>
                <Form.Control
                  className="form-input"
                  value={values.description}
                  onChange={e => setValues(v => ({ ...v, description: e.target.value }))}
                  readOnly={readOnly}
                  autoFocus
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Group</Form.Label>
                <Form.Select
                  className="form-input"
                  value={values.group_id}
                  onChange={e => setValues(v => ({ ...v, group_id: e.target.value }))}
                  disabled={readOnly}
                >
                  <option value="">Select a group…</option>
                  {groupOptions.map(o => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </Form.Select>
              </Form.Group>
              {!readOnly && (
                <Form.Group className="mb-3">
                  <Form.Label>Upload PDF</Form.Label>
                  <Form.Control
                    type="file"
                    accept="application/pdf"
                    className="form-input"
                    onChange={handleFileChange}
                    disabled={extracting}
                  />
                  {extracting && <div className="text-muted small mt-1">Extracting text…</div>}
                  {pdfFile && <div className="text-muted small mt-1">Selected: {pdfFile.name}</div>}
                </Form.Group>
              )}
              {hasPdf && document?.id && (
                <div className="mb-3">
                  <a href={`${SERVER_URL}/api/documents/${document.id}/pdf`} target="_blank" rel="noreferrer">
                    Download original PDF
                  </a>
                </div>
              )}
              <Form.Group className="mb-3">
                <Form.Label>Content</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={8}
                  className="form-input"
                  value={values.content}
                  onChange={e => setValues(v => ({ ...v, content: e.target.value }))}
                  readOnly={readOnly}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Link</Form.Label>
                <Form.Control
                  className="form-input"
                  value={values.link}
                  onChange={e => setValues(v => ({ ...v, link: e.target.value }))}
                  readOnly={readOnly}
                />
              </Form.Group>
            </>
          )}
        </Modal.Body>
        {!readOnly && isDirty && (
          <Modal.Footer>
            <Button
              type="button"
              variant="outline-secondary"
              onClick={() => setValues(initialValuesRef.current)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={saving}>Save</Button>
          </Modal.Footer>
        )}
      </Form>
    </Modal>
  )
}
