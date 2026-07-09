const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.join(__dirname, '..', 'backend', 'vagasync.db');
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database', err);
    return;
  }
  console.log('Database opened successfully');
});

db.all("SELECT * FROM configs", [], (err, rows) => {
  if (err) {
    console.error('Error querying configs', err);
    return;
  }
  console.log('--- Configs ---');
  rows.forEach((row) => {
    if (row.key === 'resume_text') {
      console.log(`key: ${row.key}, length: ${row.value ? row.value.length : 0}`);
      console.log(`preview: ${row.value ? row.value.substring(0, 100) : 'null'}`);
    } else {
      console.log(`key: ${row.key}, value: ${row.value}`);
    }
  });
  db.close();
});
