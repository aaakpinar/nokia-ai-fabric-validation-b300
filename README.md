# Nokia AI Fabric Validation: NVIDIA HGX B300

Configurations, scripts and job logs from the validation of NVIDIA HGX B300 servers on a Nokia data center fabric:

- **Backend:** Nokia 7220 IXR-H5 leaf-spine for GPU-to-GPU RoCEv2 traffic (DCQCN: PFC + ECN), SR Linux 25.10.1
- **Frontend:** Nokia 7220 IXR-D3L leaf-spine with EVPN-VXLAN services, SR Linux 25.7.2, FRR 10.1.3 on the hosts
- **Automation:** Nokia EDA 25.8.3

## Test setup

| Role | Platform | Count |
|---|---|---|
| GPU servers | Supermicro SYS-8126GS-NB3RT, NVIDIA HGX B300 (8 GPUs), ConnectX-8 NICs split into 2 × 400G | 2 |
| Backend leaf | Nokia 7220 IXR-H5-64D | 2 |
| Backend spine | Nokia 7220 IXR-H5-64D | 1 |
| Frontend leaf | Nokia 7220 IXR-D3L | 2 |
| Frontend spine | Nokia 7220 IXR-D3L | 1 |

## Results

| Test | Result |
|---|---|
| NCCL all-reduce, 16 GPUs, 1 QP per connection, no host QoS | 725.4 GB/s average bus bandwidth |
| NCCL all-reduce, 16 GPUs, 4 QPs per connection, no host QoS | 746.0 GB/s average bus bandwidth |
| NCCL all-reduce, 16 GPUs, 4 QPs per connection, host QoS applied | 746.4 GB/s average bus bandwidth |
| ib_send_bw, one 400G port, bidirectional | 776.4 Gb/s without host QoS, 778.1 Gb/s with host QoS |
| Forced congestion, two senders to one NIC | ECN marking, CNPs and PFC engaged; no packets dropped |
| MLCommons Llama 3.1 8B training, four runs | 90.4 to 97.6 minutes per run |

The results were obtained with two B300 servers and a single backend spine; behavior at larger scale (more nodes, ECMP across multiple spines) was not measured.

## Contents

| Path | Description |
|---|---|
| [`srlinux/backend/`](srlinux/backend) | Full SR Linux configurations (`info flat`) of the backend leaves and spine |
| [`srlinux/frontend/`](srlinux/frontend) | Full SR Linux configurations (`info flat`) of the frontend leaves and spine |
| [`eda/backend-crs.yaml`](eda/backend-crs.yaml) | EDA custom resources for the backend fabric |
| [`eda/frontend-crs.yaml`](eda/frontend-crs.yaml) | EDA custom resources for the frontend fabric |
| [`host/netplan-pbr-generator.py`](host/netplan-pbr-generator.py) | Generates the netplan configuration with static IPv6 addresses and policy-based routing for the B300 backend NICs |
| [`host/frr-configs.txt`](host/frr-configs.txt) | FRR configuration of the two B300 hosts (eBGP unnumbered underlay, EVPN overlay) |
| [`host/nccl-topo.xml`](host/nccl-topo.xml) | Topology discovered by NCCL (`NCCL_TOPO_DUMP_FILE`): two mlx interfaces per GPU, NUMA placement |
| [`host/ib_ethtool_delta.sh`](host/ib_ethtool_delta.sh) | Reports Ethernet and RDMA counter deltas on the B300 hosts |
| [`mlcommons-llama31-8b/`](mlcommons-llama31-8b) | Slurm output of the MLCommons Llama 3.1 8B training runs (table below) |

### MLCommons Llama 3.1 8B runs

The job names follow the MLCommons reference configuration files. All runs were executed on the B300 servers of this setup.

| Job | Nodes × GPUs | Host QoS | Configuration | Run time | Log |
|---|---|---|---|---|---|
| 52 | 2 × 4 | - | GB200_2x4x2xtp1pp1cp1_8b | 5,424 s (90.4 min) | [`slurm-52.out`](mlcommons-llama31-8b/slurm-52.out) |
| 53 | 2 × 4 | - | GB300_2x4x2xtp1pp1cp1_8b | 5,833 s (97.2 min) | [`slurm-53.out`](mlcommons-llama31-8b/slurm-53.out) |
| 54 | 1 × 8 | - | DGXB200_1x8x2xtp1pp1cp1_8b | 5,807 s (96.8 min) | [`slurm-54.out`](mlcommons-llama31-8b/slurm-54.out) |
| 56 | 2 × 4 | Applied | GB300_2x4x2xtp1pp1cp1_8b | 5,853 s (97.6 min) | [`slurm-56.out`](mlcommons-llama31-8b/slurm-56.out) |

## Redactions

Password hashes and SSH public keys in the SR Linux configurations are replaced with `<password-hash>` and `<ssh-public-key>`. A user name in the job paths is replaced with `user`. Nothing else was changed.
