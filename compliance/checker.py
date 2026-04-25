#!/usr/bin/env python3
import subprocess, yaml
from datetime import datetime

INVENTORY = "inventory/campus.yaml"
REPORT_FILE = "compliance/report.txt"

def tcp_check(ns, ip, port, timeout=3):
    cmd = f"ip netns exec {ns} timeout {timeout} bash -c 'echo >/dev/tcp/{ip}/{port}' 2>/dev/null"
    return subprocess.run(cmd, shell=True).returncode == 0

def run_checks():
    with open(INVENTORY) as f:
        inv = yaml.safe_load(f)

    approved = inv['hq']['allowed_services']
    blocked  = ["192.168.0.99:22", "192.168.0.99:3389", "8.8.8.8:53"]

    report = [f"Compliance Report — {datetime.now()}", "=" * 50]
    all_pass = True

    for branch in inv['branches']:
        ns  = branch['namespace']
        bid = branch['name']
        report.append(f"\n── {bid} ({ns}) ──")
        print(f"\n── {bid} ({ns}) ──")

        for svc in approved:
            ip, port = svc.split(":")
            ok = tcp_check(ns, ip, int(port))
            status = "PASS ✓" if ok else "FAIL ✗"
            line = f"  [ALLOWED]  {svc:<25} {status}"
            print(line); report.append(line)
            if not ok: all_pass = False

        for svc in blocked:
            ip, port = svc.split(":")
            reached = tcp_check(ns, ip, int(port))
            ok = not reached
            status = "PASS ✓" if ok else "FAIL ✗  ← LEAK DETECTED"
            line = f"  [BLOCKED]  {svc:<25} {status}"
            print(line); report.append(line)
            if not ok: all_pass = False

    summary = f"\n{'='*50}\nResult: {'COMPLIANT ✓' if all_pass else 'NON-COMPLIANT ✗'}\n"
    print(summary); report.append(summary)

    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(report))
    print(f"[*] Report saved → {REPORT_FILE}")

if __name__ == "__main__":
    run_checks()
