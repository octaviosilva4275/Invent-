from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()  # Carregar variáveis do .env

# Codigo para autentificação

account_sid = "ACc1f8fd89246833c6ec94946e9addeb12"

auth_token = "72fd4f9768bcbe85fbbe65d0093280af"
client = Client(account_sid, auth_token)

message = client.messages.create(
    to="+5516992360708",
    from_="+12542216778",
    body=f'Mensagem enviada')
print(message.sid)