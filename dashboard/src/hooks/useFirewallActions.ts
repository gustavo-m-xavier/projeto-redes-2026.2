import { useState } from "react";

export type FirewallAction = "block" | "unblock";
export type Notice = { kind: "success" | "error"; text: string };

export function useFirewallActions(notify: (notice: Notice) => void) {
  const [token, setToken] = useState(
    () => localStorage.getItem("rede-monitor-token") ?? "",
  );
  const [busyPort, setBusyPort] = useState<number | null>(null);

  async function changeFirewall(
    action: FirewallAction,
    port: number,
  ): Promise<boolean> {
    if (!token.trim()) {
      notify({
        kind: "error",
        text: "Informe o token de autenticação para gerenciar o firewall.",
      });
      return false;
    }

    setBusyPort(port);
    try {
      const response = await fetch(`/firewall/${action}/${port}`, {
        method: "POST",
        headers: { "X-Auth-Token": token.trim() },
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(
          body.detail ?? body.message ?? "Não foi possível aplicar a operação.",
        );
      }
      localStorage.setItem("rede-monitor-token", token.trim());
      notify({
        kind: "success",
        text:
          action === "block"
            ? `Bloqueio aplicado à porta ${port}.`
            : `Regra da porta ${port} removida.`,
      });
      return true;
    } catch (error) {
      notify({
        kind: "error",
        text:
          error instanceof Error
            ? error.message
            : "Erro ao conectar ao servidor.",
      });
      return false;
    } finally {
      setBusyPort(null);
    }
  }

  return { token, setToken, busyPort, changeFirewall };
}
