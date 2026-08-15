"""
SSRF (Server-Side Request Forgery) protection
MIR Samozanyatykh v8.4.1 - Security Hardened
ANO TsPS INN 9724016805
"""

import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional, Set

from app.core.logging import logger


class SSRFProtector:
    """SSRF protection with URL validation and IP filtering"""

    # Blocked IP ranges (private, loopback, link-local, metadata)
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("10.0.0.0/8"),        # Private
        ipaddress.ip_network("172.16.0.0/12"),     # Private
        ipaddress.ip_network("192.168.0.0/16"),    # Private
        ipaddress.ip_network("169.254.0.0/16"),    # Link-local
        ipaddress.ip_network("::1/128"),           # IPv6 loopback
        ipaddress.ip_network("fc00::/7"),          # IPv6 private
        ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
        ipaddress.ip_network("0.0.0.0/8"),         # Current network
        ipaddress.ip_network("::/128"),            # Unspecified
    ]

    # Blocked host patterns
    BLOCKED_HOSTS = {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
        "metadata.google.internal",
        "metadata",
        "169.254.169.254",  # AWS/Azure/GCP metadata
        "100.100.100.200",  # Alibaba metadata
    }

    # Blocked schemes
    ALLOWED_SCHEMES = {"http", "https"}

    # Blocked ports
    BLOCKED_PORTS = {22, 23, 25, 53, 110, 143, 3306, 3389, 5432, 6379, 27017}

    @classmethod
    def validate_url(cls, url: str, allow_internal: bool = False) -> tuple[bool, Optional[str]]:
        """
        Validate URL against SSRF protection rules

        Returns:
            (is_valid, error_message)
        """
        if not url:
            return False, "URL is required"

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Invalid URL format"

        # Check scheme
        scheme = parsed.scheme.lower()
        if scheme not in cls.ALLOWED_SCHEMES:
            return False, f"Scheme '{scheme}' not allowed. Use http or https"

        # Check port
        port = parsed.port
        if port and port in cls.BLOCKED_PORTS:
            return False, f"Port {port} is blocked"

        # Get hostname
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid hostname"

        hostname_lower = hostname.lower()

        # Check blocked hosts
        if hostname_lower in cls.BLOCKED_HOSTS:
            return False, f"Host '{hostname}' is blocked"

        # Check for metadata IP patterns
        if re.match(r"^169\.254\.\d+\.\d+$", hostname) or            re.match(r"^100\.\d+\.\d+\.\d+$", hostname):
            return False, "Metadata IP range is blocked"

        # Resolve and check IP
        if not allow_internal:
            try:
                import socket
                # Try to resolve hostname
                try:
                    addr_info = socket.getaddrinfo(hostname, None)
                    for _, _, _, _, sockaddr in addr_info:
                        ip_str = sockaddr[0]
                        try:
                            ip = ipaddress.ip_address(ip_str)
                            for network in cls.BLOCKED_NETWORKS:
                                if ip in network:
                                    return False, f"IP {ip_str} is in blocked range"
                        except ValueError:
                            continue
                except socket.gaierror:
                    # Cannot resolve - might be invalid or internal DNS
                    # Allow if it looks like a valid public domain
                    if not re.match(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$", hostname_lower):
                        return False, "Invalid hostname format"
            except Exception as e:
                logger.warning(f"SSRF validation error for {url}: {e}")
                return False, "URL validation failed"

        # Check for URL tricks
        if "@" in parsed.path or "@" in (parsed.query or ""):
            return False, "URL contains credentials"

        if ".." in parsed.path:
            return False, "Path traversal detected"

        # Check URL length
        if len(url) > 2048:
            return False, "URL too long"

        return True, None

    @classmethod
    def validate_webhook_url(cls, url: str) -> tuple[bool, Optional[str]]:
        """Validate webhook URL with stricter rules"""
        is_valid, error = cls.validate_url(url, allow_internal=False)
        if not is_valid:
            return False, error

        # Additional webhook-specific checks
        parsed = urlparse(url)

        # Require HTTPS for webhooks
        if parsed.scheme != "https":
            return False, "Webhooks must use HTTPS"

        # Check for common SSRF bypasses
        hostname = parsed.hostname.lower()
        if hostname.startswith("0x") or hostname.startswith("0o"):
            return False, "Numeric IP encoding not allowed"

        return True, None


ssrf_protector = SSRFProtector()
