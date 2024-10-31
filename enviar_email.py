import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def enviar_email_almoxarifado(destinatario, assunto, corpo):
  """Envia um email do almoxarifado via Gmail.

  Args:
    destinatario: Endereço de email do destinatário.
    assunto: Assunto do email (ex: Aviso de baixa de estoque, Novo pedido, etc.).
    corpo: Corpo do email com as informações relevantes.
  """

  remetente = "almoxarifadoinvent@gmail.com"
  senha = "gcor mxmo spfz sowq"

  # Cria a mensagem
  mensagem = MIMEMultipart()
  mensagem['From'] = remetente
  mensagem['To'] = destinatario
  mensagem['Subject'] = assunto

  # Corpo do email
  parte_texto = MIMEText(corpo, 'plain')
  mensagem.attach(parte_texto)

  # Conecta ao servidor SMTP do Gmail e envia o email
  with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.starttls()
    smtp.login(remetente, senha)
    smtp.sendmail(remetente, destinatario, mensagem.as_string())

# Exemplo de uso para aviso de baixa de estoque:
enviar_email_almoxarifado("octavio.freitas4275@gmail.com", "Aviso de Baixa de Estoque", 
                          "O item 'Parafuso Phillips M5' está com o estoque abaixo do mínimo. Favor realizar a compra.")