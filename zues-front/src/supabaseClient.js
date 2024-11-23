import { createClient } from '@supabase/supabase-js';

const supabaseUrl = "https://aavaqbqugbiqklvtsmsj.supabase.co";
const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdmFxYnF1Z2JpcWtsdnRzbXNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE4MTUzMDYsImV4cCI6MjA0NzM5MTMwNn0.1604HS5mtk22B6bmdeIS7-F_sDvpYiC1aVkC4h9rMuk";

export const supabase = createClient(supabaseUrl, supabaseKey);