import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

application = get_wsgi_application()

#Força a inicialização do scheduler apenas na Railway
if os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production' or os.environ.get('RENDER_EXTERNAL_HOSTNAME'):  
    from app.scheduler import start_scheduler
    start_scheduler()
