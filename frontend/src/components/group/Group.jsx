import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Container, Form, Button, Alert } from 'react-bootstrap'
import { SERVER_URL } from '../../config'
import QuestionsSection from './QuestionsSection'

export default function Group() {
  const { id } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [options, setOptions] = useState([])
  const [values, setValues] = useState({
    name: '',
    description: '',
    parent_id: searchParams.get('parent') || '',
  })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(isEdit)
  const initialValuesRef = useRef(values)

  useEffect(() => {
    fetch(`${SERVER_URL}/api/groups/options`, { credentials: 'include' })
      .then(r => r.json())
      .then(setOptions)
  }, [])

  useEffect(() => {
    if (!isEdit) return
    fetch(`${SERVER_URL}/api/groups/${id}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        const loaded = {
          name: data.name,
          description: data.description || '',
          parent_id: data.parent_id != null ? String(data.parent_id) : '',
        }
        setValues(loaded)
        initialValuesRef.current = loaded
        setLoading(false)
      })
  }, [id, isEdit])

  const isDirty = JSON.stringify(values) !== JSON.stringify(initialValuesRef.current)

  const handleSubmit = async e => {
    e.preventDefault()
    const res = await fetch(isEdit ? `${SERVER_URL}/api/groups/${id}` : `${SERVER_URL}/api/groups`, {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(values),
    })
    const data = await res.json()
    if (!res.ok) {
      setError(data.error)
      if (data.values) {
        setValues({
          name: data.values.name ?? values.name,
          description: data.values.description ?? '',
          parent_id: data.values.parent_id ?? '',
        })
      }
      return
    }
    navigate('/groups')
  }

  if (loading) return <div className="group-spinner">Loading…</div>

  return (
    <Container>
      <h1>{isEdit ? 'Edit group' : 'Add group'}</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      <Form className="group-form p-3" onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Name</Form.Label>
          <Form.Control
            value={values.name}
            onChange={e => setValues(v => ({ ...v, name: e.target.value }))}
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Parent group</Form.Label>
          <Form.Select
            value={values.parent_id ?? ''}
            onChange={e => setValues(v => ({ ...v, parent_id: e.target.value }))}
          >
            <option value="">None (top-level)</option>
            {options
              .filter(o => !isEdit || o.id !== Number(id))
              .map(o => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
          </Form.Select>
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Description</Form.Label>
          <Form.Control
            as="textarea"
            rows={3}
            value={values.description}
            onChange={e => setValues(v => ({ ...v, description: e.target.value }))}
          />
        </Form.Group>
        {isEdit && (
          <div className="mb-3">
            <QuestionsSection groupId={Number(id)} />
          </div>
        )}
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
