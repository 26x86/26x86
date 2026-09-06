"""Explicit live-host DHCP and authenticated TSS reachability diagnostics."""
from __future__ import annotations
import json
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import socket
import signal
import subprocess
import time
import urllib.request

RUN = Path("/run")
_dhcp_process = None


def stop_dhcp():
    if _dhcp_process is None or _dhcp_process.poll() is not None:
        return
    os.killpg(_dhcp_process.pid, signal.SIGTERM)
    try:
        _dhcp_process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(_dhcp_process.pid, signal.SIGKILL)
        _dhcp_process.wait(timeout=2)


def require_live_host():
    if (RUN / "venfire-live-host").read_text() != "VENFIRE_RAM_LIVE_HOST\n":
        raise RuntimeError("Network configuration is confined to the 26x86 RAM live host")


def interfaces(root=Path("/sys/class/net")) -> list[dict]:
    result = []
    for path in sorted(root.iterdir()):
        if (not re.fullmatch(r"[A-Za-z0-9_.:-]{1,15}", path.name) or path.name == "lo" or
                (path / "wireless").exists() or (path / "type").read_text().strip() != "1"):
            continue
        try:
            carrier = (path / "carrier").read_text().strip() == "1"
        except OSError:
            carrier = False
        result.append({"name": path.name, "carrier": carrier})
    return result


def configure_dhcp(interface: str, emit=print) -> dict:
    global _dhcp_process
    require_live_host()
    if interface not in {item["name"] for item in interfaces()}:
        raise ValueError("Select a currently enumerated wired interface")
    stop_dhcp()
    lease = RUN / "venfire-network-lease.json"
    if lease.exists():
        previous = json.loads(lease.read_text())
        old_interface = previous.get("interface")
        if old_interface in {item["name"] for item in interfaces()}:
            subprocess.run(["/bin/busybox", "route", "del", "default", "dev", old_interface],
                           check=False, capture_output=True, timeout=5)
            if old_interface != interface:
                subprocess.run(["/bin/busybox", "ifconfig", old_interface, "0.0.0.0"],
                               check=False, capture_output=True, timeout=5)
        lease.unlink()
    (RUN / "venfire-network-interface").write_text(interface + "\n")
    subprocess.run(["/bin/busybox", "ip", "link", "set", "dev", interface, "up"], check=True, timeout=5)
    log = RUN / "venfire-network-dhcp.log"
    with log.open("w") as output:
        _dhcp_process = subprocess.Popen(["/bin/busybox", "udhcpc", "-f", "-n", "-i", interface,
            "-s", "/opt/venfire/usb/dhcp_hook.py", "-t", "5", "-T", "3"],
            stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    started = time.monotonic()
    # Nested TCG executes the Python lease hook slowly; retain a finite bound
    # while allowing actual address/routing application to finish.
    deadline = started + 90
    while time.monotonic() < deadline:
        if lease.exists():
            details = json.loads(lease.read_text())
            if details.get("interface") == interface:
                details["elapsed_seconds"] = round(time.monotonic() - started, 3)
                emit("VENFIRE_USB|DHCP|PASS")
                emit("Live RAM network configured on " + interface + ": " + details["address"] +
                     " (" + str(details["elapsed_seconds"]) + " seconds)")
                return details
        if _dhcp_process.poll() is not None:
            break
        time.sleep(0.2)
    stop_dhcp()
    raise RuntimeError("DHCP did not configure the selected interface: " + log.read_text()[-2048:])


def check_helper(emit=print) -> bool:
    helper = Path("/usr/bin/venfire-tss-request")
    if not helper.is_file():
        emit("Restore request encoder: not included in this build.")
        return False
    result = subprocess.run([str(helper)], text=True, capture_output=True, timeout=10)
    if result.returncode != 2 or "usage: venfire-tss-request" not in result.stderr:
        raise RuntimeError("Restore helper or its runtime libraries did not load correctly")
    emit("VENFIRE_USB|RESTORE_HELPER|READY")
    return True


def check_tss(emit=print) -> dict:
    # Reuse the exact pinned Apple-root, normal hostname-validation and
    # redirect-rejection policy used by the real personalization client.
    from venfire.personalization import _tss_opener, TSS_URL
    addresses = sorted({item[4][0] for item in socket.getaddrinfo("gs.apple.com", 443, type=socket.SOCK_STREAM)})
    request = urllib.request.Request(TSS_URL, method="GET", headers={"User-Agent": "26x86-USB/0.2.0"})
    with _tss_opener().open(request, timeout=30) as response:
        body = response.read(65537)
        if response.url != TSS_URL or response.status != 200 or len(body) > 65536:
            raise RuntimeError("Unexpected TSS reachability response")
        status = re.search(rb"(?:^|&)STATUS=([0-9]+)(?:&|$)", body)
        if not status:
            raise RuntimeError("HTTPS endpoint did not return a TSS protocol status")
    report = {"schema": 1, "layer": "live-host DNS/TCP/TLS/HTTP",
              "checked_utc": datetime.now(timezone.utc).isoformat(),
              "endpoint": TSS_URL, "resolved_addresses": addresses, "http_status": 200,
              "tls_certificate_and_hostname_verified": True, "redirects_allowed": False,
              "tss_protocol_status": int(status[1]), "request_method": "GET",
              "ticket_requested": False, "ticket_received": False, "macos_boot_verified": False}
    (RUN / "venfire-network-tss.json").write_text(json.dumps(report, indent=2) + "\n")
    emit("VENFIRE_USB|TSS_HTTPS|PASS")
    emit("Authenticated TSS HTTPS response received; protocol status=" + str(report["tss_protocol_status"]))
    emit("Reachability only. This check requests no ticket and proves no macOS boot.")
    emit(json.dumps(report, sort_keys=True))
    return report


def diagnostics(interface: str, emit=print) -> dict:
    lease = configure_dhcp(interface, emit)
    helper = check_helper(emit)
    return {"dhcp": lease, "restore_helper_ready": helper, "tss": check_tss(emit)}


def automatic_diagnostics(emit=print) -> dict:
    available = interfaces()
    candidates = [item for item in available if item["carrier"]] or available
    if len(candidates) != 1:
        raise ValueError("Network self-test requires exactly one wired interface candidate")
    return diagnostics(candidates[0]["name"], emit)
