import requests
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import quote

class MeadowTester:
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip('/')
        self._session = requests.Session()

    def encender_modulo(self, numero_modulo: int) -> bool:
        if numero_modulo < 1 or numero_modulo > 3:
            print(f"Error: Número de módulo inválido ({numero_modulo})")
            return False

        try:
            response = self._session.post(f"{self._base_url}/api/meadow/module/{numero_modulo}/on")
            if response.ok:
                print(f"Módulo {numero_modulo} encendido")
                return True
            else:
                print(f"Error al encender módulo: {response.text}")
                return False
        except Exception as ex:
            print(f"Error de comunicación: {str(ex)}")
            return False

    def apagar_modulo(self, numero_modulo: int) -> bool:
        if numero_modulo < 1 or numero_modulo > 3:
            print(f"Error: Número de módulo inválido ({numero_modulo})")
            return False

        try:
            response = self._session.post(f"{self._base_url}/api/meadow/module/{numero_modulo}/off")
            if response.ok:
                print(f"Módulo {numero_modulo} apagado")
                return True
            else:
                print(f"Error al apagar módulo: {response.text}")
                return False
        except Exception as ex:
            print(f"Error de comunicación: {str(ex)}")
            return False

    def leer_temperatura(self, nombre_evento: Optional[str] = None) -> Optional[float]:
        try:
            url = f"{self._base_url}/api/meadow/temperature"
            if nombre_evento:
                url += f"?eventName={quote(nombre_evento)}"

            response = self._session.get(url)
            if response.ok:
                data = response.json()
                print(f"Temperatura: {data['Temperature']:.2f}°C")
                return data['Temperature']
            else:
                print(f"Error al leer temperatura: {response.text}")
                return None
        except Exception as ex:
            print(f"Error de comunicación: {str(ex)}")
            return None

    def esperar(self, milisegundos: int) -> bool:
        if milisegundos <= 0:
            print("Error: El tiempo de espera debe ser mayor que 0")
            return False

        try:
            response = self._session.post(f"{self._base_url}/api/meadow/wait", params={'milliseconds': milisegundos})
            if response.ok:
                print("DONE waiting")
                return True
            else:
                print(f"Error en espera: {response.text}")
                return False
        except Exception as ex:
            print(f"Error de comunicación: {str(ex)}")
            return False

    def obtener_estado_modulos(self) -> Optional[Dict[int, bool]]:
        try:
            response = self._session.get(f"{self._base_url}/api/meadow/status")
            if response.ok:
                data = response.json()
                estados = {i + 1: estado for i, estado in enumerate(data['ModuleStatus'])}
                for modulo, estado in estados.items():
                    print(f"Módulo {modulo}: {'ON' if estado else 'OFF'}")
                return estados
            else:
                print(f"Error al obtener estado: {response.text}")
                return None
        except Exception as ex:
            print(f"Error de comunicación: {str(ex)}")
            return None