from supabase import create_client, Client

# Replace with your Supabase credentials
SUPABASE_URL = "https://aavaqbqugbiqklvtsmsj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFhdmFxYnF1Z2JpcWtsdnRzbXNqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE4MTUzMDYsImV4cCI6MjA0NzM5MTMwNn0.1604HS5mtk22B6bmdeIS7-F_sDvpYiC1aVkC4h9rMuk"

def get_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)
