"""
Supabase Storage Service for LIBER
Handles file uploads and management in Supabase Storage buckets
"""
import io
import logging
from typing import Optional
from flask import current_app
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """
    Service for managing files in Supabase Storage.
    Handles uploads, downloads, and URL generation for both public and private buckets.
    """
    
    def __init__(self):
        """Initialize Supabase Storage client"""
        self.supabase_url = current_app.config.get('SUPABASE_URL', '')
        self.service_role_key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY', '')
        
        if not self.supabase_url or not self.service_role_key:
            logger.warning("Supabase Storage not configured - SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.supabase_url, self.service_role_key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
    
    def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: bytes,
        content_type: str = 'image/png',
        upsert: bool = True
    ) -> Optional[str]:
        """
        Upload a file to Supabase Storage.
        
        Args:
            bucket: Name of the storage bucket
            file_path: Path/filename in the bucket (e.g., 'qr_ristorante-mario.png')
            file_data: File content as bytes
            content_type: MIME type of the file
            upsert: If True, overwrite existing file; if False, fail if exists
            
        Returns:
            Public URL if bucket is public, or None if private (use get_signed_url instead)
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return None
        
        try:
            # Upload file - supabase-py returns dict with 'data' and 'error'
            response = self.client.storage.from_(bucket).upload(
                path=file_path,
                file=file_data,
                file_options={
                    'content-type': content_type,
                    'upsert': upsert
                }
            )
            
            # Check if upload was successful
            if response and isinstance(response, dict):
                if response.get('error'):
                    logger.error(f"Upload error: {response['error']}")
                    return None
                # Upload successful
                logger.info(f"File uploaded to {bucket}/{file_path}")
                
                # Always try to get public URL (will return URL even for private buckets, but won't work)
                # For private buckets, caller should use get_signed_url instead
                try:
                    public_url_response = self.client.storage.from_(bucket).get_public_url(file_path)
                    # get_public_url returns the URL string directly
                    if isinstance(public_url_response, str):
                        return public_url_response
                    elif isinstance(public_url_response, dict) and 'publicUrl' in public_url_response:
                        return public_url_response['publicUrl']
                    return public_url_response
                except Exception as e:
                    logger.debug(f"Could not get public URL (bucket may be private): {e}")
                    # Bucket is private, return None (caller should use get_signed_url)
                    return None
            else:
                logger.error(f"Failed to upload file to {bucket}/{file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {e}", exc_info=True)
            return None
    
    def get_signed_url(
        self,
        bucket: str,
        file_path: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generate a signed URL for a file in a private bucket.
        
        Args:
            bucket: Name of the storage bucket
            file_path: Path/filename in the bucket
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL string or None if error
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return None
        
        try:
            # create_signed_url returns dict with 'signedUrl' or 'signedURL' and 'error'
            response = self.client.storage.from_(bucket).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            
            if response and isinstance(response, dict):
                if response.get('error'):
                    logger.error(f"Signed URL error: {response['error']}")
                    return None
                # Try different key names
                signed_url = response.get('signedUrl') or response.get('signedURL') or response.get('signed_url')
                if signed_url:
                    return signed_url
            elif response and isinstance(response, str):
                # Some versions might return the URL directly
                return response
            
            logger.error(f"Failed to create signed URL for {bucket}/{file_path}: unexpected response format")
            return None
                
        except Exception as e:
            logger.error(f"Error creating signed URL: {e}", exc_info=True)
            return None
    
    def get_public_url(self, bucket: str, file_path: str) -> Optional[str]:
        """
        Get public URL for a file in a public bucket.
        
        Args:
            bucket: Name of the storage bucket
            file_path: Path/filename in the bucket
            
        Returns:
            Public URL string or None if error
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return None
        
        try:
            return self.client.storage.from_(bucket).get_public_url(file_path)
        except Exception as e:
            logger.error(f"Error getting public URL: {e}", exc_info=True)
            return None
    
    def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage.
        
        Args:
            bucket: Name of the storage bucket
            file_path: Path/filename in the bucket
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return False
        
        try:
            response = self.client.storage.from_(bucket).remove([file_path])
            logger.info(f"File deleted from {bucket}/{file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from Supabase Storage: {e}", exc_info=True)
            return False
    
    def file_exists(self, bucket: str, file_path: str) -> bool:
        """
        Check if a file exists in Supabase Storage.
        
        Args:
            bucket: Name of the storage bucket
            file_path: Path/filename in the bucket
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.client:
            return False
        
        try:
            # Extract directory and filename
            path_parts = file_path.rsplit('/', 1)
            if len(path_parts) == 2:
                directory = path_parts[0]
                filename = path_parts[1]
            else:
                directory = ''
                filename = file_path
            
            # List files in the directory (or root if no directory)
            response = self.client.storage.from_(bucket).list(path=directory if directory else None)
            
            if response and isinstance(response, dict):
                files = response.get('data', []) if 'data' in response else []
            elif isinstance(response, list):
                files = response
            else:
                files = []
            
            # Check if file exists in the list
            for file_item in files:
                if isinstance(file_item, dict) and file_item.get('name') == filename:
                    return True
                elif isinstance(file_item, str) and file_item == filename:
                    return True
            
            return False
        except Exception as e:
            logger.debug(f"Error checking file existence: {e}")
            return False

