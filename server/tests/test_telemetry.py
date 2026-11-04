import unittest
from unittest.mock import patch

from app.infrastructure.telemetry.in_memory_telemetry import InMemoryTelemetry


class TelemetryTests(unittest.TestCase):
    def test_counts_bytes_once_and_reports_average_packets_per_second(self):
        telemetry = InMemoryTelemetry(window_seconds=10)
        packet = {"protocol": "TCP", "length": 60}

        with patch("app.infrastructure.telemetry.in_memory_telemetry.time.time", side_effect=[1000, 1001]):
            telemetry.register_packet(packet)
            snapshot = telemetry.snapshot()

        self.assertEqual(snapshot["total_packets"], 1)
        self.assertEqual(snapshot["total_bytes"], 60)
        self.assertEqual(snapshot["tcp_bytes"], 60)
        self.assertEqual(snapshot["pps"], 0.1)


if __name__ == "__main__":
    unittest.main()
