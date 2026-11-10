import { useState } from "react";
import { Check, LockKeyhole, ShieldAlert, ShieldCheck } from "lucide-react";
import type { FirewallRule } from "../../types";
import type { FirewallAction, Notice } from "../../hooks/useFirewallActions";

function FirewallRuleRow({
  rule,
  busy,
  onUnblock,
}: {
  rule: FirewallRule;
  busy: boolean;
  onUnblock: () => void;
}) {
  return (
    <div className="firewall-rule">
      <span className="rule-status" />
      <span>
        <b>{rule.port ? `TCP/${rule.port}` : rule.rule ?? "Regra gerenciada"}</b>
        <small>{rule.tool ?? "firewall"} · bloqueio ativo</small>
      </span>
      {rule.port && <button type="button" disabled={busy} onClick={onUnblock}>{busy ? "Aguarde…" : "Liberar"}</button>}
    </div>
  );
}

export function FirewallPanel({
  rules,
  token,
  onTokenChange,
  busyPort,
  onAction,
  notify,
}: {
  rules: FirewallRule[];
  token: string;
  onTokenChange: (token: string) => void;
  busyPort: number | null;
  onAction: (action: FirewallAction, port: number) => Promise<boolean>;
  notify: (notice: Notice) => void;
}) {
  const [port, setPort] = useState("8080");
  const [showToken, setShowToken] = useState(false);

  async function runAction(action: FirewallAction, targetPort: number) {
    if (!token.trim()) {
      notify({ kind: "error", text: "Informe o token de autenticação para gerenciar o firewall." });
      setShowToken(true);
      return;
    }
    await onAction(action, targetPort);
  }

  function submitPort(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsedPort = Number(port);
    if (!Number.isInteger(parsedPort) || parsedPort < 1 || parsedPort > 65535) {
      notify({ kind: "error", text: "A porta deve ser um número inteiro entre 1 e 65535." });
      return;
    }
    void runAction("block", parsedPort);
  }

  return (
    <section className="panel firewall-panel" id="firewall">
      <div className="panel-heading">
        <div className="firewall-title-wrap">
          <span className="firewall-icon"><ShieldCheck size={19} /></span>
          <div><div className="panel-title">Gerenciamento de firewall</div><div className="panel-subtitle">Regras criadas e controladas por este sistema</div></div>
        </div>
        <button className="token-toggle" type="button" onClick={() => setShowToken(!showToken)}>
          <LockKeyhole size={14} /> {showToken ? "Ocultar token" : "Configurar token"}
        </button>
      </div>
      {showToken && (
        <div className="token-row">
          <label htmlFor="auth-token">Token de autenticação</label>
          <input
            id="auth-token"
            type="password"
            autoComplete="current-password"
            placeholder="AUTH_TOKEN configurado no servidor"
            value={token}
            onChange={(event) => onTokenChange(event.target.value)}
          />
          <span>Armazenado somente neste navegador.</span>
        </div>
      )}
      <div className="firewall-body">
        <form className="block-form" onSubmit={submitPort}>
          <label htmlFor="firewall-port">Bloquear porta TCP</label>
          <div className="form-controls">
            <input id="firewall-port" type="number" min="1" max="65535" value={port} onChange={(event) => setPort(event.target.value)} />
            <button type="submit" disabled={busyPort !== null}><ShieldAlert size={15} /> Bloquear</button>
          </div>
          <small>Regras afetam o firewall do host servidor.</small>
        </form>
        <div className="rule-list">
          <div className="rule-list-title">REGRAS GERENCIADAS <span>{rules.length}</span></div>
          {rules.map((rule, index) => (
            <FirewallRuleRow
              key={`${rule.port ?? rule.rule}-${index}`}
              rule={rule}
              busy={busyPort === rule.port}
              onUnblock={() => rule.port && void runAction("unblock", rule.port)}
            />
          ))}
          {rules.length === 0 && <div className="no-rules"><Check size={15} /> Nenhuma regra ativa criada pela aplicação.</div>}
        </div>
      </div>
    </section>
  );
}
