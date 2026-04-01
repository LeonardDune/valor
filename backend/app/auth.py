import os
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
import logging

# Configure logging for auth module
logger = logging.getLogger(__name__)

load_dotenv()

security = HTTPBearer()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

def verify_token_string(token: str):
    if not SUPABASE_URL:
        raise Exception("Server misconfiguration: Missing SUPABASE_URL")

    try:
        # 1. Debug: Log Algorithm from header without verifying signature yet
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get('alg')
        # logger.info(f"Token Algorithm: {alg}")

        # 2. Strategy: Try HS256 (Secret) if Alg matches and Secret exists
        if alg == 'HS256':
             if not SUPABASE_JWT_SECRET:
                  logger.error("Token is HS256 but SUPABASE_JWT_SECRET is missing in environment.")
                  raise Exception("Missing SUPABASE_JWT_SECRET for HS256 token validation")
             
             return jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",
                options={"verify_exp": True} 
             )

        # 3. Strategy: Try JWKS (RS256/ES256)
        jwks_url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            options={"verify_exp": True}
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT Verification Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
         logger.error(f"Auth Unexpected Error: {e}")
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return verify_token_string(credentials.credentials)

async def get_current_user(payload: dict = Depends(verify_token)):
    """
    Dependency that returns the Neo4j User node for the currently authenticated user.
    Extracted from the JWT payload and synced with Neo4j.
    """
    from app.db.crud import ensure_user_sync
    
    user_id = payload.get("sub")
    email = payload.get("email")
    user_meta = payload.get("user_metadata", {})
    name = user_meta.get("full_name") or user_meta.get("name")
    
    if not user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid token payload: missing sub or email"
        )
        
    # JIT Sync: Ensure user exists in Neo4j and is up-to-date
    # This ensures that throughout the app, 'user' is the Neo4j dictionary with 'id'
    db_user = await ensure_user_sync(user_id, email, name)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database synchronization failed for user"
        )

    # JIT Sync: Ensure PhysicalAgent entity exists in urn:valor:entities
    try:
        from app.db.fuseki_entities import ensure_person_entity
        await ensure_person_entity(user_id, name)
    except Exception as exc:
        logger.warning("Entity Registry JIT-sync mislukt voor %s: %s", user_id, exc)

    return db_user
