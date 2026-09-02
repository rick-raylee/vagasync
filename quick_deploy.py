# -*- coding: utf-8 -*-
"""
VagaSync Quick Deploy -- Envia apenas os arquivos atualizados (frontend dist + backend) para o VPS.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import time

try:
    import paramiko
    from paramiko import SSHClient, AutoAddPolicy
    from scp import SCPClient
except ImportError:
    print("ERRO: pip install paramiko scp")
    sys.exit(1)

HOST     = "vps68375.publiccloud.com.br"
PORT     = 22
USER     = "root"
PASSWORD = "153426Ri@"

FRONTEND_DIST_LOCAL = r"C:\Users\ricar\Desktop\VAGASYNC\frontend\dist"
BACKEND_LOCAL       = r"C:\Users\ricar\Desktop\VAGASYNC\backend"

GREEN = "\033[92m"; CYAN = "\033[96m"; RED = "\033[91m"; RESET = "\033[0m"

def log(msg, color=CYAN): print(f"{color}{msg}{RESET}", flush=True)

def run(ssh, cmd, check=True, timeout=120):
    log(f"  $ {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out:
        for line in out.splitlines(): print(f"    {line}", flush=True)
    if err:
        for line in err.splitlines(): print(f"    [err] {line}", flush=True)
    return ec, out, err

def main():
    log("=" * 55)
    log("  [DEPLOY] VagaSync Quick Deploy")
    log("=" * 55)

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=30)
    log("  [OK] Conectado!", GREEN)

    log("\n[1/4] Enviando frontend dist ...")
    with SCPClient(ssh.get_transport()) as scp:
        scp.put(FRONTEND_DIST_LOCAL, remote_path="/opt/vagasync/frontend/", recursive=True)
    log("  [OK] Frontend enviado!", GREEN)

    log("\n[2/4] Enviando backend (excluindo venv e banco de dados) ...")
    sftp = ssh.open_sftp()
    
    import os
    def sftp_put_dir(local_dir, remote_dir):
        try:
            sftp.mkdir(remote_dir)
        except IOError:
            pass  # Já existe
            
        for item in os.listdir(local_dir):
            if item in ['venv', 'venv_linux', '__pycache__', '.git', 'vagasync.db', '.env']:
                continue
            local_path = os.path.join(local_dir, item)
            remote_path = remote_dir + '/' + item
            if os.path.isdir(local_path):
                sftp_put_dir(local_path, remote_path)
            else:
                sftp.put(local_path, remote_path)

    sftp_put_dir(BACKEND_LOCAL, "/opt/vagasync/backend")
    sftp.close()
    log("  [OK] Backend enviado!", GREEN)

    log("\n[3/4] Instalando dependencias Python ...")
    run(ssh, "cd /opt/vagasync/backend && ./venv/bin/pip install -r requirements.txt -q", timeout=180, check=False)

    log("\n[4/4] Reiniciando backend ...")
    run(ssh, "systemctl restart vagasync-backend")
    time.sleep(2)
    run(ssh, "systemctl is-active vagasync-backend", check=False)

    log("\n" + "=" * 55)
    log("  [SUCESSO] Deploy concluido!", GREEN)
    log("=" * 55)
    log("  https://vagasync.com.br")
    log("  https://www.vagasync.com.br")
    ssh.close()

if __name__ == "__main__":
    main()
