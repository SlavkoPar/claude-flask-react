import { Container, Button } from 'react-bootstrap'
import { SERVER_URL } from '../config'

export default function Login() {
  return (
    <Container className="text-center mt-5">
      <h1>Sign in</h1>
      <p>You need to sign in to continue.</p>
      <Button variant="outline-secondary" href={`${SERVER_URL}/auth/google`}>
        Sign in with Google
      </Button>
    </Container>
  )
}
