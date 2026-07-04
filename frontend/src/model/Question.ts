export interface Question {
  id: number
  group_id: number
  user_id: number
  text: string
  description: string | null
  num_of_assigned_answers: number
  created_at: string
}
