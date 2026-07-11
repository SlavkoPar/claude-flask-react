import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Container, Form, Button, Alert } from 'react-bootstrap'
import { SERVER_URL } from '../config'

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

export default function DocumentForm() {
  const navigate = useNavigate()
  const [values, setValues] = useState({ description: '', content: '', link: '', group_id: '' })
  const [groupOptions, setGroupOptions] = useState([])
  const [pdfFile, setPdfFile] = useState(null)
  const [error, setError] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const initialValuesRef = useRef(values)
  const isDirty = pdfFile || JSON.stringify(values) !== JSON.stringify(initialValuesRef.current)

  useEffect(() => {
    fetch(`${SERVER_URL}/api/groups/options`, { credentials: 'include' })
      .then(r => r.json())
      .then(setGroupOptions)
  }, [])

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

  const handleSubmit = async e => {
    e.preventDefault()
    const formData = new FormData()
    formData.append('description', values.description)
    formData.append('content', values.content)
    formData.append('link', values.link)
    formData.append('group_id', values.group_id)
    if (pdfFile) formData.append('file', pdfFile)
    const res = await fetch(`${SERVER_URL}/api/documents`, {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })
    const data = await res.json()
    if (!res.ok) {
      setError(data.error)
      if (data.values) {
        setValues({
          description: data.values.description ?? values.description,
          content: data.values.content ?? values.content,
          link: data.values.link ?? '',
          group_id: data.values.group_id ?? values.group_id,
        })
      }
      return
    }
    navigate('/documents')
  }

  return (
    <Container>
      <h1>Add document</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form className="document-form p-3" onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Description</Form.Label>
          <Form.Control
            className="form-input"
            value={values.description}
            onChange={e => setValues(v => ({ ...v, description: e.target.value }))}
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Group</Form.Label>
          <Form.Select
            className="form-input"
            value={values.group_id}
            onChange={e => setValues(v => ({ ...v, group_id: e.target.value }))}
          >
            <option value="">Select a group…</option>
            {groupOptions.map(o => (
              <option key={o.id} value={o.id}>{o.name}</option>
            ))}
          </Form.Select>
        </Form.Group>
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
        <Form.Group className="mb-3">
          <Form.Label>Content</Form.Label>
          <Form.Control
            as="textarea"
            rows={8}
            className="form-input"
            value={values.content}
            onChange={e => setValues(v => ({ ...v, content: e.target.value }))}
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Link</Form.Label>
          <Form.Control
            className="form-input"
            value={values.link}
            onChange={e => setValues(v => ({ ...v, link: e.target.value }))}
          />
        </Form.Group>
        {isDirty && (
          <>
            <Button type="submit" variant="primary">Save</Button>{' '}
            <Button
              type="button"
              variant="outline-secondary"
              onClick={() => setValues(initialValuesRef.current)}
            >
              Cancel
            </Button>
          </>
        )}
      </Form>
    </Container>
  )
}
