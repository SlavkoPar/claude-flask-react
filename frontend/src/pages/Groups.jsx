import { useEffect, useState } from 'react'
import { Container, Form, Row, Col, Button } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import List from '../components/group/List'
import { SERVER_URL } from '../config'

export default function Groups() {
  const [options, setOptions] = useState([])
  const [name, setName] = useState('')
  const [parentId, setParentId] = useState('')

  useEffect(() => {
    fetch(`${SERVER_URL}/api/groups/options`, { credentials: 'include' })
      .then(r => r.json())
      .then(setOptions)
  }, [])

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1>Groups</h1>
        <Button as={Link} to="/groups/add" variant="primary">Add group</Button>
      </div>
      <Form className="groups-border p-3 mb-3">
        <Row className="g-2">
          <Col md={6}>
            <Form.Control
              placeholder="Filter by name"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </Col>
          <Col md={6}>
            <Form.Select value={parentId} onChange={e => setParentId(e.target.value)}>
              <option value="">All parent groups</option>
              {options.map(o => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </Form.Select>
          </Col>
        </Row>
      </Form>
      <List parentId={parentId ? Number(parentId) : null} name={name} />
    </Container>
  )
}
