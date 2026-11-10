# Sentinela — monitoramento e gerenciamento de rede

Sistema acadêmico para acompanhar tráfego e conexões da máquina servidora e gerenciar regras de firewall autorizadas. O servidor e o cliente podem ser executados em computadores físicos diferentes na mesma rede.

## Arquitetura

- **Máquina A — cliente:** gera requisições HTTP e DNS e envia operações de controle por TCP/JSON.
- **Máquina B — servidor:** captura e classifica pacotes, monitora sockets, calcula telemetria, expõe API/WebSocket e gerencia regras TCP do firewall do host.
- **Dashboard:** aplicação React + TypeScript, servida pelo FastAPI no mesmo endereço da API. Usa WebSocket para receber atualizações e não requer um terceiro serviço em produção.

O código segue uma separação em camadas para manter regras de aplicação independentes dos frameworks e do sistema operacional:

- `server/app/domain`: contratos (ports) consumidos pela aplicação.
- `server/app/application`: casos de uso de monitoramento, controle remoto e firewall.
- `server/app/infrastructure`: adaptadores Scapy, Psutil, telemetria em memória e backends iptables/nftables/Windows Defender Firewall.
- `server/app/presentation`: API HTTP/WebSocket e servidor TCP.
- `server/app/main.py`: composition root que instancia e conecta os adaptadores.
- `client/app/application`: fluxo de demonstração e contratos do cliente.
- `client/app/infrastructure`: geração de tráfego e cliente TCP.
- `dashboard/src/components`, `hooks`, `shared`: UI por funcionalidade, estado de integração e utilitários compartilhados.

Os serviços de aplicação recebem suas dependências por construtor, usando contratos estruturais (`Protocol`) no servidor e no cliente. Isso permite testar regras e fluxos sem iniciar captura real ou alterar o firewall.

O dashboard permite filtrar pacotes por IP, domínio, porta e protocolo, acompanhar conexões/portas em escuta e bloquear/liberar regras gerenciadas pelo sistema. O token para operações do firewall é digitado no painel e guardado somente no armazenamento local do navegador.

## Tecnologias

Python 3.11, Scapy, Psutil, FastAPI, Uvicorn, sockets TCP, React, TypeScript, Vite, Recharts e Docker Compose.

## Requisitos

- Docker Engine e Docker Compose para executar o servidor em Linux.
- Máquina B Linux ou Windows; a captura de pacotes exige uma interface de rede disponível ao Scapy.
- No Windows, instale o Npcap e execute o servidor em um terminal elevado para permitir alterações no Windows Defender Firewall.
- Acesso à rede entre as máquinas nas portas TCP configuradas em `SERVER_PORT` e `API_PORT`.
- O serviço em `FIREWALL_DEMO_PORT` deve estar escutando e acessível antes da demonstração; por padrão, essa variável usa `API_PORT`.
- Para executar localmente o frontend em desenvolvimento: Node.js 20 ou superior.

## Executar em dois computadores

Gere um token aleatório longo (por exemplo, `openssl rand -hex 32`) e configure um `.env` **separado em cada computador**, copiando `.env.example`. Preencha `AUTH_TOKEN` com o mesmo valor nos dois arquivos; o Compose não inicia com o token vazio.

### Máquina B — servidor

Configure `.env` na máquina B:

```dotenv
SERVER_HOST=0.0.0.0
SERVER_PORT=9000
API_PORT=8000
AUTH_TOKEN=<token-aleatorio-longo>
NETWORK_INTERFACE=eth0
```

Descubra a interface adequada com `ip addr` e substitua `eth0` se necessário. Depois inicie somente o servidor:

```bash
docker compose up --build server
```

Abra `http://<IP-DA-MAQUINA-B>:8000` para acessar o dashboard. A API fica no mesmo endereço, por exemplo `http://<IP-DA-MAQUINA-B>:8000/health`.

### Máquina A — cliente

Configure `.env` na máquina A com o IP real da máquina B:

```dotenv
SERVER_HOST=192.168.0.10
SERVER_PORT=9000
API_PORT=8000
AUTH_TOKEN=<o-mesmo-token-da-maquina-B>
```

Inicie somente o cliente:

```bash
docker compose up --build client
```

O cliente executa a demonstração de tráfego e controle uma vez e permanece ativo. O serviço de cliente não depende de um servidor Compose local: ele se conecta ao endereço físico informado em `SERVER_HOST`.

> O servidor usa `network_mode: host` para observar a rede do host e aplicar regras no firewall do host. O Compose restringe as capabilities a `NET_RAW` e `NET_ADMIN`; não utiliza modo privilegiado. Garanta que o firewall da máquina B permita as portas de controle/API somente conforme necessário.

## Teste entre as duas máquinas

1. Conecte as máquinas à mesma rede e confirme que a máquina A consegue alcançar o IP da máquina B.
2. Na máquina B, descubra o IP e o nome da interface com `ip addr`. Configure `NETWORK_INTERFACE` com a interface conectada à rede; não use `lo` para o teste físico.
3. Configure `SERVER_HOST=0.0.0.0` no `.env` da máquina B. Na máquina A, configure `SERVER_HOST` com o IP real da máquina B. Use o mesmo `AUTH_TOKEN` nos dois arquivos.
4. Na máquina B, execute `docker compose up --build -d server`. Confirme a inicialização com `docker compose ps` e `docker compose logs -f server`.
5. Da máquina A, abra `http://<IP-DA-MAQUINA-B>:8000/health` no navegador ou execute `curl http://<IP-DA-MAQUINA-B>:8000/health`. A resposta esperada contém `"status":"ok"`.
6. Abra `http://<IP-DA-MAQUINA-B>:8000` para o dashboard. Use **Configurar token** no painel e informe o `AUTH_TOKEN`.
7. Na máquina A, execute `docker compose up --build client` e observe a saída do cliente. No dashboard da máquina B, confira os totais de tráfego, os pacotes TCP e as conexões ao servidor.
8. A demonstração bloqueia temporariamente o serviço da porta `FIREWALL_DEMO_PORT` (por padrão, a API em TCP/8000), testa o bloqueio e a restauração e encerra com erro se algum resultado não for comprovado. A porta de controle TCP/9000 permanece separada para que a máquina A possa enviar o comando de liberação.

Essa operação afeta o **host B**, não apenas o container. O serviço de demonstração fica inacessível por cerca de dois segundos. Não escolha uma porta com serviço crítico; não interrompa o cliente enquanto a regra estiver aplicada. Se a remoção falhar ou o cliente for encerrado à força, remova a regra gerenciada pelo dashboard ou pelo firewall do host.

### Servidor Docker no WSL2 acessado pela rede local

Quando o servidor roda em Docker dentro do WSL2 no computador Windows B, o IP do WSL (por exemplo, `172.31.x.x`) normalmente não é o endereço que o computador A usa. O computador A conecta ao IPv4 da rede local do Windows B; o Windows encaminha as portas para o IP atual do WSL.

Neste exemplo:

- **Máquina A — cliente:** `192.168.15.11`
- **Máquina B — Windows que executa o servidor:** `192.168.15.17`
- **Máquina B — WSL2:** usle o endereço atua da interface `eth0`; ele pode mudar quando o WSL reiniciar.

Substitua os IPs de exemplo pelos endereços atuais da sua rede. O IP da Máquina B deve ser obtido no Windows com `ipconfig` (adaptador Wi-Fi/Ethernet); o IP do WSL deve ser obtido dentro do WSL. Não use `127.0.0.1`, `docker0` nem o IP da interface virtual do Windows `vEthernet (WSL)` como endereço da Máquina B.

1. **Na Máquina B, inicie o servidor dentro do WSL** e confirme que ele está ouvindo nas portas 8000 e 9000:

   ```bash
   docker compose up --build -d server
   docker compose ps
   ss -lnt | grep -E ':(8000|9000)\b'
   ```

   Anote o IP atual da interface WSL `eth0`:

   ```bash
   ip -4 -o addr show dev eth0
   ```

   Na saída, use o endereço IPv4 antes de `/` (por exemplo, se aparecer `172.31.140.225/20`, o IP do WSL é `172.31.140.225`).

2. **Na Máquina B, abra o PowerShell como administrador.** Defina `$WslIp` com o IPv4 anotado no passo anterior (o endereço abaixo é só um exemplo), remova encaminhamentos anteriores dessas portas, se houver, e crie os novos:

   ```powershell
   $WslIp = "172.31.140.225"
   netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=8000
   netsh interface portproxy delete v4tov4 listenaddress=0.0.0.0 listenport=9000
   netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8000 connectaddress=$WslIp connectport=8000
   netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9000 connectaddress=$WslIp connectport=9000
   ```

   As mensagens de erro dos comandos `delete` podem ser ignoradas se ainda não existia encaminhamento. O encaminhamento precisa ser atualizado se o IP do WSL mudar.

3. **Na Máquina B, permita conexões TCP da Máquina A** no Firewall do Windows. Os comandos abaixo permitem somente o IP da Máquina A (`192.168.15.11`) nas portas da API/dashboard (8000) e de controle (9000):

   ```powershell
   Remove-NetFirewallRule -DisplayName "Sentinela API 8000" -ErrorAction SilentlyContinue
   Remove-NetFirewallRule -DisplayName "Sentinela controle 9000" -ErrorAction SilentlyContinue
   New-NetFirewallRule -DisplayName "Sentinela API 8000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.15.11 -Profile Any
   New-NetFirewallRule -DisplayName "Sentinela controle 9000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 9000 -RemoteAddress 192.168.15.11 -Profile Any
   ```

   Se o IP da Máquina A for diferente, substitua `192.168.15.11` nos dois comandos `New-NetFirewallRule`. Não é necessário liberar ping para o aplicativo funcionar; ping testa ICMP, enquanto o aplicativo usa TCP.

   Se também quiser permitir que a **Máquina A** teste ping para a **Máquina B**, crie esta regra adicional no PowerShell administrador da Máquina B:

   ```powershell
   New-NetFirewallRule -DisplayName "Ping da Maquina A 192.168.15.11" -Direction Inbound -Action Allow -Protocol ICMPv4 -IcmpType 8 -RemoteAddress 192.168.15.11 -Profile Any
   ```

   Essa regra só permite pedidos de ping da Máquina A para a Máquina B; não altera o acesso TCP do aplicativo.

4. **Na Máquina B, teste o encaminhamento local** no PowerShell:

   ```powershell
   Test-NetConnection 127.0.0.1 -Port 8000
   Test-NetConnection 127.0.0.1 -Port 9000
   ```

   Ambos devem mostrar `TcpTestSucceeded: True`.

5. **Na Máquina A, teste o acesso pela rede**. No PowerShell:

   ```powershell
   Test-NetConnection 192.168.15.17 -Port 8000
   Test-NetConnection 192.168.15.17 -Port 9000
   ```

   Se a Máquina A for Linux, pode testar a API com `curl http://192.168.15.17:8000/health` e as portas com `nc -vz 192.168.15.17 8000` e `nc -vz 192.168.15.17 9000`. Os testes TCP devem passar antes de iniciar o cliente.

6. **Na Máquina A, configure o cliente** no `.env`, usando o IPv4 da Máquina B no Windows (não o IP do WSL), e inicie-o:

   ```dotenv
   SERVER_HOST=192.168.15.17
   SERVER_PORT=9000
   API_PORT=8000
   AUTH_TOKEN=<o-mesmo-token-configurado-na-maquina-B>
   ```

   ```bash
   docker compose up --build client
   ```

   O dashboard também fica acessível na Máquina A em `http://192.168.15.17:8000`. Se o servidor ou cliente for reiniciado com IPs diferentes, confira os endereços e atualize o encaminhamento/regra de firewall correspondente.

### Servidor nativo no Windows

Docker Compose continua sendo a opção documentada para o servidor Linux. Para executar o servidor diretamente no Windows, instale Python 3.11, Npcap (com suporte compatível com WinPcap) e as dependências. Descubra a interface reconhecida pelo Scapy com `py -c "from scapy.all import get_if_list; print(get_if_list())"`. Abra PowerShell **como administrador**, configure `.env` na raiz do projeto e inicie:

```powershell
cd server
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SERVER_HOST = "0.0.0.0"
$env:SERVER_PORT = "9000"
$env:API_PORT = "8000"
$env:AUTH_TOKEN = "use-o-mesmo-token-do-cliente"
$env:NETWORK_INTERFACE = "\Device\NPF_{GUID-da-interface}"
python -m app.main
```

O nome de interface deve corresponder a um dos nomes retornados pelo Scapy; substitua o exemplo pelo valor real. O servidor usa `New-NetFirewallRule`/`Remove-NetFirewallRule` via PowerShell e requer privilégios administrativos para bloquear/liberar portas. Autorize previamente, conforme o perfil de rede usado, o tráfego de entrada TCP nas portas de controle e API (9000 e 8000 no exemplo). Não bloqueie a porta de controle. O Windows Defender Firewall aplica a regra de bloqueio a todas as interfaces e perfis.

O cliente pode rodar na máquina A em Windows ou Linux. No Windows, configure e inicie-o em PowerShell:

```powershell
cd client
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:SERVER_HOST = "<IP-da-maquina-B>"
$env:SERVER_PORT = "9000"
$env:API_PORT = "8000"
$env:FIREWALL_DEMO_PORT = "8000"
$env:AUTH_TOKEN = "use-o-mesmo-token-do-servidor"
python -m app.main
```

O cliente valida que o serviço-alvo está acessível antes de pedir o bloqueio.

## Cobertura dos cinco pontos avaliados

1. **Disponibilidade do receptor:** o servidor cria um socket TCP daemon em `SERVER_HOST:SERVER_PORT` (padrão `0.0.0.0:9000`) e atende conexões em threads. No Windows, mantenha o processo em execução e permita a porta no firewall.
2. **Recepção e validação:** o receptor aceita uma linha JSON limitada a 4096 bytes; `ControlService` valida objeto, ação e token, e `FirewallService` valida a porta entre 1 e 65535. A resposta JSON confirma a operação ou informa erro.
3. **Regra dinâmica de bloqueio:** a ação `block` aplica uma regra TCP de entrada para a porta solicitada. Linux usa iptables/nftables; Windows usa `New-NetFirewallRule` com nome gerenciado pela aplicação. A API HTTP e o dashboard usam o mesmo serviço de firewall.
4. **Comprovação do descarte:** antes de bloquear, o cliente confirma que há uma conexão TCP possível para `FIREWALL_DEMO_PORT`; após receber sucesso, tenta novas conexões até confirmar que falharam. O cliente aborta sem alterar o firewall se o serviço já estiver inacessível.
5. **Restauração:** o cliente envia `unblock` pelo canal de controle separado, confirma a remoção e tenta novas conexões até comprovar que o serviço voltou. Qualquer falha de aplicação, descarte ou restauração é informada como erro; a regra é removida em bloco `finally` quando a aplicação do bloqueio foi confirmada.

Para a comprovação padrão, a API em `API_PORT` é o serviço alvo. Se `FIREWALL_DEMO_PORT` for configurada para outra porta (por exemplo, 80), um serviço TCP precisa estar escutando nela antes de iniciar o cliente; o canal de controle deve continuar em outra porta. No log do cliente, procure as mensagens “Comprovado: novas conexões ... foram bloqueadas” e “... foram restauradas”.

### O que esperar da captura

- As chamadas HTTP do cliente para a API na máquina B e o controle TCP devem atravessar a interface da máquina B e aparecer na lista de pacotes quando a captura tiver permissões.
- A consulta DNS que o cliente faz para `example.com` normalmente segue do cliente para seu resolvedor padrão, sem passar pela máquina B. Portanto, ela pode não aparecer na captura do servidor. Para demonstrar DNS no painel, a consulta precisa atravessar uma interface visível ao servidor, por exemplo, com espelhamento de tráfego configurado na rede.
- Em redes com switch, a máquina B não captura automaticamente o tráfego entre outros dispositivos; ela observa o tráfego que chega às suas interfaces.
- Se o painel indicar erro de captura, confira `NETWORK_INTERFACE`, as permissões/capabilities e os logs do serviço. O endpoint `/health` comprova somente que a API está acessível; não garante, por si só, que a captura esteja ativa.

## Desenvolvimento do dashboard

Inicie o servidor localmente com as dependências Python instaladas e, em outro terminal:

```bash
cd dashboard
npm ci
npm run dev
```

Acesse o endereço informado pelo Vite. O proxy de desenvolvimento encaminha `/firewall` e `/ws` para `http://127.0.0.1:8000`. Para gerar os arquivos estáticos de produção:

```bash
npm run build
```

O Dockerfile do servidor já compila o dashboard e o inclui no container final.

## Testes

```bash
PYTHONPATH=server python -m unittest discover -s server/tests -v
PYTHONPATH=client python -m unittest discover -s client/tests -v
cd dashboard && npm run build && npm audit
```

## Dados e interpretação

- O contador de bytes usa o tamanho do pacote IP reportado pelo Scapy para cada pacote capturado uma vez.
- PPS representa a média de pacotes por segundo na janela recente de telemetria.
- O gráfico apresenta os bytes observados por segundo, separados em TCP e UDP, no histórico disponível.
- HTTP é identificado somente quando há payload HTTP legível; conteúdo HTTPS não é descriptografado nem interpretado.
- Captura e gerenciamento de firewall dependem das permissões e do suporte do host. No Linux, o container precisa de `NET_RAW` e `NET_ADMIN`; no Windows, instale Npcap e execute com privilégios administrativos para gerenciar regras. Falhas são retornadas explicitamente.

## Rotas principais

- `GET /health`, `GET /status`, `GET /packets`, `GET /connections`
- `GET /firewall/rules`
- `POST /firewall/block/{port}` e `POST /firewall/unblock/{port}` — exigem `X-Auth-Token`
- `WS /ws` — telemetria, conexões, regras, estado da captura e pacotes recentes

As operações remotas aceitam somente ações predefinidas e portas válidas. A liberação de regras é limitada a regras marcadas como gerenciadas pela aplicação.
