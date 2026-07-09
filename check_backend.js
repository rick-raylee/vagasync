const { Client } = require('ssh2');

const conn = new Client();

conn.on('ready', () => {
  console.log('Connected to VPS.');
  conn.exec('pm2 list || systemctl status vagasync || systemctl status gunicorn || systemctl status backend', (err, stream) => {
    if (err) throw err;
    stream.resume();
    stream.on('close', (code) => {
      conn.end();
    }).on('data', (data) => {
      process.stdout.write(data);
    }).stderr.on('data', (data) => {
      process.stderr.write(data);
    });
  });
}).on('error', (err) => {
  console.error(err);
}).connect({
  host: '200.234.212.34',
  port: 22,
  username: 'root',
  password: 'Vagasync2026#'
});
