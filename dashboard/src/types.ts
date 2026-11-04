export interface Packet {
  timestamp: number;
  src_ip: string;
  dst_ip: string;
  src_port: number | null;
  dst_port: number | null;
  protocol: string;
  length: number;
  http: { method: string; headers: string[] } | null;
  dns: { domain: string | null; qr: number | null } | null;
}

export interface Telemetry {
  pps: number;
  total_packets: number;
  total_bytes: number;
  tcp_bytes: number;
  udp_bytes: number;
  history: { timestamp: number; protocol: string; bytes: number }[];
}

export interface Connection {
  status: string;
  local_address: string;
  local_port: number | null;
  remote_address: string;
  remote_port: number | null;
  protocol: string;
}

export interface FirewallRule {
  port?: number;
  rule?: string;
  status: string;
  tool?: string;
}

export interface LiveSnapshot {
  telemetry: Telemetry;
  connections: { listeners: Connection[]; connections: Connection[] };
  firewall: FirewallRule[];
  packets: Packet[];
  capture: { interface: string; error: string | null };
}
