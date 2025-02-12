# eventos/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apscheduler.triggers.date import DateTrigger
from .models import Evento
from datetime import datetime
import pytz
from app.scheduler import scheduler


@receiver(post_save, sender=Evento)
def pos_save_evento(sender, instance, created, **kwargs):
    if created and instance.scheduled_date:
        # o trigger agenda o horário
        trigger = DateTrigger(run_date=instance.scheduled_date, timezone=pytz.UTC)
        # add tarefa ao scheduler
        scheduler.add_job(
            func=notificar_evento,
            trigger=trigger,
            args=[instance.id],
            id=f"evento-{instance.id}",
            replace_existing=True,
        )
        print(f"Evento {instance.id} agendado para {instance.scheduled_date}")


@receiver(post_delete, sender=Evento)
def pos_delete_evento(sender, instance, **kwargs):
    # remove a task agendada ao deletar o evento
    job_id = f"evento-{instance.id}"
    try:
        job = scheduler.get_job(job_id)
        if job:
            scheduler.remove_job(job_id)
    except Exception as e:
        print(f"Erro ao remover a tarefa agendada: {e}")


def notificar_evento(evento_id):
    try:
        evento = Evento.objects.get(id=evento_id)
        print(f"Noficação enviada para o evento: {evento}")
        # lógica de notificação(email ou msg)
    except Evento.DoesNotExist:
        print(f"Evento {evento_id} não encontrado para notificação.")
