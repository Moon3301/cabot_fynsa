import requests
import time

#https://monitor1.acbingenieria.cl/api/table.xml?content=sensors&columns=sensor&username=prtgadmin&passhash=3617474775

#API_KEY = "WSLB7CCHH7FNDHVB5APAQ67G2VT6IVOYTNNYO434D4======"

PRTG_URL = "https://monitor1.acbingenieria.cl/api/table.json"
USERNAME = "prtgadmin"
PASSHASH = "3617474775"

params = {
    "username": USERNAME,
    "passhash": PASSHASH,
    "content": "sensors",
    "output": "json",
    "columns": "objid,sensor,status"
}

# Lista de IDs de sensores a verificar
sensor_ids = [2553, 2071, 2075, 2077, 2407, 2035, 2065, 2720, 2041]

def get_sensor_data():
    try:
        response = requests.get(PRTG_URL, params=params, verify=False)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return None

# Realiza la consulta inicial y guarda los estados de los sensores
def main(wait_time):

    horario = ""
    if wait_time >= 600:
        horario = "Horario diurno (cada 15 minutos)"
    else:
        horario = "Horario nocturno (cada 5 minutos)"

    print(f"Iniciando revision de sensores modulo PRTG... {horario}")

    data = get_sensor_data()

    if data is None:
        return True

    initial_states = {}
    for sensor in data['sensors']:
        if sensor['objid'] in sensor_ids:
            initial_states[sensor['objid']] = sensor['status']
            print(f"Sensor ID: {sensor['objid']}, Nombre: {sensor['sensor']}, Estado inicial: {sensor['status']}")

    # Espera 15 minutos
    time.sleep(wait_time)

    # Realiza la segunda consulta
    data = get_sensor_data()

    if data is None:
        return True
    
    # Verifica los estados de los sensores nuevamente
    for sensor in data['sensors']:
        if sensor['objid'] in sensor_ids:
            print(f"Sensor ID: {sensor['objid']}, Nombre: {sensor['sensor']}, Estado después de {wait_time / 60} minutos: {sensor['status']}")

            # Si el estado del sensor era 'Fallo' y no ha cambiado, imprime un mensaje de error
            if initial_states[sensor['objid']] == 'Fallo' and sensor['status'] == 'Fallo':
                
                print(f"Error: El sensor {sensor['objid']} sigue en estado 'Fallo' después de 15 minutos.")
                return False
                
    print("Todos los sensores están OK")
   
        
                        
