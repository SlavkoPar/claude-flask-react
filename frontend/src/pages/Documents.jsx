import { useState } from 'react'
import { Container, Button } from 'react-bootstrap'
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

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1>Documents</h1>
        <Button as={Link} to="/documents/add" variant="primary">Add document</Button>
      </div>
      <AsyncAutocomplete
        className="form-input mb-3"
        placeholder="Filter by description"
        fetchOptions={fetchDocumentOptions}
        onInputChange={setName}
        onSelect={option => setName(option?.label || '')}
      />
      <List name={name} />
    </Container>
  )
}
