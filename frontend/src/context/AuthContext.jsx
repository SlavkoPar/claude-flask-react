import { createContext, useContext, useEffect, useState } from 'react'
import { SERVER_URL } from '../config'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined) // undefined = loading, null = guest

  useEffect(() => {
    fetch(`${SERVER_URL}/api/auth/me`, { credentials: 'include' })
      .then(r => (r.ok ? r.json() : { user: null }))
      .then(data => setUser(data.user))
      .catch(() => setUser(null))
  }, [])

  const logout = async () => {
    await fetch(`${SERVER_URL}/api/auth/logout`, { method: 'POST', credentials: 'include' })
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
