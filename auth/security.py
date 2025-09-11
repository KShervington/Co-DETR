#!/usr/bin/env python3
"""
FastAPI Security Integration for Co-DETR API

Provides FastAPI security dependency for API key authentication.
"""

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from .api_key_manager import ApiKeyManager, ApiKey

logger = logging.getLogger(__name__)

class ApiKeyAuthenticator:
    """
    FastAPI security authenticator for API keys.
    Follows dependency inversion principle by accepting ApiKeyManager interface.
    """
    
    def __init__(self, key_manager: ApiKeyManager):
        self.key_manager = key_manager
        self.security = HTTPBearer(
            scheme_name="API Key",
            description="Provide your API key as a Bearer token"
        )
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> ApiKey:
        """
        FastAPI dependency for API key authentication.
        
        Args:
            credentials: HTTP Bearer credentials from request
            
        Returns:
            ApiKey object if authentication successful
            
        Raises:
            HTTPException: If authentication fails
        """
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        api_key = credentials.credentials
        key_data = self.key_manager.validate_key(api_key)
        
        if not key_data:
            logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Successful authentication for key: {key_data.name}")
        return key_data

class ApiKeyHeader:
    """
    Alternative authenticator that accepts API key via X-API-Key header.
    Provides flexibility for different client implementations.
    """
    
    def __init__(self, key_manager: ApiKeyManager):
        self.key_manager = key_manager
    
    async def __call__(self, x_api_key: Optional[str] = None) -> ApiKey:
        """
        FastAPI dependency for header-based API key authentication.
        
        Args:
            x_api_key: API key from X-API-Key header
            
        Returns:
            ApiKey object if authentication successful
            
        Raises:
            HTTPException: If authentication fails
        """
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-API-Key header required",
            )
        
        key_data = self.key_manager.validate_key(x_api_key)
        
        if not key_data:
            logger.warning(f"Invalid API key attempt via header: {x_api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
            )
        
        logger.info(f"Successful header authentication for key: {key_data.name}")
        return key_data

def create_api_key_authenticator(storage_file: str = "auth/api_keys.json") -> ApiKeyAuthenticator:
    """
    Factory function to create an API key authenticator.
    Follows the factory pattern for easy configuration.
    """
    key_manager = ApiKeyManager(storage_file)
    return ApiKeyAuthenticator(key_manager)

def create_header_authenticator(storage_file: str = "auth/api_keys.json") -> ApiKeyHeader:
    """
    Factory function to create a header-based API key authenticator.
    """
    key_manager = ApiKeyManager(storage_file)
    return ApiKeyHeader(key_manager)
