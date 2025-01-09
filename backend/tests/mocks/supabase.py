"""Mock Supabase module for testing."""
from typing import Dict, Any, Optional, Type, TypeVar
from unittest.mock import MagicMock

class MockSupabaseClient:
    """Mock Supabase client."""
    def __init__(self, url: str, key: str, **kwargs):
        """Initialize mock client."""
        self.url = url
        self.key = key
        self.storage = MagicMock()
        self.auth = MagicMock()
        self.table = MagicMock()
        self.rpc = MagicMock()
        self.functions = MagicMock()

    def table(self, name: str):
        """Mock table method."""
        return self.table

    def rpc(self, name: str, params: Optional[Dict[str, Any]] = None):
        """Mock RPC method."""
        return self.rpc

    def storage(self):
        """Mock storage method."""
        return self.storage

    def auth(self):
        """Mock auth method."""
        return self.auth

    def functions(self):
        """Mock functions method."""
        return self.functions

# Export Client type
Client = TypeVar('Client', bound=MockSupabaseClient)

def create_client(url: str, key: str, **kwargs) -> MockSupabaseClient:
    """Create a mock Supabase client."""
    return MockSupabaseClient(url, key, **kwargs) 