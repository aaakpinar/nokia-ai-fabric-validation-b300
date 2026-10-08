#!/usr/bin/env python3
"""A script used to generate netplan with Policy Based Routes.

Mapping Order (based on cabling):
1. GPU5 (OSFP1) -> Leaf 1
2. GPU4 (OSFP2) -> Leaf 1
3. GPU7 (OSFP3) -> Leaf 1
4. GPU6 (OSFP4) -> Leaf 1
-- Boundary --
5. GPU0 (OSFP5) -> Leaf 2
6. GPU1 (OSFP6) -> Leaf 2
7. GPU2 (OSFP7) -> Leaf 2
8. GPU3 (OSFP8) -> Leaf 2

IP Pattern: fd00:1:<LeafID>:1:<NodeID>:<Port>:0:<Host>

Node ID Calculation:
- Resets for every Leaf.
- Server 1 uses Node IDs 1-4.
- Server 2 uses Node IDs 5-8.
"""
import yaml
import argparse

# Defines the 16 interfaces sorted by the specific OSFP cabling order
interfaces = [
    # --- LEAF 1 Interfaces ---
    # 1. GPU 5 -> OSFP1
    {"name": "enp147s0f0np0", "mac": None},
    {"name": "enp147s0f1np1", "mac": None},
    # 2. GPU 4 -> OSFP2
    {"name": "enp131s0f0np0", "mac": None},
    {"name": "enp131s0f1np1", "mac": None},
    # 3. GPU 7 -> OSFP3
    {"name": "enp243s0f0np0", "mac": None},
    {"name": "enp243s0f1np1", "mac": None},
    # 4. GPU 6 -> OSFP4
    {"name": "enp227s0f0np0", "mac": None},
    {"name": "enp227s0f1np1", "mac": None},
    # --- LEAF 2 Interfaces ---
    # 5. GPU 0 -> OSFP5
    {"name": "enp3s0f0np0", "mac": None},
    {"name": "enp3s0f1np1", "mac": None},
    # 6. GPU 1 -> OSFP6
    {"name": "enp19s0f0np0", "mac": None},
    {"name": "enp19s0f1np1", "mac": None},
    # 7. GPU 2 -> OSFP7
    {"name": "enp99s0f0np0", "mac": None},
    {"name": "enp99s0f1np1", "mac": None},
    # 8. GPU 3 -> OSFP8
    {"name": "enp115s0f0np0", "mac": None},
    {"name": "enp115s0f1np1", "mac": None},
]

def generate_netplan(server_id):
    base_table_id = 1000

    ethernets = {}
    vlans = {}

    for i, iface in enumerate(interfaces):
        name = iface["name"]

        # --- Logic Calculation ---

        # Determine Leaf ID (3rd Octet)
        # First 8 interfaces (Indices 0-7) -> Leaf 1
        # Last 8 interfaces (Indices 8-15) -> Leaf 2
        if i < 8:
            leaf_id = 1
            local_i = i  # 0-7
        else:
            leaf_id = 2
            local_i = i - 8  # Reset index to 0-7 for the second leaf

        # Determine Node ID (5th Octet)
        # We process GPUs in pairs of ports.
        # local_i // 2 gives us 0, 1, 2, 3 relative to the Leaf.
        gpu_relative_index = local_i // 2

        # Calculate Base offset based on Server ID
        # Server 1 (B300-5) -> offset 0 -> IDs 1,2,3,4
        # Server 2 (B300-6) -> offset 4 -> IDs 5,6,7,8
        server_offset = (server_id - 1) * 4

        node_id_decimal = server_offset + gpu_relative_index + 1

        # Port (6th Octet): 1 or 2
        port_index = i % 2
        port_octet = port_index + 1

        # Construct Subnet Prefix
        # Pattern: fd00:1:<LeafID>:1:<NodeID>:<Port>:0
        ip_prefix = f"fd00:1:{leaf_id}:1:{node_id_decimal:x}:{port_octet}:0"

        # Server IP ends in :2
        address_ip = f"{ip_prefix}:2"
        # Gateway IP ends in :1
        gateway_ip = f"{ip_prefix}:1"

        current_table = base_table_id + i

        # --- Ethernet Config ---
        eth_config = {"mtu": 9000, "optional": True}
        if iface["mac"] and server_id == 1:
            eth_config["match"] = {"macaddress": iface["mac"]}

        ethernets[name] = eth_config

        # --- VLAN Config ---
        vlan_name = f"{name}.1"

        vlans[vlan_name] = {
            "id": 1,
            "link": name,
            "mtu": 9000,
            "addresses": [f"{address_ip}/96"],
            "routes": [{"to": "::/0", "via": gateway_ip, "table": current_table}],
            "routing-policy": [{"from": address_ip, "to": "::/0", "table": current_table}],
        }

    netplan = {"network": {"version": 2, "ethernets": ethernets, "vlans": vlans}}

    print(yaml.dump(netplan, sort_keys=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Netplan for GPU Cluster")
    parser.add_argument("--server", type=int, default=1, help="Server Index (1, 2, 3...)")
    args = parser.parse_args()

    generate_netplan(args.server)

