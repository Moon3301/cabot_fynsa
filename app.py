from flask import Flask
from flask_apscheduler import APScheduler
import paramiko
import smtplib
import email
import imaplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import base64
import time
import traceback
from datetime import datetime, timedelta
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from smtplib import SMTP
from email.utils import parseaddr
import reset_web_driver
import threading

# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 10}  # Ajusta el número según tus necesidades
    }

# Inicializar app flask
app = Flask(__name__)
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()

# Configuración de la conexión SSH
hostname = '192.168.31.1'
port = 22
username = 'admin'
password = 'Fynsa_Edge2021@'

# Se define la ruta local (local_path) para almacenar y obtener los screenshot del servicio
local_path = f"screenshots/local_screenshot_{time.time()}.png"

# Se define la ruta local (firma_path) para almacenar y obtener la firma que se insertara en el correo
firma_path = 'firmas/firma_bot.png'

# Se define la ruta local (ruta_logs_error) para almacenar y obtener los errores capturados
ruta_logs_error = f'logs_error/log_error_{time.time()}.txt'

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
instructions = ["Reiniciar", "Estado", "Test"]

# Variables externas

contador_error_IMAP4 = 0


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

def createImageFromLog(log):
    # Configura el tamaño y el formato de la imagen
    image_width = 1200
    image_height = 600
    background_color = (0, 0, 0)  # Fondo negro
    text_color = (255, 255, 255)  # Texto blanco

    # Crea una imagen en blanco con fondo negro
    image = Image.new("RGB", (image_width, image_height), background_color)
    draw = ImageDraw.Draw(image)

    # Carga una fuente monoespaciada que asemeje el estilo de consola
    font_path = "consola.ttf"  # Descarga una fuente de consola monoespaciada
    
    try:
        font = ImageFont.truetype(font_path, 14)
    except IOError:
        # Si la fuente no está disponible, utiliza la fuente por defecto
        font = ImageFont.load_default()

    # Divide el log en líneas
    lines = log.split('\n')

    # Escribe cada línea en la imagen con el estilo de consola
    y_position = 10
    for line in lines:
        draw.text((10, y_position), line, font=font, fill=text_color)
        y_position += 16  # Ajusta el espacio entre líneas según sea necesario

    # Guarda la imagen
    image.save(local_path)

    return image

def sendEmail(destinatarios, asunto, cc, body_email, image):

    # Configura los detalles del correo
    remitente = "app@acdata.cl"  # Cambia por tu correo de dominio propio
    password = "jtzgdfwnkmgnkpgy"  # Cambia por tu contraseña

    # Inicializa las variables para evitar errores si no se adjuntan archivos
    image_bytes = None
    firma_imagen = None

    if image:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_bytes = buffered.getvalue()

    # Convierte el status a base64 si se ha cargado
    if image_bytes is not None:
    # Convierte el status a base64
        status_base64 = base64.b64encode(image_bytes).decode("utf-8") if image_bytes else None
    else:
        status_base64 = None
    
    # Carga la firma desde el archivo si la ruta está presente
    if firma_path and os.path.exists(firma_path):
        with open(firma_path, 'rb') as firma_file:
            firma_imagen = firma_file.read()

    # Convierte la firma a base64 si se ha cargado
    firma_base64 = base64.b64encode(firma_imagen).decode("utf-8") if firma_imagen else None

    cuerpo_html = f"""
            <html>
            <body>
                <p>Estimados:</p>
                <p>{body_email}</p>
                {f'<img src="data:image/png;base64,{status_base64}" alt="Status">' if status_base64 else ''}
                <p>Saludos Cordiales.</p>
                {f'<img src="data:image/png;base64,{firma_base64}" alt="Firma">' if firma_base64 else ''}
            </body>
            </html>
            """
    
    subject = asunto
    cuerpo = cuerpo_html
    
    # Configura el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = ", ".join(destinatarios)
    mensaje['Subject'] = subject
    
    if cc:
        mensaje['Cc'] = ", ".join(cc)

    mensaje.attach(MIMEText(cuerpo, 'html'))

    # Adjunta la imagen del estado del servicio al mensaje si está presente
    if image_bytes:
        imagen_adjunta = MIMEImage(image_bytes, name=f'Estado_CATO_{time.time()}.png')
        mensaje.attach(imagen_adjunta)

    # Adjunta la imagen de la firma al mensaje si está presente
    if firma_imagen:
        firma_adjunta = MIMEImage(firma_imagen, name='firma_bot.png')
        mensaje.attach(firma_adjunta)

    # Configura el servidor SMTP de Gmail
    servidor_smtp = "smtp.office365.com"
    puerto_smtp = 587

    # Crea una conexión al servidor SMTP
    sesion_smtp = smtplib.SMTP(servidor_smtp, puerto_smtp)
    sesion_smtp.starttls()
    
    try:
        # Inicia sesión en el servidor
        sesion_smtp.login(remitente, password)

        # Envía el mensaje
        sesion_smtp.sendmail(remitente, destinatarios + cc, mensaje.as_string())
        
        # Retorna True indicando que el correo fue enviado correctamente
        print("Correo enviado con éxito")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"Error de autenticación: {e}")
        # Retorna False indicando que hubo un error al enviar el correo
        return False
    finally:
        # Cierra la conexión
        sesion_smtp.quit()

def receiveEmail():

    oauth_token = get_oauth_token(client_id, client_secret, tenant_id, scope)
    # Refrescar el token de acceso si es necesario
    try:
        new_access_token = get_oauth_token(client_id, client_secret, tenant_id, scope)
        oauth_token = new_access_token
    except Exception as e:
        print(f"Error al obtener un nuevo token de acceso: {e}")
    
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

        print(f'Correo recibido por: ', sender_email)
        if sender_email in allowed_senders:
            print("Correo reconocido !")
            try:
                subject = msg["Subject"]

                # Decodificar el asunto del mensaje manejando errores
                decoded_subject = subject.encode('latin-1').decode('utf-8', errors='replace')

            except UnicodeDecodeError as e:
                print(f"Error al decodificar el cuerpo del mensaje: {e}")
                decoded_subject = f"Hola, {sender_name}.\n\n No se pudo decodificar el cuerpo del mensaje correctamente. \n\n Las instrucciones programadas son las siguientes: \n\n *reiniciar tuneles \n\n *consultar estado \n\n Debes ingresar la instruccion en el asunto del correo para ser reconocida"

            for instruction in instructions:
                if re.search(instruction, decoded_subject, re.IGNORECASE):
                    print(f"Instrucción recibida: {instruction.lower()}")
                    message_lower = instruction.lower()

                    if message_lower == "reiniciar":
                        print("Confirmación reinicio Tunneles de Acceso")
                        resetService([sender_email], [sender_email])

                    elif message_lower == "actualizar estado":

                        notImage = None
                        subjectMessage = "Confirmación de actualizacion del estado del Tunnel de Acceso"
                        confirmation_text = "P2. Test actualizacion estado"
                        sendEmail([sender_email], subjectMessage, [sender_email], confirmation_text, notImage)

                    elif message_lower == "estado":

                        print("Confirmación consulta estado del Tunnel de Acceso")
                        main([sender_email], [sender_email])

                    break
            else:
                notImage = None
                subjectMessage = f'No se reconoce la instruccion: {decoded_subject}'
                cuerpo_html = f"""
                                <p>
                                    <p>No se pudo identificar el asunto del mensaje correctamente. Las instrucciones actualmente programadas son las siguientes:</p>
                                    <p>* <b>reiniciar:</b> Deshabilita y habilita todos los servicios de CATO. </p>
                                    <p>* <b>estado:</b> Captura y envía el estado actual de los servicios de CATO. </p>
                                    <p>Debes ingresar la instrucción en el <b>ASUNTO</b> del correo para ser reconocida.</p>
                                </p>
                                """
                sendEmail([sender_email], subjectMessage, [sender_email], cuerpo_html, notImage)

    mail.logout()

def receiveEmailWrapper():
    print("Esperando correos...")
    receiveEmail()  # Puedes añadir más instrucciones según sea necesario

def obtener_hora_actual():

    # Obtener la fecha y hora actual
    fecha_hora_actual = datetime.now()
    # Formatear la fecha y hora en el formato deseado
    formato_deseado = "%d-%m-%Y %H:%M"
    fecha_hora_formateada = fecha_hora_actual.strftime(formato_deseado)

    return fecha_hora_formateada

def main(destinatarios, cc):

    # Realiza la conexion SSH al servidor y obtiene el registro del comando indicado.
    output = connectSSH('show service ipsec')

    # Crea una imagen con el registro del comando
    image = createImageFromLog(output)

    # Se valida el estado del servicio y retorna la salida de comando
    status = status_app(output)

    # Si el status es verdadero envia el correo 
    if (status == True):

        try:
            # PENDIENTE
            create_email('estado', image, destinatarios, cc)

        except Exception as e:

            print("Error al crear el correo.")
            print(f"Error: {e}")

    else:

        try:
            # PENDIENTE
           
            create_email('error', image, destinatarios, cc)

            # Crea un archivo txt con el log del error obtenido
            save_output_to_file(output)

        except Exception as e:

            print("Error al enviar el correo.")
            print(f"Error: {e}")

def resetService(destinatario, cc):

    # Ejecutar comando para reiniciar servicio 
    ######

    try:
    
        reset_web_driver.main()

        ######

        # Realiza la conexion SSH al servidor y obtiene el registro del comando indicado.
        output = connectSSH('show service ipsec')

        # Crea una imagen con el registro del comando
        image = createImageFromLog(output)

        create_email('reinicio', image, destinatario, cc)
    
    except Exception as e:

        save_output_to_file(e)

        print(f"Error: {e}")


def create_email(type, image, dest_email, cc_email):

    # Obtiene la fecha actual
    fecha_actual = obtener_hora_actual()

    if type == 'estado':

        # Define el asunto del correo
        asunto = f'ESTADO CATO {fecha_actual}'

        destinatarios = dest_email

        cc = cc_email

        # Define el body del correo
        body = f'Junto con saludar, segun lo solicitado se informa estado CATO al dia de hoy: '

    if type == 'error':

        # Define el asunto del correo
        asunto = f'ERROR ESTADO CATO {fecha_actual}'

        destinatarios = dest_email

        cc = cc_email

        # Define el body del correo
        body = f'Junto con saludar, se informa caida de servicio CATO con fecha {fecha_actual}. Se adjunta print con error: '
        
    if type == 'reinicio':

        # Define el asunto del correo
        asunto = f'REINICIO CATO {fecha_actual}'

        # Define el o los destinatarios
        destinatarios = dest_email

        # Define a quien va a copia
        cc = cc_email

        # Define el body del correo
        body = f'Junto con saludar, se informa reinicio de servicio CATO con fecha {fecha_actual}. \n\n Se informa estado actual de servicio: '

    sendEmail(destinatarios, asunto, cc, body, image)

def check_status():

    print("Validando estado del servicio ...")

    # Realiza la conexion SSH al servidor y obtiene el registro del comando indicado.
    output = connectSSH('show service ipsec')

    # Se valida el estado del servicio y retorna la salida de comando
    status = status_app(output)

    # Si el status es falso envia correo al usuario para notificar caida de servicio
    if status == False:

        print("Estado del servicio DOWN !!")

        try:

            print("Reiniciando servicio desde Cloud VMware ...")
            reset_web_driver.main()

        except Exception as e:

            print("No fue posible reiniciar servicio desde Cloud.")
            print(f"Se envia correo con detalle de error: {e}")
            
        print("Enviando correo con notificacion de estado ...")
        # Crea un archivo txt con el log del error obtenido
        save_output_to_file(output)

        # Crea la imagen con salida de comando
        image = createImageFromLog(output)

        create_email("error", image, ['helpdesk@acdata.cl'], ['fynsabottest@gmail.com'])

        #Envia el correo
        # sendEmail(['helpdesk@acdata.cl'], asunto, ['fynsabottest@gmail.com'], body)
        # sendEmail(['fynsabottest@gmail.com'], asunto, ['fynsabottest@gmail.com'], body)
        print("Correo enviado!")

    else:

        print("Estado del servicio UP !!")

def status_app(output):

    # Convierte el log en un string
    log = str(output)

    # Busca las palabras UP o DOWN en la palabra Status.
    status_matches = re.findall(r'Status: (UP|DOWN)', log)

    # Inicializa las variables para tunnel y channel
    tunnels = []
    channels = []

    # Asigna valores a las variables usando un bucle
    for i in range(4):
        tunnel = status_matches[i]
        channel = status_matches[i + 4]
        tunnels.append(tunnel)
        channels.append(channel)

    # Verifica si todos los túneles y canales están en estado UP
    if all(status == 'UP' for status in tunnels + channels):
        
        return True
    
    else:

        print(f'Status Tuneles: {tunnels[0]}, {tunnels[1]}, {tunnels[2]}, {tunnels[3]} ' )
        print(f'Status Channels: {channels[0]}, {channels[1]}, {channels[2]}, {channels[3]} ' )

        return False
    
def connectSSH(comand):
    # Crear una instancia de la clase SSHClient
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conectar al servidor
        ssh.connect(hostname, port, username, password)

        # Ejecutar comandos SSH de manera interactiva
        channel = ssh.invoke_shell()

        if comand == "show service ipsec":

            # Ejecuta el comando
            channel.send(comand + '\n' * 10)

            # Espera un tiempo para que el comando se ejecute
            time.sleep(1)

            # Lee la salida
            output = channel.recv(4096).decode()

            # Realizar pruebas de validacion ...... PENDIENTE
            
            # Reemplaza 'Status: UP' por 'Status: DOWN Reason: IPSec-SA Proposals'
            #output = re.sub(r'Status: UP', r'Status: DOWN Reason: IPSec-SA Proposals', output)

            # Utilizar expresiones regulares (regex) para cortar desde "vShield Edge IPSec Service Status:"
            match = re.search(r'vShield Edge IPSec Service Status:(.+?)vse-', output, re.DOTALL)
            if match:
                # Imprimir el resultado cortado
                output = clean_text(match.group(1))
                
            else:
                print("No se encontró la coincidencia.")

            time.sleep(1)

            # Imprime la salida
            
        else:

            # Ejecuta el comando
            channel.send(comand + '\n')

            # Espera un tiempo para que el comando se ejecute
            time.sleep(1)

            # Lee la salida
            output = channel.recv(4096).decode()

            time.sleep(1)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Cerrar la conexión SSH
        ssh.close()

    return output

def save_output_to_file(output):
    with open(ruta_logs_error, 'w', encoding='utf-8') as file:
        file.write(output)

def clean_text(text):

    # Reemplazar caracteres no reconocidos entre "Status" y "UP" o "DOWN"
    clean_text = re.sub(r'Status: [^A-Za-z0-9_]+(UP|DOWN)', r'Status: \1', text)

    # Eliminar secuencias de escape ANSI
    clean_text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]*[^\x20-\x7E]', '', clean_text)
    
    # Eliminar líneas que contienen "byte XXXX"
    clean_text = re.sub(r'byte \d+', '', clean_text)

    # Eliminar caracteres no imprimibles
    clean_text = re.sub(r'[^ -~\n]', '', clean_text)

    # Reemplazar patrones específicos que pueden causar problemas
    clean_text = re.sub(r': UP[^\n]*\n', ': UP\n', clean_text)
    clean_text = re.sub(r': DOWN[^\n]*\n', ': DOWN\n', clean_text)

    # Reemplazar patrones específicos que pueden causar problemas
    clean_text = re.sub(r'Status\s*:\s*(UP|DOWN)', r'Status: \1', clean_text)

    return clean_text

@scheduler.task(trigger=CronTrigger(hour=9, minute=0, day_of_week="mon-fri"), id='1', max_instances=2)
def tarea_1():
    try:
        print("Ejecutando tarea 1... 'Estado cato 09:00' ")
        # Código de la tarea 1
        main(['hortega@fynsa.cl', 'mallende@fynsa.cl'], ['helpdesk@acdata.cl'])
        
    except Exception as e:
        print(f"Error en tarea 1 'Estado cato 09:00' : {e}")
        traceback.print_exc()

        save_output_to_file(e)

        # Calcular el próximo momento para ejecutar la tarea, 10 segundos después del error
        next_run_time = datetime.now() + timedelta(seconds=10)

        # Puedes reprogramar la tarea para intentar nuevamente
        scheduler.add_job(tarea_1, trigger='date', run_date=next_run_time)

@scheduler.task(trigger=CronTrigger(hour=12, minute=0, day_of_week="mon-fri"), id='2', max_instances=2)
def tarea_2():
    try:
        print("Ejecutando tarea 2... 'Estado cato 12:00 '")
        # Código de la tarea 2
        main(['hortega@fynsa.cl', 'mallende@fynsa.cl'], ['helpdesk@acdata.cl'] )

    except Exception as e:
        print(f"Error en tarea 2 'Estado cato 12:00' : {e}")
        traceback.print_exc()

        save_output_to_file(e)
        # Calcular el próximo momento para ejecutar la tarea, 10 segundos después del error
        next_run_time = datetime.now() + timedelta(seconds=10)

        # Puedes reprogramar la tarea para intentar nuevamente
        scheduler.add_job(tarea_2, trigger='date', run_date=next_run_time)

@scheduler.task(trigger=CronTrigger(hour=15, minute=0, day_of_week="mon-fri"), id='3', max_instances=2)
def tarea_3():
    try:
        print("Ejecutando tarea 3... 'Estado cato 15:00 '")
        # Código de la tarea 3
        main(['hortega@fynsa.cl', 'mallende@fynsa.cl'], ['helpdesk@acdata.cl'])

    except Exception as e:
        print(f"Error en tarea 3 'Estado cato 15:00' : {e}")
        traceback.print_exc()

        save_output_to_file(e)
        # Calcular el próximo momento para ejecutar la tarea, 10 segundos después del error
        next_run_time = datetime.now() + timedelta(seconds=10)

        # Puedes reprogramar la tarea para intentar nuevamente
        scheduler.add_job(tarea_3, trigger='date', run_date=next_run_time)

@scheduler.task(trigger=IntervalTrigger(minutes=15), id='4', max_instances=3)
def check_service_status():

    try:
        
        check_status()
    
    except Exception as e:

        print(f"Error en tarea 4 'Check service Status': {e}")
        traceback.print_exc()

        save_output_to_file(e)

        # Calcular el próximo momento para ejecutar la tarea, 10 segundos después del error
        next_run_time = datetime.now() + timedelta(seconds=10)

        # Puedes reprogramar la tarea para intentar nuevamente
        scheduler.add_job(check_service_status, trigger='date', run_date=next_run_time)

@scheduler.task(trigger=IntervalTrigger(minutes=1), id='5', max_instances=4)
def receive_email():

    try:
        
        receiveEmailWrapper()
    
    except imaplib.IMAP4.error as e:

        contador_error_IMAP4 = contador_error_IMAP4 + 1

        if contador_error_IMAP4 >= 10:

            print(f"Se ha alcanzado el numero maximo de reintentos para ejecutar la tarea ... ")
            
        else:

            print(f"Error en tarea 5 'Responder Email': {e}. Intento: {contador_error_IMAP4}")
            traceback.print_exc()

            save_output_to_file(e)

            # Calcular el próximo momento para ejecutar la tarea, 10 segundos después del error
            next_run_time = datetime.now() + timedelta(seconds=30)

            # Reprogramar la tarea para intentar nuevamente
            scheduler.add_job(check_service_status, trigger='date', run_date=next_run_time)

scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run()