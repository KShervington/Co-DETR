#!/usr/bin/env python3
"""
API Key Management System for Co-DETR

A simple, secure API key management system following SOLID principles.
Handles API key generation, validation, and storage.
"""

import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ApiKey:
    """Data class representing an API key."""
    key_id: str
    key_hash: str
    name: str
    created_at: str
    expires_at: Optional[str] = None
    is_active: bool = True
    usage_count: int = 0
    last_used: Optional[str] = None

class ApiKeyGenerator:
    """Handles API key generation following single responsibility principle."""
    
    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key."""
        return f"codetr_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def generate_key_id() -> str:
        """Generate a unique key identifier."""
        return secrets.token_hex(8)
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Create a secure hash of the API key."""
        return hashlib.sha256(api_key.encode()).hexdigest()

class ApiKeyStorage:
    """Handles API key storage operations following single responsibility principle."""
    
    def __init__(self, storage_file: str = "auth/api_keys.json"):
        self.storage_file = storage_file
        self._ensure_storage_directory()
    
    def _ensure_storage_directory(self):
        """Ensure the storage directory exists."""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
    
    def load_keys(self) -> Dict[str, ApiKey]:
        """Load API keys from storage."""
        try:
            if not os.path.exists(self.storage_file):
                return {}
            
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                return {
                    key_id: ApiKey(**key_data) 
                    for key_id, key_data in data.items()
                }
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            return {}
    
    def save_keys(self, keys: Dict[str, ApiKey]) -> bool:
        """Save API keys to storage."""
        try:
            with open(self.storage_file, 'w') as f:
                data = {key_id: asdict(key) for key_id, key in keys.items()}
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")
            return False

class ApiKeyValidator:
    """Handles API key validation following single responsibility principle."""
    
    def __init__(self, storage: ApiKeyStorage):
        self.storage = storage
    
    def validate_key(self, api_key: str) -> Optional[ApiKey]:
        """
        Validate an API key and return the associated ApiKey object if valid.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            ApiKey object if valid, None otherwise
        """
        if not api_key or not api_key.startswith('codetr_'):
            return None
        
        key_hash = ApiKeyGenerator.hash_key(api_key)
        keys = self.storage.load_keys()
        
        for key_data in keys.values():
            if key_data.key_hash == key_hash and key_data.is_active:
                # Check if key is expired
                if key_data.expires_at:
                    expires_at = datetime.fromisoformat(key_data.expires_at)
                    if datetime.now() > expires_at:
                        continue
                
                # Update usage statistics
                key_data.usage_count += 1
                key_data.last_used = datetime.now().isoformat()
                
                # Save updated statistics
                keys[key_data.key_id] = key_data
                self.storage.save_keys(keys)
                
                return key_data
        
        return None

class ApiKeyManager:
    """
    Main API key management class following open/closed principle.
    Orchestrates key generation, storage, and validation.
    """
    
    def __init__(self, storage_file: str = "auth/api_keys.json"):
        self.storage = ApiKeyStorage(storage_file)
        self.generator = ApiKeyGenerator()
        self.validator = ApiKeyValidator(self.storage)
    
    def create_key(self, name: str, expires_days: Optional[int] = None) -> Tuple[str, str]:
        """
        Create a new API key.
        
        Args:
            name: Human-readable name for the key
            expires_days: Number of days until expiration (None for no expiration)
            
        Returns:
            Tuple of (api_key, key_id)
        """
        api_key = self.generator.generate_key()
        key_id = self.generator.generate_key_id()
        key_hash = self.generator.hash_key(api_key)
        
        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()
        
        key_data = ApiKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at
        )
        
        # Load existing keys and add new one
        keys = self.storage.load_keys()
        keys[key_id] = key_data
        
        if self.storage.save_keys(keys):
            logger.info(f"Created new API key '{name}' with ID {key_id}")
            return api_key, key_id
        else:
            raise RuntimeError("Failed to save API key")
    
    def validate_key(self, api_key: str) -> Optional[ApiKey]:
        """Validate an API key."""
        return self.validator.validate_key(api_key)
    
    def revoke_key(self, key_id: str) -> bool:
        """Revoke an API key by setting it inactive."""
        keys = self.storage.load_keys()
        
        if key_id in keys:
            keys[key_id].is_active = False
            if self.storage.save_keys(keys):
                logger.info(f"Revoked API key with ID {key_id}")
                return True
        
        return False
    
    def list_keys(self) -> List[Dict]:
        """List all API keys (without exposing the actual keys)."""
        keys = self.storage.load_keys()
        return [
            {
                "key_id": key_data.key_id,
                "name": key_data.name,
                "created_at": key_data.created_at,
                "expires_at": key_data.expires_at,
                "is_active": key_data.is_active,
                "usage_count": key_data.usage_count,
                "last_used": key_data.last_used
            }
            for key_data in keys.values()
        ]
    
    def cleanup_expired_keys(self) -> int:
        """Remove expired keys from storage."""
        keys = self.storage.load_keys()
        expired_count = 0
        current_time = datetime.now()
        
        keys_to_remove = []
        for key_id, key_data in keys.items():
            if key_data.expires_at:
                expires_at = datetime.fromisoformat(key_data.expires_at)
                if current_time > expires_at:
                    keys_to_remove.append(key_id)
                    expired_count += 1
        
        for key_id in keys_to_remove:
            del keys[key_id]
        
        if expired_count > 0:
            self.storage.save_keys(keys)
            logger.info(f"Cleaned up {expired_count} expired API keys")
        
        return expired_count
