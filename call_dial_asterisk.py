import socket
import time

# Se instancia socket de conexion
s = socket.socket()

def mainCall():

    start_session_ami("BotAsterisk","1234","200.32.181.201", 5038)

    #call(1514, 1512)
    #auto_answer_call(1514)
    call_externo(25712895)
    
    time.sleep(20)

    end_session_ami()


def start_session_ami(user, secret, mi_ip, port):

    print("Iniciando ...")

    try:

        # Se define la ip y el puerto del conexion
        s.connect((mi_ip, port))

        # Se autentica usuario
        print("Autenticando usuario")
        s.send("Action:Login\n".encode())
        s.send(f"Username:{user}\n".encode())
        s.send(f"Secret:{secret}\n".encode())
        s.send("\n".encode())
        time.sleep(8)
        return True

    except Exception as e:

        print(f"Error: {e}")
        return False


def call(anexo_origen, anexo_destino):

    try:

        print(f"Llamando desde el anexo {anexo_origen} al anexo: {anexo_destino}")

        #
        s.send(f"Action: Originate\n".encode())
        #
        s.send(f"Channel: SIP/{str(anexo_origen)}\n".encode())
        #
        s.send(f"Context: anexos\n".encode())
        #
        s.send(f"Exten: {anexo_destino}\n".encode())
        #
        s.send(f"Priority: 1\n".encode())
        #
        s.send(f"nCallerID: {anexo_origen}\n".encode())

        s.send("\n".encode())

    except Exception as e:

        print(f"Error: {e}")




def auto_answer_call(anexo_origen):

    try:

        print(f"Llamando desde el anexo {anexo_origen} a la extensión especial")

        #
        s.send(f"Action: Originate\n".encode())
        #
        s.send(f"Channel: SIP/{str(anexo_origen)}\n".encode())
        #anexos
        s.send(f"Context: from-pstn\n".encode())
        #
        s.send(f"Exten: 25712860\n".encode())  # Aquí se marca la extensión especial
        #
        s.send(f"Priority: 1\n".encode())
        #
        s.send(f"nCallerID: {anexo_origen}\n".encode())

        s.send("\n".encode())

    except Exception as e:

        print(f"Error: {e}")


def call_externo(exten_destino):

    try:

        print(f"Llamando al exten: {exten_destino}")

        #
        s.send(f"Action: Originate\n".encode())
        #
        s.send(f"Channel: Local/{exten_destino}@from-pstn\n".encode())  # Aquí se marca el exten al que se desea llamar
        #
        s.send(f"Context: from-pstn\n".encode())  # Aquí se marca el contexto para llamadas externas
        #
        s.send(f"Exten: {exten_destino}\n".encode())  # Aquí se marca el exten al que se desea llamar
        #
        s.send(f"Priority: 1\n".encode())
        #
        s.send(f"nCallerID: {exten_destino}\n".encode())

        s.send("\n".encode())

    except Exception as e:

        print(f"Error: {e}")

def end_session_ami():
    try:
        print("Cerrando sesion ...")
        s.send("Action: Logoff\n".encode())
        print("Cerrando conexion ...")
        s.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False



