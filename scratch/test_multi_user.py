import os
import sys
from datetime import datetime

# Adiciona a pasta backend no PATH do Python
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

import security
from database import SessionLocal, User, Job, Application, init_db

def run_test():
    print("[INFO] Iniciando Teste de Isolamento Multi-Usuario (Fase 2)...")
    init_db()
    db = SessionLocal()
    
    email_a = "candidato_a_teste@vagasync.com.br"
    email_b = "candidato_b_teste@vagasync.com.br"
    
    try:
        # 1. Limpar testes anteriores se existirem
        db.query(User).filter(User.email.in_([email_a, email_b])).delete(synchronize_session=False)
        db.commit()
        
        # 2. Criar Candidato A
        pass_a = security.hash_password("senhaA123")
        user_a = User(email=email_a, password_hash=pass_a, name="Candidato A", role="candidate")
        db.add(user_a)
        
        # 3. Criar Candidato B
        pass_b = security.hash_password("senhaB123")
        user_b = User(email=email_b, password_hash=pass_b, name="Candidato B", role="candidate")
        db.add(user_b)
        db.commit()
        
        print("[OK] Usuarios A e B criados com sucesso.")
        
        # 4. Atualizar curriculo isolado do Candidato A
        user_a.resume_text = "Curriculo do Candidato A: Expert em Python e DevOps."
        db.commit()
        
        # Recarrega do banco
        db.refresh(user_a)
        db.refresh(user_b)
        
        assert user_a.resume_text == "Curriculo do Candidato A: Expert em Python e DevOps."
        assert user_b.resume_text is None
        print("[OK] Isolamento de Curriculo validado: Curriculo de A nao afetou B.")
        
        # 5. Criar um Job global de teste
        job = Job(
            title="Desenvolvedor backend Python",
            company="Google DeepMind",
            location="Remoto",
            link="https://google.com/jobs/deepmind-python",
            source="linkedin",
            description="Vaga para testar isolamento de candidaturas."
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # 6. Candidatar o Candidato A à vaga (criar entrada em Application)
        app_a = Application(
            candidate_id=user_a.id,
            job_id=job.id,
            status="applied",
            applied_at=datetime.utcnow()
        )
        db.add(app_a)
        db.commit()
        
        # 7. Validar isolamento de candidaturas
        # Busca candidaturas de A
        app_check_a = db.query(Application).filter(Application.candidate_id == user_a.id, Application.job_id == job.id).first()
        # Busca candidaturas de B
        app_check_b = db.query(Application).filter(Application.candidate_id == user_b.id, Application.job_id == job.id).first()
        
        assert app_check_a is not None
        assert app_check_a.status == "applied"
        assert app_check_b is None
        
        print("[OK] Isolamento de Status de Candidaturas validado: Vaga aplicada por A esta livre/found para B.")
        print("[SUCCESS] TODOS OS TESTES PASSARAM COM SUCESSO!")
        
    except AssertionError as err:
        print(f"[FAIL] TEST ERROR: Assercao falhou! {err}")
    except Exception as e:
        print(f"[FAIL] TEST ERROR: Ocorreu uma excecao inesperada! {e}")
    finally:
        # Limpa dados do banco
        db.query(User).filter(User.email.in_([email_a, email_b])).delete(synchronize_session=False)
        db.query(Application).filter(Application.candidate_id.in_([user_a.id if 'user_a' in locals() else -1, user_b.id if 'user_b' in locals() else -1])).delete(synchronize_session=False)
        if 'job' in locals():
            db.query(Job).filter(Job.id == job.id).delete(synchronize_session=False)
        db.commit()
        db.close()

if __name__ == "__main__":
    run_test()
