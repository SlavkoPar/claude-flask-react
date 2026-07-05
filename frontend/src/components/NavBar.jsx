import { Navbar, Nav, NavDropdown, Container } from 'react-bootstrap'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import { SERVER_URL } from '../config'

export default function NavBar({ onToggleSidebar }) {
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
            {user === undefined ? null : user ? (
              <NavDropdown title={user.name} align="end" id="user-menu">
                <NavDropdown.Item onClick={toggleTheme}>
                  {theme === 'dark' ? 'Light theme' : 'Dark theme'}
                </NavDropdown.Item>
                <NavDropdown.Item onClick={logout}>Sign out</NavDropdown.Item>
              </NavDropdown>
            ) : (
              <Nav.Link href={`${SERVER_URL}/auth/google`}>Sign in with Google</Nav.Link>
            )}
            {user && (
              <button
                type="button"
                className="hamburger-btn"
                aria-label="Toggle sidebar"
                onClick={onToggleSidebar}
              >
                ☰
              </button>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  )
}
