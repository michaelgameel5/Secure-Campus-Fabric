#!/usr/bin/env python3
import argparse, yaml, subprocess, os, sys

INVENTORY = "inventory/campus.yaml"

def run(cmd, ns=None):
    if ns: cmd = f"ip netns exec {ns} {cmd}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [warn] {r.stderr.strip()}")

p = argparse.ArgumentParser()
p.add_argument("--id",       required=True)
p.add_argument("--name",     required=True)
p.add_argument("--vpn-ip",   required=True)
p.add_argument("--lan",      required=True)
p.add_argument("--link-net", required=True)
args = p.parse_args()

with open(INVENTORY) as f:
    inv = yaml.safe_load(f)

# Check not duplicate
if any(b['id'] == args.id for b in inv['branches']):
    print(f"[!] Branch {args.id} already exists in inventory"); sys.exit(1)

new_branch = {
    "id": args.id, "name": args.name,
    "namespace": f"ns_{args.id}",
    "lan_subnet": args.lan,
    "vpn_ip": args.vpn_ip,
    "veth_local": f"veth_{args.id}",
    "veth_peer":  f"veth_{args.id}_hq",
    "link_ip_branch": f"{args.link_net}.2/30",
    "link_ip_hq":     f"{args.link_net}.1/30",
}

inv['branches'].append(new_branch)
with open(INVENTORY, "w") as f:
    yaml.dump(inv, f, default_flow_style=False)
print(f"[+] {args.name} added to inventory")

run(f"ip netns add ns_{args.id}")
run(f"ip link add veth_{args.id} type veth peer name veth_{args.id}_hq")
run(f"ip link set veth_{args.id} netns ns_{args.id}")
run(f"ip link set veth_{args.id}_hq netns ns_hq")
run(f"ip addr add {args.link_net}.2/30 dev veth_{args.id}", f"ns_{args.id}")
run(f"ip link set veth_{args.id} up", f"ns_{args.id}")
run(f"ip link set lo up", f"ns_{args.id}")
run(f"ip addr add {args.link_net}.1/30 dev veth_{args.id}_hq", "ns_hq")
run(f"ip link set veth_{args.id}_hq up", "ns_hq")
print(f"[+] Namespace ns_{args.id} wired up")

os.system("python3 scripts/controller.py")
print(f"\n[✓] {args.name} is fully onboarded!")
