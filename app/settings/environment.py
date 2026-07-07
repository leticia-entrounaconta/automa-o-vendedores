def load_environment():
    """Load environment variables from a .env file if present."""
    from dotenv import load_dotenv

    load_dotenv()
