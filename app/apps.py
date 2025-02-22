from django.apps import AppConfig
import os

scheduler_initialized = False

class AppConfig(AppConfig):
    name = 'app'

    def ready(self):
        global scheduler_initialized
         
        if scheduler_initialized or os.environ.get('RUN_MAIN') != 'true':
            return
        #Só inicia o scheduler no ambiente local, pois na Railway ele já é chamado no wsgi.py
        if not os.environ.get('RAILWAY_ENVIRONMENT_NAME'):
            try:
                from app.scheduler import start_scheduler
                start_scheduler()
                scheduler_initialized = True
                print("✅ Scheduler iniciado com sucesso (Local)!")
            except Exception as e:
                print(f"❌ Erro ao iniciar o scheduler: {e}")
         
