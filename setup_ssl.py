# -*- coding: utf-8 -*-
"""
VagaSync SSL Setup -- Instala Certbot e configura HTTPS no VPS.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import time

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
except ImportError:
    print("ERRO: pip install paramiko")
    sys.exit(1)

HOST     = "vps68375.publiccloud.com.br"
PORT     = 22
USER     = "root"
PASSWORD = "153426Ri@"

CYAN  = "\033[96m"
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, color=CYAN):
    print(f"{color}{msg}{RESET}", flush=True)

def run(ssh, cmd, check=True, timeout=120):
    log(f"  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        for line in out.splitlines():
            print(f"    {line}", flush=True)
    if err:
        for line in err.splitlines():
            print(f"    [err] {line}", flush=True)
    if check and exit_code != 0:
        log(f"  AVISO: exit code {exit_code}", YELLOW)
    return exit_code, out, err

def main():
    log("=" * 60)
    log("  [SSL] VagaSync HTTPS Setup com Let's Encrypt")
    log("=" * 60)

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    log(f"\n[1/5] Conectando ao VPS {HOST} ...")
    try:
        ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)
        log("  [OK] Conectado!", GREEN)
    except Exception as e:
        log(f"  ERRO: {e}", RED)
        sys.exit(1)

    log("\n[2/5] Verificando dominio e IP publico do VPS ...")
    run(ssh, "curl -s https://api.ipify.org || hostname -I | awk '{print $1}'", check=False)
    
    log("\n[3/5] Instalando Certbot + plugin nginx ...")
    run(ssh, "apt-get update -qq", timeout=180)
    run(ssh, "apt-get install -y certbot python3-certbot-nginx -qq", timeout=300, check=False)
    
    # Verifica se certbot foi instalado
    ec, out, _ = run(ssh, "certbot --version", check=False)
    if ec != 0:
        log("  Tentando via snap ...", YELLOW)
        run(ssh, "snap install --classic certbot", timeout=180, check=False)
        run(ssh, "ln -sf /snap/bin/certbot /usr/bin/certbot", check=False)

    log("\n[4/5] Emitindo certificado SSL para vagasync.com.br ...")
    log("  (Isso pode levar 1-2 minutos...)", YELLOW)
    
    # Tenta emitir cert para os dominios
    cmd_certbot = (
        "certbot --nginx "
        "-d vagasync.com.br "
        "-d www.vagasync.com.br "
        "--non-interactive "
        "--agree-tos "
        "--email contato@vagasync.com.br "
        "--redirect "
        "2>&1"
    )
    ec, out, err = run(ssh, cmd_certbot, check=False, timeout=180)
    
    if ec == 0:
        log("  [OK] Certificado SSL emitido com sucesso!", GREEN)
    else:
        log("  AVISO: Certbot retornou erro. Verificando causa...", YELLOW)
        # Verifica se o dominio aponta para o VPS
        run(ssh, "dig +short vagasync.com.br || nslookup vagasync.com.br", check=False)
        log("  O dominio vagasync.com.br precisa apontar para o IP deste VPS.", YELLOW)
        log("  Tente configurar o DNS e rode certbot manualmente depois.", YELLOW)

    log("\n[5/5] Status final dos servicos ...")
    run(ssh, "systemctl is-active vagasync-backend", check=False)
    run(ssh, "systemctl is-active nginx", check=False)
    run(ssh, "nginx -t", check=False)
    
    # Mostra certificados instalados
    run(ssh, "certbot certificates 2>&1", check=False, timeout=30)

    log("\n" + "=" * 60)
    log("  [CONCLUIDO] Configuracao SSL finalizada!", GREEN)
    log("=" * 60)
    log(f"  HTTP:  http://vagasync.com.br")
    log(f"  HTTPS: https://vagasync.com.br")
    log(f"  HTTPS: https://www.vagasync.com.br")
    log(f"  VPS:   http://vps68375.publiccloud.com.br")

    ssh.close()

if __name__ == "__main__":
    main()
