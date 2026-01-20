-- Add WiFi IP verification fields to venues table
ALTER TABLE venues ADD COLUMN IF NOT EXISTS wifi_ip_address VARCHAR(45) DEFAULT NULL;
ALTER TABLE venues ADD COLUMN IF NOT EXISTS wifi_ip_range VARCHAR(100) DEFAULT NULL;
ALTER TABLE venues ADD COLUMN IF NOT EXISTS wifi_verification_enabled BOOLEAN DEFAULT FALSE;

-- Add comments for documentation
COMMENT ON COLUMN venues.wifi_ip_address IS 'Single IP address of the venue WiFi (IPv4 or IPv6)';
COMMENT ON COLUMN venues.wifi_ip_range IS 'IP range in CIDR notation (e.g., 192.168.1.0/24) or comma-separated IPs';
COMMENT ON COLUMN venues.wifi_verification_enabled IS 'Enable WiFi IP verification for QR code access';
