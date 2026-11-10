import unittest

from scapy.all import DNS, DNSQR, IP, Raw, TCP, UDP

from app.infrastructure.capture.scapy_packet_analyzer import ScapyPacketAnalyzer


class ScapyPacketAnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = ScapyPacketAnalyzer()

    def test_extracts_http_method_and_transport_metadata(self):
        packet = (
            IP(src="192.0.2.10", dst="192.0.2.20")
            / TCP(sport=43210, dport=80)
            / Raw(load=b"GET / HTTP/1.1\r\nHost: example.test\r\n\r\n")
        )

        result = self.analyzer.analyze(packet)

        self.assertEqual(result["protocol"], "TCP")
        self.assertEqual(result["src_port"], 43210)
        self.assertEqual(result["http"]["method"], "GET")

    def test_extracts_dns_query_domain(self):
        packet = (
            IP(src="192.0.2.10", dst="192.0.2.53")
            / UDP(sport=53000, dport=53)
            / DNS(qd=DNSQR(qname="example.test"))
        )

        result = self.analyzer.analyze(packet)

        self.assertEqual(result["dns"]["domain"], "example.test")
        self.assertEqual(result["dns"]["qr"], 0)

    def test_ignores_packets_without_ipv4(self):
        self.assertIsNone(self.analyzer.analyze(UDP(sport=1, dport=2)))


if __name__ == "__main__":
    unittest.main()
