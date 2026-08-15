"""
SSRF protection for Mir Samozanyatykh v8.2
Blocks private IPs, metadata endpoints, validates redirects
"""

import ipaddress
import socket
from urllib.parse import urlparse
import requests

BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:127.0.0.0/104"),
]

METADATA_ENDPOINTS = [
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.azure.internal",
    "metadata.aws.internal",
    "100.100.100.200",
]


def is_private_ip(ip_str: str) -> bool:
    """Check if IP is private/blocked"""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return True
        return False
    except ValueError:
        return True


def validate_url(url: str, allow_redirects: bool = False) -> bool:
    """Validate URL for SSRF"""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    if hostname in METADATA_ENDPOINTS:
        return False

    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            ip_str = info[4][0]
            if is_private_ip(ip_str):
                return False
    except socket.gaierror:
        return False

    return True


def safe_request(
    url: str,
    method: str = "GET",
    max_redirects: int = 3,
    timeout: int = 10,
    max_size: int = 10 * 1024 * 1024,
    **kwargs
) -> requests.Response:
    """Make safe HTTP request with SSRF protection"""

    if not validate_url(url):
        raise ValueError(f"SSRF: URL blocked: {url}")

    response = requests.request(
        method,
        url,
        allow_redirects=False,
        timeout=timeout,
        stream=True,
        **kwargs
    )

    redirect_count = 0
    while response.is_redirect and redirect_count < max_redirects:
        redirect_url = response.headers.get("Location")
        if not redirect_url:
            break

        if not validate_url(redirect_url):
            raise ValueError(f"SSRF: Redirect blocked: {redirect_url}")

        response = requests.request(
            method,
            redirect_url,
            allow_redirects=False,
            timeout=timeout,
            stream=True,
            **kwargs
        )
        redirect_count += 1

    content = b""
    for chunk in response.iter_content(chunk_size=8192):
        content += chunk
        if len(content) > max_size:
            raise ValueError(f"Response too large (max {max_size} bytes)")

    response._content = content
    return response
