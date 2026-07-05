import { useState } from 'react'
import { Container, Button } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import List from '../components/answer/List'
import AsyncAutocomplete from '../components/common/AsyncAutocomplete'
import { SERVER_URL } from '../config'

async function fetchAnswerOptions(query) {
  const params = new URLSearchParams()
  if (query) params.set('name', query)
  const res = await fetch(`${SERVER_URL}/api/answers?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load answers')
  const data = await res.json()
  return data.map(a => ({ id: a.id, label: a.short_desc }))
}

export default function Answers() {
  const [name, setName] = useState('')

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1>Answers</h1>
        <Button as={Link} to="/answers/add" variant="primary">Add answer</Button>
      </div>
      <AsyncAutocomplete
        className="form-input mb-3"
        placeholder="Filter by name"
        fetchOptions={fetchAnswerOptions}
        onInputChange={setName}
        onSelect={option => setName(option?.label || '')}
      />
      <List name={name} />
    </Container>
  )
}
