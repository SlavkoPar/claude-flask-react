export interface Document {
  id: number
  user_id: number
  group_id: number
  description: string
  content: string
  link: string | null
  created_at: string
  pdf_filename: string | null
  has_pdf: boolean
}
