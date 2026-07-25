import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { SERVER_URL } from '../config'
import { useAuth } from '../context/AuthContext'

export default function GoogleCallback() {
  const navigate = useNavigate()
  const { setUser } = useAuth()

  useEffect(() => {
    fetch(`${SERVER_URL}/auth/google/callback${window.location.search}`, { credentials: 'include' })
      .then(r => (r.ok ? r.json() : Promise.reject(new Error('Google sign-in failed'))))
      .then(data => {
        setUser(data.user)
        navigate('/', { replace: true })
      })
      .catch(() => navigate('/login', { replace: true }))
  }, [navigate, setUser])

  return <div className="text-muted small p-3">Signing you in…</div>
}
