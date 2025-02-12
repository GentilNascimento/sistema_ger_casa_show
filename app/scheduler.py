from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger 
from django.utils import timezone
import logging
import os
#Configura o logger p monitorar agendador 
logger = logging.getLogger('apscheduler')
logger.setLevel(logging.INFO)

class JobAddedFilter(logging.Filter):
    def filter(self, record):
        # Ignora mensagens sobre jobs adicionados, mas mantém outras mensagens
        return 'Added job' not in record.getMessage()


for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.addFilter(JobAddedFilter())  # Suprime logs de adição de jobs
 

scheduler = BackgroundScheduler()

def start_scheduler():
    if not scheduler.running:
        from artistas.tasks import enviar_mensagens_agendadas, verificar_status
        scheduler.start()
         
        scheduler.add_job(enviar_mensagens_agendadas, 'interval', minutes=1, 
                          id='enviar_mensagens_agendadas', replace_existing=True)
        
        scheduler.add_job(verificar_status, 'interval', minutes=1, 
                          id='verificar_status', replace_existing=True)
 
def scheduler_daily_message(artista_id):
    #define uma task diária p enviar msg.
    #trigger = CronTrigger(hour=9, minute=0)
    trigger = IntervalTrigger(minutes=1)
    scheduler.add_job(enviar_mensagens_agendadas, trigger, args=[artista_id], 
                      id=f"send_message_{artista_id}", replace_existing=True)
     