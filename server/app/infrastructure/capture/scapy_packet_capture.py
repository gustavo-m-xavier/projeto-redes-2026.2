import logging
import threading
from collections import deque

from scapy.all import sniff

from app.domain.ports import PacketAnalyzerPort, PacketCapturePort, TelemetryPort

logger = logging.getLogger(__name__)


class ScapyPacketCapture(PacketCapturePort):
    def __init__(
        self,
        network_interface: str,
        analyzer: PacketAnalyzerPort,
        telemetry: TelemetryPort,
    ) -> None:
        self._network_interface = network_interface
        self._analyzer = analyzer
        self._telemetry = telemetry
        self._lock = threading.Lock()
        self._buffer = deque(maxlen=200)
        self._sniffer = None
        self._stop_event = threading.Event()
        self._last_error = None

    def start(self) -> None:
        if self._sniffer and self._sniffer.is_alive():
            return
        self._stop_event.clear()
        self._last_error = None
        self._sniffer = threading.Thread(target=self._capture_loop, daemon=True)
        self._sniffer.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._sniffer and self._sniffer.is_alive():
            self._sniffer.join(timeout=2)

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def _capture_loop(self) -> None:
        try:
            sniff(
                iface=self._network_interface,
                prn=self._handle_packet,
                store=False,
                stop_filter=lambda _: self._stop_event.is_set(),
                monitor=False,
            )
        except OSError as exc:
            self._last_error = str(exc)
            logger.exception("Não foi possível iniciar a captura na interface %s", self._network_interface)
        except Exception as exc:
            self._last_error = str(exc)
            logger.exception("Falha durante a captura de pacotes")

    def _handle_packet(self, packet):
        metadata = self._analyzer.analyze(packet)
        if metadata is None:
            return

        with self._lock:
            self._buffer.append(metadata)

        self._telemetry.register_packet(metadata)

    def get_packets(self, ip: str | None = None, port: int | None = None, protocol: str | None = None) -> list[dict]:
        with self._lock:
            items = list(self._buffer)
        filtered = []
        for item in items:
            if ip and item.get("src_ip") != ip and item.get("dst_ip") != ip:
                continue
            if port and item.get("src_port") != port and item.get("dst_port") != port:
                continue
            if protocol and str(item.get("protocol")).upper() != str(protocol).upper():
                continue
            filtered.append(item)
        return filtered
