import { useEffect, useState } from "react";
import type { LiveSnapshot, Telemetry } from "../types";

const emptyTelemetry: Telemetry = {
  pps: 0,
  total_packets: 0,
  total_bytes: 0,
  tcp_bytes: 0,
  udp_bytes: 0,
  history: [],
};

const emptySnapshot: LiveSnapshot = {
  telemetry: emptyTelemetry,
  connections: { listeners: [], connections: [] },
  firewall: [],
  packets: [],
  capture: { interface: "unknown", error: null },
};

export function useLiveSnapshot() {
  const [snapshot, setSnapshot] = useState<LiveSnapshot>(emptySnapshot);
  const [connected, setConnected] = useState(false);
  const [messageError, setMessageError] = useState<string | null>(null);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/ws`;
    let socket: WebSocket;
    let retryTimer: number;
    let active = true;

    const connect = () => {
      socket = new WebSocket(url);
      socket.onopen = () => setConnected(true);
      socket.onmessage = (event) => {
        try {
          setSnapshot({ ...emptySnapshot, ...JSON.parse(event.data) });
          setMessageError(null);
        } catch {
          setMessageError("O servidor enviou uma atualização inválida.");
        }
      };
      socket.onclose = () => {
        setConnected(false);
        if (active) retryTimer = window.setTimeout(connect, 2000);
      };
      socket.onerror = () => socket.close();
    };

    connect();
    return () => {
      active = false;
      window.clearTimeout(retryTimer);
      socket?.close();
    };
  }, []);

  return { snapshot, connected, messageError };
}
