import threading
import time
from collections import deque


from app.domain.ports import TelemetryPort


class InMemoryTelemetry(TelemetryPort):
    def __init__(self, window_seconds: int = 10):
        self.window_seconds = window_seconds
        self.total_packets = 0
        self.total_bytes = 0
        self.tcp_bytes = 0
        self.udp_bytes = 0
        self._history = deque(maxlen=600)
        self._lock = threading.Lock()

    def register_packet(self, packet: dict) -> None:
        timestamp = time.time()
        protocol = str(packet.get("protocol", "UNKNOWN")).upper()
        length = int(packet.get("length", 0) or 0)

        with self._lock:
            self.total_packets += 1
            self.total_bytes += length
            if protocol == "TCP":
                self.tcp_bytes += length
            elif protocol == "UDP":
                self.udp_bytes += length
            self._history.append({"timestamp": timestamp, "protocol": protocol, "bytes": length})

    def snapshot(self) -> dict:
        now = time.time()
        with self._lock:
            recent_packets = [entry for entry in self._history if now - float(entry["timestamp"]) <= self.window_seconds]
            pps = round(len(recent_packets) / self.window_seconds, 2)
            recent_bytes = sum(int(entry["bytes"]) for entry in recent_packets)
            history = list(self._history)
            total_packets = self.total_packets
            total_bytes = self.total_bytes
            tcp_bytes = self.tcp_bytes
            udp_bytes = self.udp_bytes

        return {
            "pps": pps,
            "total_packets": total_packets,
            "total_bytes": total_bytes,
            "tcp_bytes": tcp_bytes,
            "udp_bytes": udp_bytes,
            "history": [
                {"timestamp": entry["timestamp"], "protocol": entry["protocol"], "bytes": entry["bytes"]}
                for entry in history
            ],
            "recent_window_bytes": recent_bytes,
        }
