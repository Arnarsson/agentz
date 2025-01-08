#!/usr/bin/env python3
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import json
import webbrowser
import jwt
from jwt import PyJWKClient

# Load environment variables from backend/.env
env_path = Path(__file__).parent.parent / "backend" / ".env"
load_dotenv(env_path)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_PUBLISHABLE_KEY = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", os.getenv("CLERK_PUBLISHABLE_KEY"))

if not CLERK_SECRET_KEY or not CLERK_PUBLISHABLE_KEY:
    raise ValueError("CLERK_SECRET_KEY or CLERK_PUBLISHABLE_KEY not found in .env file")

def get_clerk_instance_id():
    """Extract instance ID from publishable key."""
    if not CLERK_PUBLISHABLE_KEY:
        print("No publishable key found")
        return None
    # Format: pk_test_cG9zc2libGUtbG9jdXN0LTgzLmNsZXJrLmFjY291bnRzLmRldiQ
    try:
        print(f"Publishable key: {CLERK_PUBLISHABLE_KEY}")
        instance_id = CLERK_PUBLISHABLE_KEY.split('_')[2]
        print(f"Instance ID: {instance_id}")
        return instance_id
    except Exception as e:
        print(f"Error parsing instance ID: {e}")
        return None

def get_clerk_frontend_url():
    """Get the Clerk frontend URL."""
    instance_id = get_clerk_instance_id()
    if not instance_id:
        print("Error: Could not determine Clerk instance ID from publishable key")
        return None
    return f"https://possible-locust-83.clerk.accounts.dev/sign-in"

def get_clerk_jwks_url():
    """Get the JWKS URL for the Clerk instance."""
    instance_id = get_clerk_instance_id()
    if not instance_id:
        return None
    return f"https://possible-locust-83.clerk.accounts.dev/.well-known/jwks.json"

def verify_token(token):
    """Verify a JWT token using Clerk's JWKS endpoint."""
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        # First decode without verification to get the header
        unverified_header = jwt.get_unverified_header(token)
        print(f"Token header: {json.dumps(unverified_header, indent=2)}")
        
        # Get the key ID from the header
        kid = unverified_header.get('kid')
        if not kid:
            return False, "No 'kid' in token header"
        print(f"Key ID from token: {kid}")
            
        # Get the public key from JWKS
        jwks_url = get_clerk_jwks_url()
        if not jwks_url:
            return False, "Could not determine JWKS URL"
        print(f"JWKS URL: {jwks_url}")
            
        # Fetch JWKS directly first to debug
        jwks_response = requests.get(jwks_url)
        print(f"JWKS Response: {json.dumps(jwks_response.json(), indent=2)}")
            
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print(f"Found signing key with kid: {signing_key.key_id}")
        
        # Verify the token
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True}
        )
        return True, decoded
        
    except Exception as e:
        return False, str(e)

def print_instructions():
    """Print instructions for getting a session token."""
    frontend_url = get_clerk_frontend_url()
    if not frontend_url:
        print("Error: Could not determine Clerk frontend URL")
        return
        
    print("\nTo get a session token:")
    print("1. Visit the Clerk sign-in page:")
    print(f"   {frontend_url}")
    print("\n2. Sign in or create an account")
    print("\n3. After signing in, open your browser's developer tools:")
    print("   - Press F12 or right-click and select 'Inspect'")
    print("   - Go to the 'Network' tab")
    print("   - Look for requests to Clerk's API")
    print("   - Find the 'Authorization' header in any request")
    print("   - The token will be in the format: 'Bearer <your_token>'")
    print("\n4. Use the token with our API:")
    print('   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/auth/me')
    print("\n5. To verify a token, run this script with the token as an argument:")
    print('   python3 scripts/get_clerk_token.py "Bearer YOUR_TOKEN"')
    
    # Open the sign-in page in the default browser
    webbrowser.open(frontend_url)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Token provided as argument
        token = sys.argv[1]
        print(f"\nVerifying token...")
        is_valid, result = verify_token(token)
        if is_valid:
            print("\nToken is valid!")
            print("\nDecoded token:")
            print(json.dumps(result, indent=2))
        else:
            print("\nToken verification failed:")
            print(result)
    else:
        print_instructions() 