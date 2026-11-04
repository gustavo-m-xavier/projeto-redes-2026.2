import type { Telemetry } from "../types";

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 100 ? 0 : 1)} ${units[unit]}`;
}

export function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function buildChartData(telemetry: Telemetry) {
  const buckets = new Map<
    number,
    { timestamp: number; tcp: number; udp: number; other: number }
  >();
  const now = Math.floor(Date.now() / 1000);
  for (let second = now - 29; second <= now; second += 1) {
    buckets.set(second, { timestamp: second, tcp: 0, udp: 0, other: 0 });
  }
  for (const point of telemetry.history ?? []) {
    const bucket = buckets.get(Math.floor(point.timestamp));
    if (!bucket) continue;
    if (point.protocol === "TCP") bucket.tcp += point.bytes;
    else if (point.protocol === "UDP") bucket.udp += point.bytes;
    else bucket.other += point.bytes;
  }
  return [...buckets.values()].map((bucket) => ({
    ...bucket,
    label: new Date(bucket.timestamp * 1000).toLocaleTimeString("pt-BR", {
      minute: "2-digit",
      second: "2-digit",
    }),
  }));
}
