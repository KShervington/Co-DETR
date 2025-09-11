#!/usr/bin/env python3
"""
API Key Management CLI Tool for Co-DETR

Command-line utility for generating, listing, and managing API keys.
Usage examples:
    python manage_api_keys.py create "My API Key"
    python manage_api_keys.py create "Test Key" --expires-days 30
    python manage_api_keys.py list
    python manage_api_keys.py revoke <key_id>
    python manage_api_keys.py cleanup
"""

import argparse
import sys
import logging
from datetime import datetime
from auth import ApiKeyManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_key(args):
    """Create a new API key."""
    try:
        manager = ApiKeyManager(args.storage_file)
        api_key, key_id = manager.create_key(args.name, args.expires_days)
        
        print("✅ API Key Created Successfully!")
        print("=" * 50)
        print(f"Key ID: {key_id}")
        print(f"Name: {args.name}")
        print(f"API Key: {api_key}")
        if args.expires_days:
            expires_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Expires: {expires_date} (in {args.expires_days} days)")
        else:
            print("Expires: Never")
        print("=" * 50)
        print("⚠️  IMPORTANT: Save this API key securely!")
        print("   You will NOT be able to retrieve it again.")
        print("   This key is required for API authentication.")
        
    except Exception as e:
        print(f"❌ Failed to create API key: {e}")
        sys.exit(1)

def list_keys(args):
    """List all API keys."""
    try:
        manager = ApiKeyManager(args.storage_file)
        keys = manager.list_keys()
        
        if not keys:
            print("📝 No API keys found.")
            return
        
        print(f"📋 Found {len(keys)} API key(s):")
        print("=" * 80)
        
        for key_data in keys:
            status = "🟢 Active" if key_data['is_active'] else "🔴 Inactive"
            created = datetime.fromisoformat(key_data['created_at']).strftime('%Y-%m-%d %H:%M')
            
            expires = "Never"
            if key_data['expires_at']:
                expires_dt = datetime.fromisoformat(key_data['expires_at'])
                expires = expires_dt.strftime('%Y-%m-%d %H:%M')
                if datetime.now() > expires_dt:
                    status = "⏰ Expired"
            
            last_used = "Never"
            if key_data['last_used']:
                last_used = datetime.fromisoformat(key_data['last_used']).strftime('%Y-%m-%d %H:%M')
            
            print(f"Key ID: {key_data['key_id']}")
            print(f"Name: {key_data['name']}")
            print(f"Status: {status}")
            print(f"Created: {created}")
            print(f"Expires: {expires}")
            print(f"Usage Count: {key_data['usage_count']}")
            print(f"Last Used: {last_used}")
            print("-" * 80)
        
    except Exception as e:
        print(f"❌ Failed to list API keys: {e}")
        sys.exit(1)

def revoke_key(args):
    """Revoke an API key."""
    try:
        manager = ApiKeyManager(args.storage_file)
        
        if manager.revoke_key(args.key_id):
            print(f"✅ API key {args.key_id} has been revoked successfully.")
        else:
            print(f"❌ API key {args.key_id} not found or already inactive.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to revoke API key: {e}")
        sys.exit(1)

def cleanup_keys(args):
    """Clean up expired API keys."""
    try:
        manager = ApiKeyManager(args.storage_file)
        expired_count = manager.cleanup_expired_keys()
        
        if expired_count > 0:
            print(f"✅ Cleaned up {expired_count} expired API key(s).")
        else:
            print("📝 No expired API keys found.")
            
    except Exception as e:
        print(f"❌ Failed to cleanup API keys: {e}")
        sys.exit(1)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Co-DETR API Key Management Tool",
        epilog="For more information, see the API documentation."
    )
    
    parser.add_argument(
        '--storage-file',
        default='auth/api_keys.json',
        help='Path to API key storage file (default: auth/api_keys.json)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new API key')
    create_parser.add_argument('name', help='Human-readable name for the API key')
    create_parser.add_argument(
        '--expires-days',
        type=int,
        help='Number of days until the key expires (optional)'
    )
    create_parser.set_defaults(func=create_key)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all API keys')
    list_parser.set_defaults(func=list_keys)
    
    # Revoke command
    revoke_parser = subparsers.add_parser('revoke', help='Revoke an API key')
    revoke_parser.add_argument('key_id', help='ID of the key to revoke')
    revoke_parser.set_defaults(func=revoke_key)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove expired API keys')
    cleanup_parser.set_defaults(func=cleanup_keys)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the command
    args.func(args)

if __name__ == '__main__':
    main()
