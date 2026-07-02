import { useEffect, useState } from 'react'
import Row from './Row'
import { SERVER_URL } from '../../config'

async function fetchGroups({ parentId, name }) {
  const params = new URLSearchParams()
  if (name) params.set('name', name)
  if (parentId != null) params.set('parent_id', parentId)
  const res = await fetch(`${SERVER_URL}/api/groups?${params.toString()}`, { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to load groups')
  return res.json()
}

export default function List({ parentId = null, name = '' }) {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchGroups({ parentId, name })
      .then(data => { if (!cancelled) setGroups(data) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [parentId, name, version])

  const refresh = () => setVersion(v => v + 1)

  if (loading) return <div className="group-spinner">Loading…</div>
  if (groups.length === 0) return null

  return (
    <div className="groups">
      {groups.map(group => (
        <Row key={group.id} group={group} onChange={refresh} />
      ))}
    </div>
  )
}
