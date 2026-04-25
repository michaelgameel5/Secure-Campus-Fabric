#!/usr/bin/env python3
import subprocess, time, yaml, datetime, os

INVENTORY = "inventory/campus.yaml"
METRICS_FILE = "monitoring/metrics.prom"
LOG_FILE = "monitoring/events.log"
INTERVAL = 10

def ping(ns, target, count=3):
    cmd = f"ip netns exec {ns} ping -c {count} -W 2 {target}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        if "rtt" in line:
            return float(line.split('/')[4])
    return None

def log_event(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def write_metrics(metrics):
    with open(METRICS_FILE, "w") as f:
        f.write(f"# Updated {datetime.datetime.now()}\n")
        for name, val in metrics.items():
            f.write(f"{name} {val}\n")

def monitor():
    with open(INVENTORY) as f:
        inv = yaml.safe_load(f)
    hq_ip = inv['hq']['vpn_ip']
    prev_state = {}

    print(f"[*] Health monitor started — polling every {INTERVAL}s")
    print(f"[*] Metrics → {METRICS_FILE} | Events → {LOG_FILE}\n")

    while True:
        metrics = {}
        for branch in inv['branches']:
            ns  = branch['namespace']
            bid = branch['id']
            latency = ping(ns, hq_ip)

            if latency is not None:
                metrics[f'tunnel_up{{branch="{bid}"}}'] = 1
                metrics[f'tunnel_latency_ms{{branch="{bid}"}}'] = round(latency, 2)
                if prev_state.get(bid) == 0:
                    log_event(f"RECOVERY  {bid} → HQ tunnel restored ({latency:.1f}ms)")
                else:
                    log_event(f"OK        {bid} → HQ  {latency:.1f} ms")
                prev_state[bid] = 1
            else:
                metrics[f'tunnel_up{{branch="{bid}"}}'] = 0
                metrics[f'tunnel_latency_ms{{branch="{bid}"}}'] = -1
                if prev_state.get(bid) != 0:
                    log_event(f"FAILOVER  {bid} → HQ UNREACHABLE — failover triggered!")
                prev_state[bid] = 0

        write_metrics(metrics)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    os.makedirs("monitoring", exist_ok=True)
    monitor()
