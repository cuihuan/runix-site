#!/usr/bin/env python3
"""Re-check the TLS claim /security makes, so the page cannot quietly go stale.

/security states that the hosts accept TLS 1.3 and 1.2 and refuse 1.0 and 1.1,
and invites the reader to verify it. A published security claim that stops
being true is worse than one never made, and TLS policy is set at the edge
rather than in this repository — nothing here would notice it changing.

Run periodically. Exits non-zero if reality has moved.

Note on method: macOS system curl links LibreSSL and fails --tlsv1.3 locally
even against a server that supports it, which reads as "not supported" and is
wrong. Python's ssl module is OpenSSL-backed, so it is used instead.
"""
import socket
import ssl
import sys

HOSTS = ["runixcloud.io", "api.router.runixcloud.io", "console.router.runixcloud.io"]
EXPECTED = {"TLSv1": False, "TLSv1.1": False, "TLSv1.2": True, "TLSv1.3": True}
VERSIONS = [("TLSv1", ssl.TLSVersion.TLSv1), ("TLSv1.1", ssl.TLSVersion.TLSv1_1),
            ("TLSv1.2", ssl.TLSVersion.TLSv1_2), ("TLSv1.3", ssl.TLSVersion.TLSv1_3)]

problems = []
for host in HOSTS:
    for name, version in VERSIONS:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.minimum_version = ctx.maximum_version = version
        except ValueError:
            print(f"  {host} {name}: local OpenSSL will not offer it — cannot test")
            continue
        try:
            with socket.create_connection((host, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as tls:
                    got = True, tls.version()
        except Exception:
            got = False, None
        ok = got[0] == EXPECTED[name]
        print(f"  {host:<32} {name:<8} {'accepted' if got[0] else 'refused':<9}"
              f"{'' if ok else '  <-- /security says otherwise'}")
        if not ok:
            problems.append(f"{host} {name}: "
                            f"{'accepted' if got[0] else 'refused'}, "
                            f"/security claims {'accepted' if EXPECTED[name] else 'refused'}")

if problems:
    print(f"\n{len(problems)} mismatch(es) between the live endpoints and /security:")
    for p in problems:
        print(f"  x {p}")
    sys.exit(1)
print("\n/security's TLS claim still holds")
