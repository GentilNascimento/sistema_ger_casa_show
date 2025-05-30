✌️Nome do Projeto: APP (Sistema web de gerenciamento casa de shows)

-Criamos um controle de cadastro de pessoas, com os campos de: 
'nome','cpf', 'telefone', 'banco', 'chave pix', 'tipo chave'.

-Todo dia a meia noite, o sistema faz uma varredura nas msgs.

-Agendamento de: data e hora, e mensagens p watsap.

-Monitorar as mensagens, e quando tiver; disparar pro cel agendado.

-Monitorar as msg já enviadas, para não reenvia-las novamente.

1-Criado em Python e Django com o comando(django-admin startproject app).

2-Ambiente virtual: (dhenv).

3-Criado as pastas (accounts, artistas, eventos) e (app) como aplicativo principal.

4-Usamos: APScheduler para controle de msg, e vamos usar o swager
pra documentar API.
