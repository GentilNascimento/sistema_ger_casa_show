import logging
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re 
from validate_docbr import CPF

 
 
logger = logging.getLogger('artistas')

class Artista(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=15, null=True, blank=True)
    banco = models.CharField(max_length=100)
    tipo_chave_pix = models.CharField(
        max_length=10,
        choices=[
            ('cel', 'Celular'),
            ('email', 'E-mail'),
            ('cpf', 'CPF')
        ],
        default='cel'
    )
    chave_pix = models.CharField(max_length=100)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def validar_cpf(self):
        cpf_validator = CPF()
        if not cpf_validator.validate(self.cpf):
            raise ValidationError("CPF inválido.")
    
    def validar_email(self):
        if self.email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', self.email):
            raise ValidationError("E-mail inválido.")
        
    def validar_chave_pix(self):
        if self.chave_pix:
            if self.tipo_chave_pix == 'cel':
                if not re.match(r'^\+?\d{11,15}$', self.chave_pix):  # Garante formato correto do número com ou sem '+'
                    raise ValidationError("A chave Pix deve ser um número de celular válido com código do país.")
            elif self.tipo_chave_pix == 'email':
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', self.chave_pix):  # Validação básica de e-mail
                    raise ValidationError("A chave Pix deve ser um e-mail válido.")
            elif self.tipo_chave_pix == 'cpf':
                cpf_validator = CPF()
                if not cpf_validator.validate(self.chave_pix):  # Usa validação específica de CPF
                    raise ValidationError("A chave Pix deve ser um CPF válido com 11 dígitos.")

    def clean(self):
        self.validar_cpf()
        self.validar_email()
        self.validar_chave_pix()

    def save(self, *args, **kwargs):
        self.full_clean()  # Garante que as validações sejam aplicadas antes de salvar
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    """
    Verificar se o artista tem informações incompletas ou inativas.
    """
    def deve_ser_atualizado(self):
        if self.tipo_chave_pix == 'email':
            campos_obrigatorios = [self.telefone, self.chave_pix]
        else:
            campos_obrigatorios = [self.telefone]
            
        return any(campo is None or campo == '' for campo in campos_obrigatorios)
    """
    Atualiza o status do artista.
    """ 
    def atualizar_status(self):
        if self.deve_ser_atualizado():
            logger.info(f"Artista {self.id} com informações incompletas.")
            self.save()
         

class Message(models.Model):
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE)
    conteudo = models.TextField()
    scheduled_date = models.DateTimeField(auto_now_add=True, verbose_name="Data Agendada")
    send_date = models.DateTimeField(default=timezone.now, verbose_name="Data de Envio")
    sent = models.BooleanField(default=False, verbose_name="Enviada")
    
         
    def save(self, *args, **kwargs):
        self.full_clean()  # Chama o método clean() para validação
        super().save(*args, **kwargs)
   
    def __str__(self):
        return f"Mensagem para {self.artista.nome} agendada para {self.send_date}"
    #A mensagem deve ser enviada se a data de envio é menor ou igual ao horário atual
    #e ainda não foi marcada como enviada.
    
    def deve_enviar(self):
        return self.send_date <= timezone.now() and not self.sent
    
    #lógica de envio das msg.
    def enviar(self):
        if self.sent:
            return  #impede o reenvio        
        try:
            #Simula o envio da msg
            self.sent = True   #atualiza o status p envio
            self.save()   #persiste a alteração no Bd
            
            logger.info(f"Mensagem ID {self.id} enviada com sucesso para o artista {self.artista.nome}.")
             
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem ID {self.id}: {e}")
            raise e #propaga a exceção p depuração
         
            
    def deve_ser_atualizado(self):
    # Verifica se a mensagem não foi enviada e se a data de envio passou.
        return not self.sent and self.send_date < timezone.now() 
       
    def atualizar_status(self):
        # Verifica se a msg ainda não foi env e já passou da hora de envio
        agora = timezone.now()
        if not self.sent and self.send_date < timezone.now():
            # Verifica se o envio foi tentado recentemente
            ultima_tentativa_envio = timezone.now() - timezone.timedelta(minutes=1)   
            mensagens_recem_enviadas = Message.objects.filter(
                id=self.id, send_date__gte=ultima_tentativa_envio)
            
            if not mensagens_recem_enviadas.exists():
                logger.warning(f"Mensagem {self.id} está atrasada.")                    
                self.sent = False  #Assegura q mensagem permanece ñ enviada.
                self.save()
                    
                       
    @property
    def status(self):
        #retorna o status atual da msg
        if self.sent:
            return "Enviada"
        if not self.sent and self.send_date < timezone.now():
            return "Atrasada"
        return "Pendente"
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"