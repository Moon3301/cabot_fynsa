from flask import Flask
from flask_apscheduler import APScheduler
import paramiko
import time
import smtplib
import email
import imaplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re
from PIL import Image, ImageDraw, ImageFont
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from smtplib import SMTP
from email.utils import parseaddr

# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True

# Inicializar app flask
app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()
# Definir la ruta local para guardar la captura de pantalla
local_path = f"screenshots/local_screenshot_{time.time()}.png"

# Configuración de la aplicación en Azure AD
client_id = "6b528cdf-48fa-44ca-bddc-bb92915df304"
client_secret = "DwF8Q~cJG8E.Nd.5kEEzOgUQhtF_Dm~TvQbftaFQ"
tenant_id = "898b2aab-fa1b-4bd1-ae98-9923fff34e31"
token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'

# Configuración del ámbito (permisos necesarios)
scope = ['https://outlook.office365.com/.default']

# Usuarios permitidos para enviar instrucciones
allowed_senders = ["carl.acevedoa@duocuc.cl", "cacevedo@acdata.cl","scancino@acdata.cl", "ctoro@acdata.cl","fynsabottest@gmail.com"]

# Lista de instrucciones programadas
instructions = ["Reiniciar tuneles", "Actualizar estado", "Consulta estado"]

def get_oauth_token(client_id, client_secret, tenant_id, scope):

    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': scope,
        'grant_type': 'client_credentials'
    }

    response = requests.post(token_url, data=token_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f"Error al obtener el token de acceso: {response.text}")

# Obtener el token de acceso
# 
oauth_token = get_oauth_token(client_id, client_secret, tenant_id, scope)

def sendEmail(destinatario, asunto, body):

    # Configura los detalles del correo
    remitente = "app@acdata.cl"  # Cambia por tu correo de dominio propio
    password = "jtzgdfwnkmgnkpgy"  # Cambia por tu contraseña. pass app@acdata.cl: jtzgdfwnkmgnkpgy BotReporteCATO

    destinatarios = [destinatario]
    subject = asunto
    cuerpo = body

    # Configura el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = ", ".join(destinatarios)
    mensaje['Subject'] = subject
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    # Configura el servidor SMTP de Gmail
    servidor_smtp = "smtp.office365.com"
    #smtp-mail.outlook.com
    #smtp.office365.com
    #smtp.gmail.com

    puerto_smtp = 587

    # Crea una conexión al servidor SMTP
    sesion_smtp = smtplib.SMTP(servidor_smtp, puerto_smtp)
    sesion_smtp.starttls()
    
    try:
        # Inicia sesión en el servidor
        sesion_smtp.login(remitente, password)

        # Envía el mensaje
        sesion_smtp.sendmail(remitente, destinatarios, mensaje.as_string())
        print("Correo enviado con éxito")

        # Retorna True indicando que el correo fue enviado correctamente
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"Error de autenticación: {e}")
        # Retorna False indicando que hubo un error al enviar el correo
        return False
    finally:
        # Cierra la conexión
        sesion_smtp.quit()

def receiveEmail(oauth_token):
    
    email_user = "app@acdata.cl"
    mail = imaplib.IMAP4_SSL("outlook.office365.com")
    mail.authenticate('XOAUTH2', lambda x: b"user=" + email_user.encode() + b"\1auth=Bearer " + oauth_token.encode() + b"\1\1")
    mail.select("inbox")

    status, messages = mail.search(None, "(UNSEEN)")

    for mail_id in messages[0].split():
        _, msg_data = mail.fetch(mail_id, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Utiliza parseaddr para obtener la dirección de correo electrónico y el nombre de usuario
        sender_name, sender_email = parseaddr(msg["From"])

        print(f'Correo recibido por: ',sender_email)
        if sender_email in allowed_senders:
            print("Correo validado")
            if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                subject = msg["Subject"]

                                # Decodificar el asunto del mensaje manejando errores
                                decoded_subject = subject.encode('latin-1').decode('utf-8', errors='replace')

                            except UnicodeDecodeError as e:
                                print(f"Error al decodificar el cuerpo del mensaje: {e}")
                                decoded_subject = f" Hola! {sender_name}. \n\n No se pudo decodificar el cuerpo del mensaje correctamente. \n\n Las instrucciones programadas son las siguientes: \n\n *reiniciar tuneles \n\n *consultar estado \n\n Debes ingresar la instruccion en el asunto del correo para ser reconocida"

                            for instruction in instructions:
                                if re.search(instruction, decoded_subject, re.IGNORECASE):
                                    print(f"Instrucción recibida: {instruction.lower()}")
                                    message_lower = instruction.lower()

                                    if message_lower == "reiniciar tuneles":
                                        subjectMessage = "Confirmación de Reinicio del Tunnel de Acceso"
                                        confirmation_text = "P1. El tunnel de acceso ha sido reiniciado exitosamente."
                                        sendEmail(msg["From"], subjectMessage, confirmation_text)

                                    elif message_lower == "actualizar estado":
                                        subjectMessage = "Confirmación de actualizacion del estado del Tunnel de Acceso"
                                        confirmation_text = "P2. Test actualizacion estado"
                                        sendEmail(msg["From"], subjectMessage, confirmation_text)

                                    elif message_lower == "consulta estado":
                                        subjectMessage = "Confirmación de consulta de estado del Tunnel de Acceso"
                                        
                                        confirmation_text = "P3. Test consulta estado"
                                        sendEmail(msg["From"], subjectMessage, confirmation_text)

                                    break
                            else:
                                subjectMessage = f'No se reconoce la instruccion: {decoded_subject}'
                                confirmation_text = f" Hola! {sender_name}. \n\n No se pudo identificar el asunto del mensaje correctamente. \n\n Las instrucciones actualmente programadas son las siguientes: \n\n * reiniciar tuneles: Deshabilita y habilita todos los tuneles de CATO  \n\n * consultar estado: Captura y envia el estado actual de los tuneles de CATO. \n\n Debes ingresar la instruccion en el asunto del correo para ser reconocida."
                                sendEmail(msg["From"], subjectMessage, confirmation_text)
            
    mail.logout()

def receiveEmailWrapper():
    print("Esperando correos...")
    receiveEmail(["Reiniciar tuneles", "Actualizar estado", "Consulta estado"], oauth_token)  # Puedes añadir más instrucciones según sea necesario

scheduler.add_job(id='7',func=receiveEmailWrapper,trigger='interval', minutes=0.1)

scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run(debug = True, port=3000)