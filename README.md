# Sentinela — monitoramento e gerenciamento de rede

Sistema acadêmico para acompanhar tráfego e conexões da máquina servidora e gerenciar regras de firewall autorizadas. O servidor e o cliente podem ser executados em computadores físicos diferentes na mesma rede.

## Arquitetura

- **Máquina A — cliente:** gera requisições HTTP e DNS e envia operações de controle por TCP/JSON.
- **Máquina B — servidor:** captura e classifica pacotes, monitora sockets, calcula telemetria, expõe API/WebSocket e gerencia regras TCP do firewall do host.
- **Dashboard:** aplicação React + TypeScript, servida pelo FastAPI no mesmo endereço da API. Usa WebSocket para receber atualizações e não requer um terceiro serviço em produção.

O código segue uma separação em camadas para manter regras de aplicação independentes dos frameworks e do sistema operacional:

- `server/app/domain`: contratos (ports) consumidos pela aplicação.
- `server/app/application`: casos de uso de monitoramento, controle remoto e firewall.
- `server/app/infrastructure`: adaptadores Scapy, Psutil, telemetria em memória e backends iptables/nftables.
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

- Docker Engine e Docker Compose nas máquinas Linux.
- Máquina B Linux, com uma interface de rede para captura.
- Acesso à rede entre as máquinas nas portas TCP configuradas em `SERVER_PORT` e `API_PORT`.
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
8. Para testar o gerenciamento do firewall, primeiro confirme que bloquear TCP/8080 é seguro no host B e use uma porta de teste sem serviço importante. É possível executar o teste pelo dashboard, que oferece bloqueio e liberação separados.

O cliente também tenta bloquear TCP/8080 por cerca de dois segundos e depois liberar a regra automaticamente. Essa operação afeta o **host B**, não apenas o container. Não execute o cliente se a porta 8080 estiver em uso por um serviço que precise continuar acessível. Não interrompa o cliente durante esse intervalo; depois confirme no dashboard que não há regra ativa.

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
cd dashboard && npm run build && npm audit
```

## Dados e interpretação

- O contador de bytes usa o tamanho do pacote IP reportado pelo Scapy para cada pacote capturado uma vez.
- PPS representa a média de pacotes por segundo na janela recente de telemetria.
- O gráfico apresenta os bytes observados por segundo, separados em TCP e UDP, no histórico disponível.
- HTTP é identificado somente quando há payload HTTP legível; conteúdo HTTPS não é descriptografado nem interpretado.
- Captura e gerenciamento de firewall dependem das capabilities e do suporte do kernel/host Linux. Sem permissão, o dashboard informa o erro da captura e as operações de firewall retornam uma falha explícita.

## Rotas principais

- `GET /health`, `GET /status`, `GET /packets`, `GET /connections`
- `GET /firewall/rules`
- `POST /firewall/block/{port}` e `POST /firewall/unblock/{port}` — exigem `X-Auth-Token`
- `WS /ws` — telemetria, conexões, regras, estado da captura e pacotes recentes

As operações remotas aceitam somente ações predefinidas e portas válidas. A liberação de regras é limitada a regras marcadas como gerenciadas pela aplicação.
