import { useEffect, useState } from 'react'
import { Container, Form, Button } from 'react-bootstrap'
import { Link } from 'react-router-dom'
import List from '../components/answer/List'
import { SERVER_URL } from '../config'

export default function Answers() {
  const [name, setName] = useState('')
  const [suggestions, setSuggestions] = useState([])

  useEffect(() => {
    const params = new URLSearchParams()
    if (name) params.set('name', name)
    const timeout = setTimeout(() => {
      fetch(`${SERVER_URL}/api/answers?${params.toString()}`, { credentials: 'include' })
        .then(r => r.json())
        .then(data => setSuggestions(data.map(a => a.short_desc)))
    }, 200)
    return () => clearTimeout(timeout)
  }, [name])

  return (
    <Container>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1>Answers</h1>
        <Button as={Link} to="/answers/add" variant="primary">Add answer</Button>
      </div>
      <Form className="mb-3">
        <Form.Control
          className="form-input"
          placeholder="Filter by name"
          list="answer-suggestions"
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <datalist id="answer-suggestions">
          {suggestions.map(s => (
            <option key={s} value={s} />
          ))}
        </datalist>
      </Form>
      <List name={name} />
    </Container>
  )
}
