#!/bin/bash
echo "[*] Tearing down namespaces..."
for ns in ns_hq ns_branch1 ns_branch2 ns_branch3 ns_branch4; do
  ip netns del $ns 2>/dev/null && echo "[-] Deleted $ns" || true
done
echo "[✓] Teardown complete"
