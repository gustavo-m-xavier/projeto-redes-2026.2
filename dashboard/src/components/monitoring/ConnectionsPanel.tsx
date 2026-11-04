import type { Connection } from "../../types";

function ConnectionRow({ connection }: { connection: Connection }) {
  return (
    <div className="connection-row">
      <span className="connection-protocol">
        {connection.protocol === "TCP" ? "T" : "U"}
      </span>
      <div className="connection-address">
        <b>{connection.remote_address}</b>
        <small>porta remota {connection.remote_port ?? "—"}</small>
      </div>
      <span className="local-port">{connection.local_port ?? "—"}</span>
    </div>
  );
}

export function ConnectionsPanel({
  connections,
  listeners,
}: {
  connections: Connection[];
  listeners: Connection[];
}) {
  const established = connections.filter(
    (connection) => connection.status === "ESTABLISHED",
  );
  const ports = listeners
    .map((item) => item.local_port)
    .filter((value): value is number => value !== null);
  return (
    <section className="panel connections-panel" id="connections">
      <div className="panel-heading">
        <div>
          <div className="panel-title">Conexões estabelecidas</div>
          <div className="panel-subtitle">Sockets ativos no servidor</div>
        </div>
        <span className="count-badge">{established.length}</span>
      </div>
      <div className="connection-list">
        {established.slice(0, 7).map((connection, index) => (
          <ConnectionRow
            key={`${connection.local_port}-${index}`}
            connection={connection}
          />
        ))}
        {established.length === 0 && (
          <div className="empty-state">
            Nenhuma conexão estabelecida no momento.
          </div>
        )}
      </div>
      <div className="listener-footer">
        <span>PORTAS EM ESCUTA</span>
        <strong>{ports.slice(0, 8).join(" · ") || "—"}</strong>
      </div>
    </section>
  );
}
