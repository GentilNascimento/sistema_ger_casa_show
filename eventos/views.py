from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic import ListView
# from django.views.generic import DetailView
from . import models, forms
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from app.scheduler import scheduler
from apscheduler.jobstores.base import JobLookupError
from django.db import IntegrityError
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)


class EventoListView(ListView):
    model = models.Evento
    template_name = 'evento_list.html'
    context_object_name = 'eventos'
    ordering = ['-scheduled_date']


@method_decorator(login_required(login_url='login'), name='dispatch')
class EventoCreateView(CreateView):
    model = models.Evento
    template_name = 'evento_create.html'
    form_class = forms.EventoForm

    def form_valid(self, form):
        try:
            logger.debug(f"Dados do formulário: {form.cleaned_data}")  # Adicionando para manter coerência
            self.object = form.save()
            messages.success(
                self.request,
                f'Evento do Artista "{self.object.artista.nome}" criado com sucesso para: {self.object.scheduled_date.strftime("%d/%m/%Y %H:%M")}!'
            )
            return redirect('evento_create')
        except IntegrityError:
            messages.error(self.request, 'Erro ao criar evento. Verifique os dados e tente novamente.')
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao criar evento. Verifique os dados e tente novamente.')
        return self.render_to_response(self.get_context_data(form=form))


'''
class EventoDetailView(DetailView):
    model = models.Evento
    template_name = 'evento_detail.html'
'''


@method_decorator(login_required(login_url='login'), name='dispatch')
class EventoUpdateView(UpdateView):
    model = models.Evento
    template_name = 'evento_update.html'
    form_class = forms.EventoForm
    success_url = reverse_lazy('evento_list')


@method_decorator(login_required(login_url='login'), name='dispatch')
class EventoDeleteView(DeleteView):
    model = models.Evento
    template_name = 'evento_delete.html'
    success_url = reverse_lazy('evento_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        messages.success(request, f'Evento "{self.object.descricao}" excluído com sucesso!')
        return super().delete(request, *args, **kwargs)
