import { useMemo, useState } from "react";
import type { Packet } from "../../types";
import { formatBytes, formatTime } from "../../shared/formatters";

function ProtocolPill({ protocol }: { protocol: string }) {
  return (
    <span className={`protocol-pill ${protocol.toLowerCase()}`}>
      {protocol}
    </span>
  );
}

function PacketRow({ packet }: { packet: Packet }) {
  const detail = packet.dns?.domain
    ? `${packet.dns.qr ? "Resposta" : "Consulta"} DNS · ${packet.dns.domain}`
    : packet.http?.method
      ? `HTTP ${packet.http.method}`
      : "—";
  return (
    <tr>
      <td className="muted-cell">{formatTime(packet.timestamp)}</td>
      <td>
        <span className="address-cell">
          {packet.src_ip}
          <small>:{packet.src_port ?? "—"}</small>
        </span>
      </td>
      <td>
        <span className="address-cell">
          {packet.dst_ip}
          <small>:{packet.dst_port ?? "—"}</small>
        </span>
      </td>
      <td>
        <ProtocolPill protocol={packet.protocol} />
      </td>
      <td className={packet.dns || packet.http ? "detail-cell" : "muted-cell"}>
        {detail}
      </td>
      <td>{formatBytes(packet.length)}</td>
    </tr>
  );
}

export function PacketTable({
  packets,
  connected,
}: {
  packets: Packet[];
  connected: boolean;
}) {
  const [query, setQuery] = useState("");
  const [protocol, setProtocol] = useState("ALL");
  const visiblePackets = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return packets.filter((packet) => {
      const matchesProtocol =
        protocol === "ALL" || packet.protocol === protocol;
      const searchable = [
        packet.src_ip,
        packet.dst_ip,
        packet.src_port,
        packet.dst_port,
        packet.dns?.domain,
        packet.http?.method,
      ]
        .join(" ")
        .toLowerCase();
      return matchesProtocol && (!needle || searchable.includes(needle));
    });
  }, [packets, protocol, query]);

  return (
    <section className="panel packet-panel">
      <div className="panel-heading">
        <div>
          <div className="panel-title">Pacotes recentes</div>
          <div className="panel-subtitle">
            {visiblePackets.length} registros na janela de captura
          </div>
        </div>
        <div className="filters">
          <input
            aria-label="Filtrar pacotes"
            placeholder="IP, domínio, porta..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <select
            aria-label="Filtrar protocolo"
            value={protocol}
            onChange={(event) => setProtocol(event.target.value)}
          >
            <option value="ALL">Todos</option>
            <option value="TCP">TCP</option>
            <option value="UDP">UDP</option>
          </select>
        </div>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Horário</th>
              <th>Origem</th>
              <th>Destino</th>
              <th>Protocolo</th>
              <th>Detalhe</th>
              <th>Tamanho</th>
            </tr>
          </thead>
          <tbody>
            {visiblePackets
              .slice()
              .reverse()
              .slice(0, 12)
              .map((packet, index) => (
                <PacketRow
                  packet={packet}
                  key={`${packet.timestamp}-${index}`}
                />
              ))}
            {visiblePackets.length === 0 && (
              <tr>
                <td className="empty-row" colSpan={6}>
                  {connected
                    ? "Aguardando pacotes da interface…"
                    : "Conectando ao servidor…"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
