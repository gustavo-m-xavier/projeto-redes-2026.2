import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Telemetry } from "../../types";
import { buildChartData, formatBytes } from "../../shared/formatters";

export function TrafficChart({ telemetry }: { telemetry: Telemetry }) {
  const data = buildChartData(telemetry);
  return (
    <section className="panel traffic-panel" id="traffic">
      <div className="panel-heading">
        <div><div className="panel-title">Volume de tráfego</div><div className="panel-subtitle">Bytes observados por protocolo · últimos 30 segundos</div></div>
        <div className="chart-legend">
          <span><i className="legend-dot tcp" /> TCP <b>{formatBytes(telemetry.tcp_bytes)}</b></span>
          <span><i className="legend-dot udp" /> UDP <b>{formatBytes(telemetry.udp_bytes)}</b></span>
        </div>
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 12, bottom: 0, left: -12 }}>
            <defs>
              <linearGradient id="tcpGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#39c6f4" stopOpacity={0.28} /><stop offset="100%" stopColor="#39c6f4" stopOpacity={0} /></linearGradient>
              <linearGradient id="udpGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#9b8cff" stopOpacity={0.22} /><stop offset="100%" stopColor="#9b8cff" stopOpacity={0} /></linearGradient>
            </defs>
            <CartesianGrid stroke="#1b2a3e" strokeDasharray="3 5" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#8292a8", fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={30} />
            <YAxis tick={{ fill: "#8292a8", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={formatBytes} />
            <Tooltip
              contentStyle={{ background: "#0d1928", border: "1px solid #25364a", borderRadius: 10, color: "#e7f0fb" }}
              formatter={(value) => formatBytes(Number(value))}
              labelStyle={{ color: "#97a9bf" }}
            />
            <Area type="monotone" dataKey="tcp" name="TCP" stroke="#39c6f4" strokeWidth={2} fill="url(#tcpGradient)" isAnimationActive={false} />
            <Area type="monotone" dataKey="udp" name="UDP" stroke="#9b8cff" strokeWidth={2} fill="url(#udpGradient)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
