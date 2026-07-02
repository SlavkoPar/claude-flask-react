export interface Group {
  id: number
  parent_id: number | null
  user_id: number
  name: string
  description: string | null
  has_child_groups: boolean
  created_at: string
}
