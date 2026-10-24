"""
resolver_dns — módulo compartido para todos los tools del workspace.

El router DNS local (192.168.80.1) falla de forma intermitente en consultas
IPv6 (AAAA) y en algunas cadenas CNAME (credly.com, getonbrd.cl). Este módulo:

1. Fuerza resolución IPv4 en todo el proceso (socket.getaddrinfo).
2. Añade un resolver de respaldo directo contra 1.1.1.1 / 8.8.8.8 (UDP, stdlib).
3. Expone ip_de(host) para pasar IPs a Chromium via --host-resolver-rules.

Uso:
    import resolver_dns
    resolver_dns.activar()
"""
from __future__ import annotations

import random
import socket
import struct

_orig_getaddrinfo = socket.getaddrinfo
_cache: dict[str, list[str]] = {}


def dns_a(host: str, servidor: str = "1.1.1.1", timeout: float = 5.0) -> list[str]:
    """Consulta DNS tipo A directa por UDP, solo stdlib."""
    tid = random.randint(0, 65535)
    q = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    for parte in host.split("."):
        q += bytes([len(parte)]) + parte.encode("ascii")
    q += b"\x00" + struct.pack(">HH", 1, 1)  # tipo A, clase IN

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        s.sendto(q, (servidor, 53))
        resp, _ = s.recvfrom(4096)

    _tid, flags, qd, an = struct.unpack(">HHHH", resp[:8])
    if not an:
        return []
    pos = 12
    for _ in range(qd):
        while resp[pos] != 0:
            pos += resp[pos] + 1
        pos += 5
    ips: list[str] = []
    for _ in range(an):
        if resp[pos] & 0xC0 == 0xC0:
            pos += 2
        else:
            while resp[pos] != 0:
                pos += resp[pos] + 1
            pos += 1
        tipo, _clase, _ttl, rdlen = struct.unpack(">HHIH", resp[pos : pos + 10])
        pos += 10
        if tipo == 1 and rdlen == 4:
            ips.append(socket.inet_ntoa(resp[pos : pos + 4]))
        pos += rdlen
    return ips


def _resolver_con_fallback(host: str) -> list[str]:
    ips = _cache.get(host)
    if ips:
        return ips
    for servidor in ("1.1.1.1", "8.8.8.8"):
        try:
            ips = dns_a(host, servidor)
            if ips:
                _cache[host] = ips
                return ips
        except OSError:
            continue
    return []


def _getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    except socket.gaierror:
        if isinstance(host, str) and family in (0, socket.AF_INET):
            ips = _resolver_con_fallback(host)
            if ips:
                try:
                    p = int(port)
                except (TypeError, ValueError):
                    p = 443
                return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ips[0], p))]
        raise


def activar() -> None:
    """Instala el resolver IPv4+fallback en el proceso actual."""
    socket.getaddrinfo = _getaddrinfo_ipv4


def ip_de(host: str) -> str | None:
    """Devuelve la IP del host (sistema o fallback DNS), para Chromium."""
    try:
        return _orig_getaddrinfo(host, 443, socket.AF_INET)[0][4][0]
    except OSError:
        ips = _resolver_con_fallback(host)
        return ips[0] if ips else None
