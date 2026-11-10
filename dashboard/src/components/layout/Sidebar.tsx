import { Activity, EthernetPort, Network, Shield, Signal } from "lucide-react";

export function Sidebar({ connected }: { connected: boolean }) {
  return (
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Sentinela início">
        <span className="brand-mark">
          <Signal size={20} />
        </span>
        <span>
          <strong>sentinela</strong>
          <small>NETWORK OBSERVABILITY</small>
        </span>
      </a>
      <div className="side-label">MONITORAMENTO</div>
      <a className="nav-item active" href="#overview">
        <Activity size={17} /> Visão geral <span className="nav-live" />
      </a>
      <a className="nav-item" href="#traffic">
        <Network size={17} /> Tráfego e pacotes
      </a>
      <a className="nav-item" href="#connections">
        <EthernetPort size={17} /> Conexões
      </a>
      <a className="nav-item" href="#firewall">
        <Shield size={17} /> Firewall
      </a>
      <div className="sidebar-bottom">
        <span className={`connection-indicator ${connected ? "online" : ""}`} />
        <div>
          <b>{connected ? "Servidor conectado" : "Reconectando…"}</b>
          <small>Canal de atualização ao vivo</small>
        </div>
      </div>
    </aside>
  );
}
