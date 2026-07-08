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

  const demoLogin = async () => {
    const r = await fetch(`${SERVER_URL}/api/auth/demo-login`, { method: 'POST', credentials: 'include' })
    if (r.ok) {
      const data = await r.json()
      setUser(data.user)
    }
  }

  return (
    <AuthContext.Provider value={{ user, setUser, logout, demoLogin }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
