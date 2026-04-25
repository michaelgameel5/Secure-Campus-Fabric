#!/bin/bash
set -e

echo "[*] Creating HQ namespace..."
ip netns add ns_hq 2>/dev/null || echo "ns_hq already exists"
ip netns exec ns_hq ip link set lo up

for b in 1 2 3; do
  NS="ns_branch${b}"
  VETH="veth_b${b}"
  PEER="veth_b${b}_hq"
  BRANCH_IP="172.16.${b}.2/30"
  HQ_IP="172.16.${b}.1/30"

  echo "[*] Creating $NS..."
  ip netns add $NS 2>/dev/null || echo "$NS already exists"

  ip link add $VETH type veth peer name $PEER 2>/dev/null || true
  ip link set $VETH netns $NS
  ip link set $PEER netns ns_hq

  ip netns exec $NS ip addr add $BRANCH_IP dev $VETH 2>/dev/null || true
  ip netns exec $NS ip link set $VETH up
  ip netns exec $NS ip link set lo up

  ip netns exec ns_hq ip addr add $HQ_IP dev $PEER 2>/dev/null || true
  ip netns exec ns_hq ip link set $PEER up

  echo "[+] Branch${b} ready"
done

echo "[✓] All namespaces created"
