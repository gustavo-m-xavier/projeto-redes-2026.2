import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowUpRight,
  Check,
  CircleHelp,
  Radio,
  RefreshCw,
  X,
} from "lucide-react";
import { ConnectionsPanel } from "./components/monitoring/ConnectionsPanel";
import { PacketTable } from "./components/monitoring/PacketTable";
import { StatCard } from "./components/monitoring/StatCard";
import { TrafficChart } from "./components/monitoring/TrafficChart";
import { FirewallPanel } from "./components/firewall/FirewallPanel";
import { Sidebar } from "./components/layout/Sidebar";
import { useFirewallActions } from "./hooks/useFirewallActions";
import type { Notice } from "./hooks/useFirewallActions";
import { useLiveSnapshot } from "./hooks/useLiveSnapshot";
import { formatBytes } from "./shared/formatters";

export default function App() {
  const [notice, setNotice] = useState<Notice | null>(null);
  const { snapshot, connected, messageError } = useLiveSnapshot();
  const firewall = useFirewallActions(setNotice);
  const established = snapshot.connections.connections.filter((connection) => connection.status === "ESTABLISHED");

  useEffect(() => {
    if (messageError) setNotice({ kind: "error", text: messageError });
  }, [messageError]);

  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(null), 4500);
    return () => window.clearTimeout(timer);
  }, [notice]);

  return (
    <main className="app-shell">
      <Sidebar connected={connected} />

      <section className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumbs">Infraestrutura <span>/</span> <b>Monitoramento</b></div>
          <div className="topbar-right">
            <span className={`live-badge ${connected ? "online" : ""}`}><i /> {connected ? "AO VIVO" : "OFFLINE"}</span>
            <span className="updated"><RefreshCw size={13} /> atualização contínua</span>
          </div>
        </header>

        <div className="page-heading">
          <div>
            <div className="eyebrow">PAINEL DE CONTROLE</div>
            <h1>Visão geral da rede</h1>
            <p>Tráfego, conexões e segurança da infraestrutura em tempo real.</p>
          </div>
          <div className="interface-chip"><span className="pulse-dot" /> Interface <b>{snapshot.capture.interface}</b></div>
        </div>

        {snapshot.capture.error && (
          <div className="warning-banner">
            <CircleHelp size={17} />
            <span><b>Captura indisponível</b> — {snapshot.capture.error}. Execute o servidor com permissões de captura e confira a interface.</span>
          </div>
        )}

        <div className="stats-grid">
          <StatCard label="Pacotes por segundo" value={snapshot.telemetry.pps.toLocaleString("pt-BR")} note="Média na janela recente" icon={<Activity size={18} />} accent="cyan" />
          <StatCard label="Pacotes capturados" value={snapshot.telemetry.total_packets.toLocaleString("pt-BR")} note="Desde o início da execução" icon={<Radio size={18} />} accent="violet" />
          <StatCard label="Dados observados" value={formatBytes(snapshot.telemetry.total_bytes)} note="TCP + UDP + outros" icon={<ArrowDownToLine size={18} />} accent="green" />
          <StatCard label="Conexões ativas" value={established.length.toLocaleString("pt-BR")} note={`${snapshot.connections.listeners.length} portas em escuta`} icon={<ArrowUpRight size={18} />} accent="orange" />
        </div>

        <TrafficChart telemetry={snapshot.telemetry} />

        <div className="lower-grid">
          <PacketTable packets={snapshot.packets} connected={connected} />
          <ConnectionsPanel
            connections={snapshot.connections.connections}
            listeners={snapshot.connections.listeners}
          />
        </div>

        <FirewallPanel
          rules={snapshot.firewall}
          token={firewall.token}
          onTokenChange={firewall.setToken}
          busyPort={firewall.busyPort}
          onAction={firewall.changeFirewall}
          notify={setNotice}
        />

        <footer className="footer">
          <span><span className={`connection-indicator ${connected ? "online" : ""}`} /> {connected ? "Dados transmitidos via WebSocket" : "Aguardando conexão WebSocket"}</span>
          <span>Sentinela Network Monitor <b>·</b> Projeto acadêmico</span>
        </footer>
      </section>

      {notice && (
        <div className={`toast ${notice.kind}`} role="status">
          <span>{notice.kind === "success" ? <Check size={17} /> : <CircleHelp size={17} />}</span>
          {notice.text}
          <button type="button" aria-label="Fechar notificação" onClick={() => setNotice(null)}><X size={15} /></button>
        </div>
      )}
    </main>
  );
}
