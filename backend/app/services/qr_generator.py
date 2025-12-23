"""
QR Code Generator Service for LIBER
Generates QR codes for venues to share with customers
"""
import io
import base64
import os
from typing import Optional
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image
from flask import current_app


class QRGeneratorService:
    """
    Service for generating branded QR codes for venues.
    Creates QR codes that link to the venue's sommelier chat.
    """
    
    def __init__(self):
        self.frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:5173')
        self.qr_storage_path = os.path.join(current_app.root_path, '..', 'static', 'qrcodes')
        
        # Ensure storage directory exists
        os.makedirs(self.qr_storage_path, exist_ok=True)
    
    def generate_for_venue(
        self, 
        venue, 
        force_regenerate: bool = False
    ) -> str:
        """
        Generate a QR code for a venue.
        
        Args:
            venue: Venue model instance
            force_regenerate: Force regeneration even if exists
            
        Returns:
            URL/path to the QR code image
        """
        filename = f"qr_{venue.slug}.png"
        filepath = os.path.join(self.qr_storage_path, filename)
        
        # Check if already exists
        if os.path.exists(filepath) and not force_regenerate:
            return f"/static/qrcodes/{filename}"
        
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
        
        # Save the image
        img.save(filepath)
        
        return f"/static/qrcodes/{filename}"
    
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
        Generate a high-quality printable QR code.
        
        Args:
            venue: Venue model instance
            size: 'small', 'medium', 'large'
            
        Returns:
            Path to high-res QR code
        """
        sizes = {
            'small': {'box_size': 15, 'border': 2},   # Good for business cards
            'medium': {'box_size': 25, 'border': 3},  # Good for table tents
            'large': {'box_size': 40, 'border': 4}    # Good for posters
        }
        
        params = sizes.get(size, sizes['medium'])
        
        filename = f"qr_{venue.slug}_{size}.png"
        filepath = os.path.join(self.qr_storage_path, filename)
        
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
        
        img.save(filepath, dpi=(300, 300))
        
        return f"/static/qrcodes/{filename}"
    
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

