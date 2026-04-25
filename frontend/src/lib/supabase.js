import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://poupbwuajqbdhokkzerr.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvdXBid3VhanFiZGhva2t6ZXJyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY5MzM2MjUsImV4cCI6MjA5MjUwOTYyNX0.Oa4abwlA0vHTfRSMcGTKRxHnHyurQAAdBw_LHncTX7s'

export const supabase = createClient(supabaseUrl, supabaseKey)
