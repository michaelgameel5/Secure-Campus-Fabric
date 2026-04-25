#!/usr/bin/env python3
import yaml, subprocess, os
from jinja2 import Template

INVENTORY = "inventory/campus.yaml"

def run(cmd, ns=None):
    if ns:
        cmd = f"ip netns exec {ns} {cmd}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [warn] {result.stderr.strip()}")
    return result

def gen_keypair(name, out_dir="configs/wireguard"):
    priv = f"{out_dir}/{name}_private.key"
    pub  = f"{out_dir}/{name}_public.key"
    if not os.path.exists(priv):
        os.system(f"wg genkey > {priv} && wg pubkey < {priv} > {pub}")
        os.chmod(priv, 0o600)
    return open(priv).read().strip(), open(pub).read().strip()

def load_inventory():
    with open(INVENTORY) as f:
        return yaml.safe_load(f)

def generate_wg_configs(inv):
    print("\n[*] Generating WireGuard configs...")
    hq = inv['hq']
    hq_priv, hq_pub = gen_keypair("hq")

    hq_peers = ""
    branch_configs = {}

    for branch in inv['branches']:
        b_priv, b_pub = gen_keypair(branch['id'])
        link_ip = branch['link_ip_hq'].split('/')[0]

        hq_peers += f"""
[Peer]
# {branch['name']}
PublicKey = {b_pub}
AllowedIPs = {branch['vpn_ip']}/32
"""
        branch_configs[branch['id']] = f"""[Interface]
PrivateKey = {b_priv}
Address = {branch['vpn_ip']}/24

[Peer]
PublicKey = {hq_pub}
Endpoint = {link_ip}:{hq['vpn_listen_port']}
AllowedIPs = {hq['vpn_ip']}/32, {hq['lan_subnet']}
PersistentKeepalive = 25
"""

    hq_conf = f"""[Interface]
PrivateKey = {hq_priv}
Address = {hq['vpn_ip']}/24
ListenPort = {hq['vpn_listen_port']}
{hq_peers}"""
    open("configs/wireguard/hq.conf", "w").write(hq_conf)
    print("  [+] configs/wireguard/hq.conf")

    for bid, cfg in branch_configs.items():
        path = f"configs/wireguard/{bid}.conf"
        open(path, "w").write(cfg)
        print(f"  [+] {path}")

def apply_firewall(inv):
    print("\n[*] Applying firewall rules...")
    for branch in inv['branches']:
        ns = branch['namespace']
        run("iptables -F", ns)
        run("iptables -P FORWARD DROP", ns)
        run("iptables -P INPUT DROP", ns)
        run("iptables -P OUTPUT ACCEPT", ns)
        run("iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT", ns)
        run("iptables -A INPUT -i lo -j ACCEPT", ns)
        for svc in inv['hq']['allowed_services']:
            ip, port = svc.split(":")
            run(f"iptables -A OUTPUT -d {ip} -p tcp --dport {port} -j ACCEPT", ns)
        rules_out = f"configs/firewall/{branch['id']}_rules.txt"
        run_result = run("iptables -L -n --line-numbers", ns)
        open(rules_out, "w").write(run_result.stdout)
        print(f"  [+] Firewall applied → {ns} (saved to {rules_out})")

def apply_routes(inv):
    print("\n[*] Applying routes...")
    hq = inv['hq']
    for branch in inv['branches']:
        ns = branch['namespace']
        gw = branch['link_ip_hq'].split('/')[0]
        run(f"ip route replace default via {gw}", ns)
        route_out = f"configs/routing/{branch['id']}_routes.txt"
        r = run("ip route show", ns)
        open(route_out, "w").write(r.stdout)
        print(f"  [+] Routes applied → {ns} (saved to {route_out})")

if __name__ == "__main__":
    inv = load_inventory()
    os.makedirs("configs/wireguard", exist_ok=True)
    os.makedirs("configs/firewall", exist_ok=True)
    os.makedirs("configs/routing", exist_ok=True)
    generate_wg_configs(inv)
    apply_firewall(inv)
    apply_routes(inv)
    print("\n[✓] Controller finished — all configs generated and applied")
