#!/bin/bash

ETH_IFACE="$1"
PATTERN="$2"
IB_DEV="$3"
INTERVAL=10
IB_PORT=1

if [[ -z "$ETH_IFACE" || -z "$PATTERN" || -z "$IB_DEV" ]]; then
    echo "Usage: $0 <eth_iface> <pattern> <ib_device>"
    echo "Example: $0 enp227s0f0np0 \"pause|prio3|prio6\" mlx5_20"
    exit 1
fi

IB_PATH="/sys/class/infiniband/$IB_DEV/ports/$IB_PORT/hw_counters"

if [[ ! -d "$IB_PATH" ]]; then
    echo "ERROR: IB counters path not found: $IB_PATH"
    exit 1
fi

declare -A base_eth
declare -A base_ib

# --- Capture Ethernet baseline ---
while read -r key val; do
    base_eth["$key"]=$val
done < <(ethtool -S "$ETH_IFACE" | grep -E "$PATTERN" | awk '{print $1, $2}')

# --- Capture IB baseline ---
for f in "$IB_PATH"/*; do
    key=$(basename "$f")
    base_ib["$key"]=$(cat "$f")
done

# --- Loop ---
while true; do
    clear
    echo "Since start ($(date))"
    echo
    echo "=== Ethernet counters ($ETH_IFACE) ==="
    echo "Pattern: $PATTERN"
    echo

    ethtool -S "$ETH_IFACE" | grep -E "$PATTERN" | awk '{print $1, $2}' | while read -r key val; do
        delta=$((val - base_eth[$key]))
        printf "%-40s %s\n" "$key:" "$delta"
    done

    echo
    echo "=== InfiniBand HW counters ($IB_DEV port $IB_PORT) ==="
    echo

    for f in "$IB_PATH"/*; do
        key=$(basename "$f")
        val=$(cat "$f")
        delta=$((val - base_ib[$key]))
        printf "%-40s %s\n" "$key:" "$delta"
    done

    sleep "$INTERVAL"
done
