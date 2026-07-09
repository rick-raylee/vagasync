# TODO — Correção: clique na vaga de recrutador não deve abrir LinkedIn

- [x] Atualizar `backend/main.py`: ao retornar `/api/jobs`, normalizar `link` para vagas de recrutador usando `https://vagasync.com.br/vagas/{job.id}`.
- [x] Rodar backend (ou testes rápidos) para garantir que `/api/jobs` responde com `link` normalizado.
- [x] Validar manualmente no frontend: clicar numa vaga de recrutador não abre LinkedIn.
