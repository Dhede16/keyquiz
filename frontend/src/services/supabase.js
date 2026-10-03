import { createClient } from '@supabase/supabase-js'

const supabaseUrl =
  import.meta.env.VITE_SUPABASE_URL || 'https://vkpluwyyalyrpjzigrss.supabase.co'
const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZrcGx1d3l5YWx5cnBqemlncnNzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA2OTEwNjIsImV4cCI6MjEwNjI2NzA2Mn0.pc8L5DvQZllGD5MBr9PE2guHSkkK-YbEDwadLwBw5L0'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

export default supabase
