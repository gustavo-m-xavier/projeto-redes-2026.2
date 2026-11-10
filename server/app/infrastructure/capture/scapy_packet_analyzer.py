from scapy.all import DNS, DNSQR, IP, TCP, UDP


class ScapyPacketAnalyzer:
    HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD")

    def analyze(self, packet: object) -> dict | None:
        if not packet.haslayer(IP):
            return None

        protocol = "TCP" if packet.haslayer(TCP) else "UDP" if packet.haslayer(UDP) else "UNKNOWN"
        transport = packet[TCP] if packet.haslayer(TCP) else packet[UDP] if packet.haslayer(UDP) else None
        payload = bytes(transport.payload) if transport is not None else b""
        metadata = {
            "timestamp": float(packet.time),
            "src_ip": packet[IP].src,
            "dst_ip": packet[IP].dst,
            "src_port": transport.sport if transport is not None else None,
            "dst_port": transport.dport if transport is not None else None,
            "protocol": protocol,
            "length": int(len(packet)),
            "payload_preview": payload[:128].decode("latin1", errors="ignore"),
            "http": None,
            "dns": None,
        }

        if packet.haslayer(DNS):
            dns_layer = packet[DNS]
            domain = None
            if dns_layer.qd and packet.haslayer(DNSQR):
                domain = packet[DNSQR].qname.decode("utf-8", errors="ignore").rstrip(".")
            metadata["dns"] = {
                "domain": domain,
                "id": int(dns_layer.id) if dns_layer.id is not None else None,
                "qr": int(dns_layer.qr) if dns_layer.qr is not None else None,
            }

        if protocol == "TCP" and payload:
            text = payload.decode("latin1", errors="ignore")
            first_line = text.splitlines()[0] if text.splitlines() else ""
            method = first_line.split(" ", 1)[0]
            if method in self.HTTP_METHODS:
                metadata["http"] = {"method": method, "headers": text.splitlines()[:8]}

        return metadata
