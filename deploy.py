# -*- coding: utf-8 -*-
"""
VagaSync Deploy Script -- Envia dist + backend para o VPS e reinicia servicos.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import os
import sys
import time

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
    from scp import SCPClient
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

HOST = "vps68375.publiccloud.com.br"
PORT = 22
USER = "root"
PASSWORD = "153426Ri@"

FRONTEND_DIST_LOCAL  = r"C:\Users\ricar\Desktop\VAGASYNC\frontend\dist"
BACKEND_LOCAL        = r"C:\Users\ricar\Desktop\VAGASYNC\backend"

REMOTE_FRONTEND_DIST = "/opt/vagasync/frontend/dist"
REMOTE_BACKEND       = "/opt/vagasync/backend"

CYAN  = "\033[96m"
GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"

def log(msg, color=CYAN):
    print(f"{color}{msg}{RESET}")

def run_remote(ssh, cmd, check=True):
    log(f"  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"    {out}")
    if err: print(f"    [stderr] {err}")
    if check and exit_code != 0:
        log(f"  ERRO (exit {exit_code}): {cmd}", RED)
    return exit_code, out, err

def upload_dir(scp, local_path, remote_path):
    log(f"  Enviando {local_path} → {remote_path} ...")
    scp.put(local_path, remote_path=remote_path, recursive=True)
    log(f"  ✓ Upload concluído!", GREEN)

def main():
    if not HAS_PARAMIKO:
        log("ERRO: paramiko ou scp não instalado. Execute:", RED)
        log("  pip install paramiko scp", RED)
        sys.exit(1)

    log("=" * 60)
    log("  [DEPLOY] VagaSync Deploy --> VPS publiccloud.com.br")
    log("=" * 60)

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    log(f"\n[1/6] Conectando ao VPS {HOST}:{PORT} como {USER} ...")
    try:
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)
        log("  ✓ Conectado com sucesso!", GREEN)
    except Exception as e:
        log(f"  ERRO ao conectar: {e}", RED)
        sys.exit(1)

    log("\n[2/6] Criando estrutura de pastas no VPS ...")
    run_remote(ssh, "mkdir -p /opt/vagasync/frontend/dist /opt/vagasync/backend /opt/vagasync/backend/uploads")

    log("\n[3/6] Enviando frontend (dist) ...")
    try:
        with SCPClient(ssh.get_transport(), progress=lambda fn, sz, sent: None) as scp:
            # Envia conteúdo da pasta dist
            scp.put(FRONTEND_DIST_LOCAL, remote_path="/opt/vagasync/frontend/", recursive=True)
        log("  [OK] Frontend enviado!", GREEN)
    except Exception as e:
        log(f"  ERRO no upload do frontend: {e}", RED)

    log("\n[4/6] Enviando backend ...")
    try:
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(BACKEND_LOCAL, remote_path="/opt/vagasync/", recursive=True)
        log("  [OK] Backend enviado!", GREEN)
    except Exception as e:
        log(f"  ERRO no upload do backend: {e}", RED)

    log("\n[5/6] Instalando dependências Python no VPS ...")
    run_remote(ssh, "cd /opt/vagasync/backend && python3 -m venv venv 2>/dev/null || true")
    run_remote(ssh, "cd /opt/vagasync/backend && ./venv/bin/pip install --upgrade pip -q")
    run_remote(ssh, "cd /opt/vagasync/backend && ./venv/bin/pip install -r requirements.txt -q", check=False)

    log("\n[6/6] Configurando e reiniciando serviços ...")

    # Cria/atualiza o serviço systemd
    service_content = """[Unit]
Description=VagaSync Backend (FastAPI/Uvicorn)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vagasync/backend
Environment=PYTHONUNBUFFERED=1
Environment=ALLOWED_ORIGINS=https://vagasync.com.br,https://www.vagasync.com.br
Environment=FRONTEND_URL=https://www.vagasync.com.br
Environment=BACKEND_URL=https://www.vagasync.com.br
ExecStart=/opt/vagasync/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    stdin, _, _ = ssh.exec_command("cat > /etc/systemd/system/vagasync-backend.service << 'EOFSERVICE'\n" + service_content + "\nEOFSERVICE")
    stdin.channel.recv_exit_status()

    run_remote(ssh, "systemctl daemon-reload")
    run_remote(ssh, "systemctl enable vagasync-backend")
    run_remote(ssh, "systemctl restart vagasync-backend")
    time.sleep(3)
    run_remote(ssh, "systemctl is-active vagasync-backend", check=False)

    # Verifica/cria configuração nginx
    nginx_conf = """server {
    listen 80;
    server_name vagasync.com.br www.vagasync.com.br vps68375.publiccloud.com.br;

    location / {
        root /opt/vagasync/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300;
    }

    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_buffering off;
    }
}
"""
    run_remote(ssh, "apt-get install -y nginx 2>/dev/null || true", check=False)
    cmd_nginx = "cat > /etc/nginx/sites-available/vagasync << 'EOFNGINX'\n" + nginx_conf + "\nEOFNGINX"
    stdin, _, _ = ssh.exec_command(cmd_nginx)
    stdin.channel.recv_exit_status()

    run_remote(ssh, "ln -sf /etc/nginx/sites-available/vagasync /etc/nginx/sites-enabled/vagasync")
    run_remote(ssh, "rm -f /etc/nginx/sites-enabled/default", check=False)
    run_remote(ssh, "nginx -t")
    run_remote(ssh, "systemctl reload nginx || systemctl restart nginx")

    log("\n" + "=" * 60)
    log("  [SUCESSO] DEPLOY CONCLUIDO COM SUCESSO!", GREEN)
    log("=" * 60)
    log(f"  Acesse: http://vps68375.publiccloud.com.br")
    log(f"  API:    http://vps68375.publiccloud.com.br/api/health")
    log(f"\n  Para logs do backend:")
    log(f"  journalctl -u vagasync-backend -f")

    ssh.close()

if __name__ == "__main__":
    main()
