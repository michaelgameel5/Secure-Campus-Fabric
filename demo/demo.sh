#!/bin/bash
set -e
cd "$(dirname "$0")/.."
source venv/bin/activate

echo "========================================"
echo "   Secure Campus Fabric — Full Demo"
echo "========================================"

echo -e "\n[1] Setting up namespaces..."
sudo bash scripts/setup_namespaces.sh

echo -e "\n[2] Running controller..."
sudo venv/bin/python3 scripts/controller.py

echo -e "\n[3] Starting health monitor (background)..."
sudo venv/bin/python3 monitoring/health_monitor.py &
MONITOR_PID=$!
sleep 5

echo -e "\n[4] Compliance check (baseline)..."
sudo venv/bin/python3 compliance/checker.py

echo -e "\n[5] Onboarding new branch: Branch-Delta..."
sudo venv/bin/python3 scripts/onboard_branch.py \
  --id branch4 --name "Branch-Delta" \
  --vpn-ip 10.10.10.5 --lan 192.168.4.0/24 --link-net 172.16.4

echo -e "\n[6] Simulating link failure on Branch-Alpha..."
sudo ip netns exec ns_hq ip link set veth_b1_hq down
echo "  Primary path DOWN — waiting 15s for monitor to detect..."
sleep 15

echo -e "\n[7] Restoring Branch-Alpha link..."
sudo ip netns exec ns_hq ip link set veth_b1_hq up
sleep 5

echo -e "\n[8] Final compliance check..."
sudo venv/bin/python3 compliance/checker.py

kill $MONITOR_PID 2>/dev/null || true
echo -e "\n[✓] Demo complete!"
echo "    → Metrics:    monitoring/metrics.prom"
echo "    → Event log:  monitoring/events.log"
echo "    → Compliance: compliance/report.txt"
echo "    → WG configs: configs/wireguard/"
