const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', () => {
  console.log('Connected to VPS.');
  
  // 1. Zera a chave resume_text no SQLite de produção
  // 2. Reinicia o backend Python para desativar qualquer execução em andamento na memória
  const command = `sqlite3 /var/www/vagasync/backend/vagasync.db "UPDATE configs SET value = '' WHERE key = 'resume_text';" && systemctl restart vagasync-backend && echo "SUCCESS"`;
  
  console.log('Running reset commands...');
  conn.exec(command, (err, stream) => {
    if (err) {
      console.error('Command execution failed', err);
      conn.end();
      return;
    }
    
    stream.on('close', (code) => {
      console.log(`Command closed with code ${code}`);
      conn.end();
    }).on('data', (data) => {
      console.log('STDOUT:', data.toString());
    }).stderr.on('data', (data) => {
      console.error('STDERR:', data.toString());
    });
  });
}).on('error', (err) => {
  console.error('SSH Connection Error', err);
}).connect({
  host: '200.234.212.34',
  port: 22,
  username: 'root',
  password: 'Vagasync2026#'
});
