import json
import re
import shutil
import subprocess


class WindowsFirewallBackend:
    RULE_PREFIX = "RedesMonitor-TCP-In-"

    @staticmethod
    def _run(script: str) -> subprocess.CompletedProcess:
        executable = next(
            (
                path
                for name in ("powershell", "powershell.exe", "pwsh")
                if (path := shutil.which(name))
            ),
            None,
        )
        if executable is None:
            raise RuntimeError("PowerShell não foi encontrado para gerenciar o Windows Defender Firewall.")
        return subprocess.run(
            [executable, "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            check=False,
        )

    def block_port(self, port: int) -> dict:
        name = f"{self.RULE_PREFIX}{port}"
        script = (
            "$ErrorActionPreference = 'Stop'; "
            f"$rule = Get-NetFirewallRule -Name '{name}' -ErrorAction SilentlyContinue; "
            "if (-not $rule) { "
            f"New-NetFirewallRule -Name '{name}' -DisplayName '{name}' "
            f"-Direction Inbound -Action Block -Protocol TCP -LocalPort {port} -Profile Any | Out-Null "
            "}"
        )
        self._ensure_success(self._run(script), "Falha ao aplicar regra no Windows Defender Firewall.")
        return {"port": port, "status": "blocked", "tool": "Windows Defender Firewall"}

    def unblock_port(self, port: int) -> dict:
        if not any(rule["port"] == port for rule in self.list_rules()):
            raise KeyError(f"Porta {port} não está sendo gerenciada pelo sistema.")

        name = f"{self.RULE_PREFIX}{port}"
        script = (
            "$ErrorActionPreference = 'Stop'; "
            f"Get-NetFirewallRule -Name '{name}' | Remove-NetFirewallRule"
        )
        self._ensure_success(self._run(script), "Falha ao remover regra do Windows Defender Firewall.")
        return {"port": port, "status": "unblocked", "tool": "Windows Defender Firewall"}

    def list_rules(self) -> list[dict]:
        script = (
            "$ErrorActionPreference = 'Stop'; "
            f"$names = @(Get-NetFirewallRule -Name '{self.RULE_PREFIX}*' "
            "-ErrorAction SilentlyContinue | "
            "Where-Object { $_.Direction -eq 'Inbound' -and $_.Action -eq 'Block' } | "
            "ForEach-Object { "
            "$filter = $_ | Get-NetFirewallPortFilter; "
            f"$port = $_.Name.Substring({len(self.RULE_PREFIX)}); "
            "if ($filter.Protocol -eq 'TCP' -and [string]$filter.LocalPort -eq $port) { $_.Name } "
            "}); "
            "ConvertTo-Json -InputObject $names -Compress"
        )
        result = self._run(script)
        self._ensure_success(result, "Falha ao consultar as regras do Windows Defender Firewall.")
        names = json.loads(result.stdout) if result.stdout.strip() else []
        if names is None:
            names = []
        if isinstance(names, str):
            names = [names]

        rules = []
        for name in names:
            match = re.fullmatch(r"RedesMonitor-TCP-In-(\d+)", name)
            if match:
                rules.append(
                    {
                        "port": int(match.group(1)),
                        "status": "managed",
                        "tool": "Windows Defender Firewall",
                    }
                )
        return rules

    @staticmethod
    def _ensure_success(result: subprocess.CompletedProcess, fallback: str) -> None:
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or fallback)
