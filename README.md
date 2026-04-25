# Secure Campus Fabric

Automates branch-to-HQ connectivity for a multi-site campus using **Linux network namespaces** on a single Kali machine — no VMs required.

## Features
- Multi-site routing via virtual ethernet pairs + WireGuard tunnels
- Auto-generated VPN and route configs from YAML inventory
- Per-branch iptables ACL and firewall rules
- Health monitoring with failover detection
- Compliance checker (approved services only)
- One-command branch onboarding

## Quick Start
```bash
sudo bash scripts/setup_namespaces.sh
sudo python3 scripts/controller.py
sudo python3 monitoring/health_monitor.py &
sudo python3 compliance/checker.py
```

## Full Demo
```bash
sudo bash demo/demo.sh
```

## Onboard a New Branch
```bash
sudo python3 scripts/onboard_branch.py \
  --id branch4 --name "Branch-Delta" \
  --vpn-ip 10.10.10.5 --lan 192.168.4.0/24 --link-net 172.16.4
```

## Outputs
| File | Description |
|------|-------------|
| `configs/wireguard/*.conf` | WireGuard configs per site |
| `configs/firewall/*_rules.txt` | iptables rules per branch |
| `configs/routing/*_routes.txt` | Route tables per branch |
| `monitoring/metrics.prom` | Prometheus-style tunnel metrics |
| `monitoring/events.log` | Failover event log |
| `compliance/report.txt` | Branch compliance checklist |
