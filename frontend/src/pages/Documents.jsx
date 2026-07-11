import { useEffect, useState } from 'react'
import { Container, Button, Form, Row, Col } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import List from '../components/document/List'
import AsyncAutocomplete from '../components/common/AsyncAutocomplete'
import { SERVER_URL } from '../config'

async function fetchDocumentOptions(query) {
  const params = new URLSearchParams()
  if (query) params.set('name', query)
  const res = await fetch(`${SERVER_URL}/api/documents?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load documents')
  const data = await res.json()
  return data.map(d => ({ id: d.id, label: d.description }))
}

export default function Documents() {
  const [name, setName] = useState('')
  const [groupId, setGroupId] = useState('')
  const [groupOptions, setGroupOptions] = useState([])

  useEffect(() => {
    fetch(`${SERVER_URL}/api/groups/options`, { credentials: 'include' })
      .then(r => r.json())
      .then(setGroupOptions)
  }, [])

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1>Documents</h1>
        <Button as={Link} to="/documents/add" variant="primary">Add document</Button>
      </div>
      <Row className="g-2 mb-3">
        <Col md={6}>
          <AsyncAutocomplete
            className="form-input"
            placeholder="Filter by description"
            fetchOptions={fetchDocumentOptions}
            onInputChange={setName}
            onSelect={option => setName(option?.label || '')}
          />
        </Col>
        <Col md={6}>
          <Form.Select value={groupId} onChange={e => setGroupId(e.target.value)}>
            <option value="">All groups</option>
            {groupOptions.map(o => (
              <option key={o.id} value={o.id}>{o.name}</option>
            ))}
          </Form.Select>
        </Col>
      </Row>
      <List name={name} groupId={groupId ? Number(groupId) : null} />
    </Container>
  )
}
