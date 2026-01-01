"""
QR Code Generator Service for LIBER
Generates QR codes for venues to share with customers
"""
import io
import base64
import os
import logging
from typing import Optional
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image
from flask import current_app
from app.services.supabase_storage import SupabaseStorageService

logger = logging.getLogger(__name__)


class QRGeneratorService:
    """
    Service for generating branded QR codes for venues.
    Creates QR codes that link to the venue's sommelier chat.
    Stores QR codes in Supabase Storage (private bucket).
    """
    
    def __init__(self):
        self.frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        self.storage_service = SupabaseStorageService()
        self.qr_bucket = current_app.config.get('SUPABASE_STORAGE_BUCKET_QRCODES', 'qrcodes')
        
        # Fallback: ensure local storage directory exists (for development/fallback)
        self.qr_storage_path = os.path.join(current_app.root_path, '..', 'static', 'qrcodes')
        os.makedirs(self.qr_storage_path, exist_ok=True)
    
    def generate_for_venue(
        self, 
        venue, 
        force_regenerate: bool = False
    ) -> str:
        """
        Generate a QR code for a venue and upload to Supabase Storage.
        Maintains identity: qr_{venue.slug}.png
        
        Args:
            venue: Venue model instance
            force_regenerate: Force regeneration even if exists
            
        Returns:
            Storage path (not URL, since bucket is private) - format: "qrcodes/qr_{venue.slug}.png"
        """
        # Maintain identity: qr_{venue.slug}.png
        filename = f"qr_{venue.slug}.png"
        storage_path = filename  # Store at root of bucket
        
        # Check if already exists (only if not forcing regeneration)
        if not force_regenerate and self.storage_service.file_exists(self.qr_bucket, storage_path):
            # Return storage path (not URL, since bucket is private)
            return f"{self.qr_bucket}/{storage_path}"
        
        # Generate the URL
        venue_url = f"{self.frontend_url}/v/{venue.slug}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2
        )
        qr.add_data(venue_url)
        qr.make(fit=True)
        
        # Get venue's primary color or default burgundy
        primary_color = venue.primary_color or '#722F37'
        
        # Convert hex to RGB
        fill_color = self._hex_to_rgb(primary_color)
        back_color = (255, 255, 255)  # White background
        
        # Create styled image
        try:
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(
                    back_color=back_color,
                    front_color=fill_color
                )
            )
        except Exception:
            # Fallback to simple QR if styled fails
            img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        # Add branding/logo if available
        if venue.logo_url:
            img = self._add_logo(img, venue.logo_url)
        
        # Convert image to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        file_data = buffer.getvalue()
        
        # Upload to Supabase Storage (private bucket)
        public_url = self.storage_service.upload_file(
            bucket=self.qr_bucket,
            file_path=storage_path,
            file_data=file_data,
            content_type='image/png',
            upsert=True
        )
        
        # Since bucket is private, public_url will be None
        # Return storage path identifier instead
        if public_url is None:
            # Upload succeeded but bucket is private, return storage path
            logger.info(f"QR code uploaded to Supabase Storage: {self.qr_bucket}/{storage_path}")
            return f"{self.qr_bucket}/{storage_path}"
        else:
            # Should not happen for private bucket, but handle anyway
            logger.warning(f"QR code uploaded but got public URL (bucket may be public): {public_url}")
            return f"{self.qr_bucket}/{storage_path}"
    
    def generate_base64(self, venue) -> str:
        """
        Generate a QR code and return as base64 encoded string.
        Useful for inline display.
        
        Args:
            venue: Venue model instance
            
        Returns:
            Base64 encoded PNG image
        """
        venue_url = f"{self.frontend_url}/v/{venue.slug}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=2
        )
        qr.add_data(venue_url)
        qr.make(fit=True)
        
        primary_color = venue.primary_color or '#722F37'
        fill_color = self._hex_to_rgb(primary_color)
        
        img = qr.make_image(fill_color=fill_color, back_color=(255, 255, 255))
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def generate_printable(
        self, 
        venue, 
        size: str = 'medium'
    ) -> str:
        """
        Generate a high-quality printable QR code and upload to Supabase Storage.
        Maintains identity: qr_{venue.slug}_{size}.png
        
        Args:
            venue: Venue model instance
            size: 'small', 'medium', 'large'
            
        Returns:
            Storage path (not URL, since bucket is private) - format: "qrcodes/qr_{venue.slug}_{size}.png"
        """
        sizes = {
            'small': {'box_size': 15, 'border': 2},   # Good for business cards
            'medium': {'box_size': 25, 'border': 3},  # Good for table tents
            'large': {'box_size': 40, 'border': 4}    # Good for posters
        }
        
        params = sizes.get(size, sizes['medium'])
        
        # Maintain identity: qr_{venue.slug}_{size}.png
        filename = f"qr_{venue.slug}_{size}.png"
        storage_path = filename  # Store at root of bucket
        
        venue_url = f"{self.frontend_url}/v/{venue.slug}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=params['box_size'],
            border=params['border']
        )
        qr.add_data(venue_url)
        qr.make(fit=True)
        
        primary_color = venue.primary_color or '#722F37'
        fill_color = self._hex_to_rgb(primary_color)
        
        try:
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer(),
                color_mask=SolidFillColorMask(
                    back_color=(255, 255, 255),
                    front_color=fill_color
                )
            )
        except Exception:
            img = qr.make_image(fill_color=fill_color, back_color=(255, 255, 255))
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', dpi=(300, 300))
        buffer.seek(0)
        file_data = buffer.getvalue()
        
        # Upload to Supabase Storage (private bucket)
        self.storage_service.upload_file(
            bucket=self.qr_bucket,
            file_path=storage_path,
            file_data=file_data,
            content_type='image/png',
            upsert=True
        )
        
        logger.info(f"Printable QR code uploaded to Supabase Storage: {self.qr_bucket}/{storage_path}")
        return f"{self.qr_bucket}/{storage_path}"
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _add_logo(self, qr_img, logo_url: str) -> Image:
        """
        Add a logo to the center of the QR code.
        
        Args:
            qr_img: QR code image
            logo_url: URL to the logo
            
        Returns:
            QR image with logo
        """
        try:
            # This would need to download the logo from URL
            # For now, we'll skip logo embedding
            return qr_img
        except Exception:
            return qr_img

