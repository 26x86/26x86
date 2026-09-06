#!/usr/bin/python3
"""Apply a lease only to the interface explicitly selected in the live menu."""
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def lease_parameters(env):
    interface = env.get("interface", "")
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,15}", interface):
        raise ValueError("Invalid DHCP interface")
    address = str(ipaddress.IPv4Address(env["ip"]))
    prefix = ipaddress.IPv4Network("0.0.0.0/" + env["subnet"]).prefixlen
    routers = [str(ipaddress.IPv4Address(value)) for value in env.get("router", "").split()]
    dns = [str(ipaddress.ip_address(value)) for value in env.get("dns", "").split()]
    if not routers or not dns:
        raise ValueError("DHCP lease must supply a default gateway and DNS server")
    return {"interface": interface, "address": address + "/" + str(prefix),
            "netmask": str(ipaddress.IPv4Network("0.0.0.0/" + str(prefix)).netmask),
            "gateway": routers[0], "dns": dns}


def apply(event, env):
    from network import require_live_host, RUN
    require_live_host()
    interface = env.get("interface", "")
    if (RUN / "venfire-network-interface").read_text().strip() != interface:
        raise ValueError("DHCP event is outside the explicitly selected interface")
    if event not in ("bound", "renew"):
        return
    lease = lease_parameters(env)
    # BusyBox ipaddr implements add/delete, not iproute2's address replace.
    # ifconfig updates the selected interface's IPv4 lease idempotently.
    subprocess.run(["/bin/busybox", "ifconfig", interface, lease["address"].split("/")[0],
                    "netmask", lease["netmask"], "up"], check=True, timeout=5)
    # The ioctl route applet avoids a full netlink interface dump in this small
    # initramfs. Replace the selected interface's previous gateway on renew.
    subprocess.run(["/bin/busybox", "route", "del", "default", "dev", interface],
                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    subprocess.run(["/bin/busybox", "route", "add", "default", "gw", lease["gateway"], "dev", interface],
                   check=True, timeout=5)
    Path("/etc/resolv.conf").write_text("".join("nameserver " + value + "\n" for value in lease["dns"]) +
                                      "options timeout:3 attempts:1\n")
    temporary = RUN / "venfire-network-lease.new.json"
    temporary.write_text(json.dumps(lease) + "\n")
    temporary.replace(RUN / "venfire-network-lease.json")


if __name__ == "__main__":
    print("VENFIRE_DHCP_HOOK|BEGIN|" + sys.argv[1], flush=True)
    apply(sys.argv[1], os.environ)
    print("VENFIRE_DHCP_HOOK|DONE|" + sys.argv[1], flush=True)
