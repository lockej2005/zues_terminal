from supabase import create_client, Client

# Replace with your Supabase credentials
SUPABASE_URL = "insert"
SUPABASE_KEY = "insert"

def get_supabase_client() -> Client:
    """Initialize and return the Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)
