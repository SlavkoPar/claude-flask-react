import { useRef, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Container, Form, Button, Alert } from 'react-bootstrap'
import { SERVER_URL } from '../config'

export default function AnswerForm() {
  const navigate = useNavigate()
  const [values, setValues] = useState({ short_desc: '', description: '', link: '' })
  const [error, setError] = useState(null)
  const initialValuesRef = useRef(values)
  const isDirty = JSON.stringify(values) !== JSON.stringify(initialValuesRef.current)

  const handleSubmit = async e => {
    e.preventDefault()
    const res = await fetch(`${SERVER_URL}/api/answers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(values),
    })
    const data = await res.json()
    if (!res.ok) {
      setError(data.error)
      if (data.values) {
        setValues({
          short_desc: data.values.short_desc ?? values.short_desc,
          description: data.values.description ?? '',
          link: data.values.link ?? '',
        })
      }
      return
    }
    navigate('/answers')
  }

  return (
    <Container>
      <h1>Add answer</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form className="answer-form p-3" onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Short description</Form.Label>
          <Form.Control
            className="form-input"
            value={values.short_desc}
            onChange={e => setValues(v => ({ ...v, short_desc: e.target.value }))}
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            className="form-input"
            value={values.description}
            onChange={e => setValues(v => ({ ...v, description: e.target.value }))}
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
            <Button as={Link} to="/answers" variant="outline-secondary">Cancel</Button>
          </>
        )}
      </Form>
    </Container>
  )
}
