import hashlib
import hmac
import os
from typing import Optional

SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")

def hash_password(password: str) -> str:
    """
    Hashes a password using SHA-256.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verifies a password against a hashed password.

    Args:
        password (str): The password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the password matches the hashed password, False otherwise.
    """
    return hash_password(password) == hashed_password

def generate_token(data: str) -> str:
    """
    Generates a secure token using HMAC-SHA256.

    Args:
        data (str): The data to include in the token.

    Returns:
        str: The generated token.
    """
    return hmac.new(SECRET_KEY.encode(), data.encode(), hashlib.sha256).hexdigest()

def verify_token(data: str, token: str) -> bool:
    """
    Verifies a token using HMAC-SHA256.

    Args:
        data (str): The data to include in the token.
        token (str): The token to verify.

    Returns:
        bool: True if the token is valid, False otherwise.
    """
    return hmac.compare_digest(generate_token(data), token)

def generate_api_key() -> str:
    """
    Generates a random API key.

    Returns:
        str: The generated API key.
    """
    return hashlib.sha256(os.urandom(32)).hexdigest()

def verify_api_key(api_key: str, stored_api_key: str) -> bool:
    """
    Verifies an API key against a stored API key.

    Args:
        api_key (str): The API key to verify.
        stored_api_key (str): The stored API key to compare against.

    Returns:
        bool: True if the API key matches the stored API key, False otherwise.
    """
    return hmac.compare_digest(api_key, stored_api_key)

def authenticate_user(username: str, password: str, stored_password_hash: str) -> bool:
    """
    Authenticates a user by verifying the provided password against the stored password hash.

    Args:
        username (str): The username of the user.
        password (str): The password provided by the user.
        stored_password_hash (str): The stored password hash to compare against.

    Returns:
        bool: True if the authentication is successful, False otherwise.
    """
    return verify_password(password, stored_password_hash)

def authorize_user(api_key: str, stored_api_key: str) -> bool:
    """
    Authorizes a user by verifying the provided API key against the stored API key.

    Args:
        api_key (str): The API key provided by the user.
        stored_api_key (str): The stored API key to compare against.

    Returns:
        bool: True if the authorization is successful, False otherwise.
    """
    return verify_api_key(api_key, stored_api_key)
