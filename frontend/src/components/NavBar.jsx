import { Navbar, Nav, Container, Button } from 'react-bootstrap'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { SERVER_URL } from '../config'

export default function NavBar() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()

  return (
    <Navbar expand="md" className="mb-3 shadow-sm" data-bs-theme={theme}>
      <Container>
        <Navbar.Brand as={Link} to="/">MyApp</Navbar.Brand>
        <Navbar.Toggle aria-controls="main-nav" />
        <Navbar.Collapse id="main-nav">
          <Nav className="me-auto">
            <Nav.Link as={NavLink} to="/">Home</Nav.Link>
            <Nav.Link as={NavLink} to="/groups">Groups</Nav.Link>
            {user && <Nav.Link as={NavLink} to="/answers">Answers</Nav.Link>}
          </Nav>
          <Nav className="align-items-center gap-2">
            <Button variant="outline-secondary" size="sm" onClick={toggleTheme}>
              {theme === 'dark' ? 'Light' : 'Dark'}
            </Button>
            {user === undefined ? null : user ? (
              <>
                <Navbar.Text>{user.name}</Navbar.Text>
                <Button variant="outline-secondary" size="sm" onClick={logout}>
                  Sign out
                </Button>
              </>
            ) : (
              <Nav.Link href={`${SERVER_URL}/auth/google`}>Sign in with Google</Nav.Link>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}
