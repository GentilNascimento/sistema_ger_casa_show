# eventos/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Evento
 
 


@receiver(post_save, sender=Evento)
def pos_save_evento(sender, instance, created, **kwargs):
    if created:
        print(f"✅ Evento {instance.id} criado e registrado como job: evento-{instance.id}")

         


@receiver(post_delete, sender=Evento)
def pos_delete_evento(sender, instance, **kwargs):
    # remove a task agendada ao deletar o evento
    print(f"Evento {instance.id} foi deletado do banco.")
    
     

 