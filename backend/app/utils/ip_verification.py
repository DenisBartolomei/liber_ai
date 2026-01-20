"""
IP Verification Utility
Helper functions to verify if a client IP matches venue WiFi configuration.
Supports both IPv4 and IPv6.
"""
import ipaddress
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Get the real client IP address from Flask request.
    Handles proxies and load balancers.
    Supports both IPv4 and IPv6.
    
    Args:
        request: Flask request object
        
    Returns:
        str: Client IP address or None
    """
    # Check for forwarded headers (common in production with proxies/load balancers)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, take the first one
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        logger.debug(f"Got IP from X-Forwarded-For: {ip}")
        return ip
    
    if request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
        logger.debug(f"Got IP from X-Real-IP: {ip}")
        return ip
    
    # Fallback to remote_addr
    ip = request.remote_addr
    logger.debug(f"Got IP from remote_addr: {ip}")
    return ip


def is_valid_ip(ip_string):
    """
    Check if a string is a valid IP address (IPv4 or IPv6).
    
    Args:
        ip_string: String to check
        
    Returns:
        bool: True if valid IP, False otherwise
    """
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def get_ip_version(ip_string):
    """
    Get the IP version (4 or 6) of an IP address.
    
    Args:
        ip_string: IP address string
        
    Returns:
        int: 4 for IPv4, 6 for IPv6, or None if invalid
    """
    try:
        ip = ipaddress.ip_address(ip_string)
        return ip.version
    except ValueError:
        return None


def ip_in_range(ip_address, ip_range):
    """
    Check if an IP address is within a given range.
    Supports both IPv4 and IPv6.
    Supports:
    - Single IP: "192.168.1.1" or "2001:0db8::1"
    - CIDR notation: "192.168.1.0/24" or "2001:0db8::/32"
    - Comma-separated IPs: "192.168.1.1,192.168.1.2"
    
    Args:
        ip_address: The IP address to check (str)
        ip_range: The IP range/address to check against (str)
        
    Returns:
        bool: True if IP is in range, False otherwise
    """
    if not ip_address or not ip_range:
        return False
    
    try:
        client_ip = ipaddress.ip_address(ip_address)
    except ValueError:
        logger.warning(f"Invalid IP address: {ip_address}")
        return False
    
    # Handle comma-separated IPs
    if ',' in ip_range:
        ip_list = [ip.strip() for ip in ip_range.split(',')]
        for single_ip in ip_list:
            if ip_matches(client_ip, single_ip):
                return True
        return False
    
    # Handle CIDR notation
    if '/' in ip_range:
        try:
            # Try to parse as network (supports both IPv4 and IPv6)
            network = ipaddress.ip_network(ip_range, strict=False)
            # Ensure client IP is same version as network
            if client_ip.version == network.version:
                return client_ip in network
            else:
                logger.warning(f"IP version mismatch: client is IPv{client_ip.version}, network is IPv{network.version}")
                return False
        except ValueError:
            logger.warning(f"Invalid CIDR notation: {ip_range}")
            return False
    
    # Handle single IP
    return ip_matches(client_ip, ip_range)


def ip_matches(ip, pattern):
    """
    Check if an IP matches a pattern (exact match or CIDR).
    Supports both IPv4 and IPv6.
    
    Args:
        ip: ipaddress.IPv4Address or ipaddress.IPv6Address
        pattern: IP address string or CIDR notation
        
    Returns:
        bool: True if matches, False otherwise
    """
    try:
        if '/' in pattern:
            network = ipaddress.ip_network(pattern, strict=False)
            # Ensure IP versions match
            if ip.version == network.version:
                return ip in network
            else:
                return False
        else:
            pattern_ip = ipaddress.ip_address(pattern)
            # Ensure IP versions match
            if ip.version == pattern_ip.version:
                return ip == pattern_ip
            else:
                return False
    except ValueError:
        return False


def verify_wifi_access(venue, client_ip):
    """
    Verify if client IP matches venue WiFi configuration.
    Supports both IPv4 and IPv6.
    
    Args:
        venue: Venue model instance
        client_ip: Client IP address (str)
        
    Returns:
        Tuple (is_allowed: bool, message: str)
    """
    # If WiFi verification is disabled, allow access
    if not venue.wifi_verification_enabled:
        return True, "WiFi verification disabled"
    
    # If no WiFi IP is configured, allow access (backward compatibility)
    if not venue.wifi_ip_address and not venue.wifi_ip_range:
        logger.warning(f"Venue {venue.id} has WiFi verification enabled but no IP configured")
        return True, "WiFi IP not configured"
    
    # Validate client IP
    if not is_valid_ip(client_ip):
        logger.warning(f"Invalid client IP: {client_ip}")
        return False, "Indirizzo IP non valido"
    
    client_ip_version = get_ip_version(client_ip)
    
    # Check single IP address
    if venue.wifi_ip_address:
        if is_valid_ip(venue.wifi_ip_address):
            venue_ip_version = get_ip_version(venue.wifi_ip_address)
            # Only compare if same IP version
            if client_ip_version == venue_ip_version:
                if ip_matches(ipaddress.ip_address(client_ip), venue.wifi_ip_address):
                    logger.info(f"Client IP {client_ip} (IPv{client_ip_version}) matches venue WiFi IP {venue.wifi_ip_address}")
                    return True, "IP matches WiFi configuration"
            else:
                logger.debug(f"IP version mismatch: client IPv{client_ip_version}, venue IPv{venue_ip_version}")
    
    # Check IP range
    if venue.wifi_ip_range:
        if ip_in_range(client_ip, venue.wifi_ip_range):
            logger.info(f"Client IP {client_ip} (IPv{client_ip_version}) matches venue WiFi range {venue.wifi_ip_range}")
            return True, "IP matches WiFi range"
    
    # IP doesn't match
    logger.warning(f"WiFi verification failed: client IP {client_ip} (IPv{client_ip_version}) doesn't match venue {venue.id} configuration")
    return False, "L'accesso è consentito solo quando sei connesso al WiFi del locale. Connettiti al WiFi e riprova."
