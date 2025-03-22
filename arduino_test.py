#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Arduino Test - Automatización de pruebas para módulos de hardware y sensor TMP36

Este script permite automatizar pruebas de encendido/apagado de módulos de hardware
y la lectura de datos del sensor de temperatura TMP36 a través de comunicación serial
con una placa Arduino.
"""

import serial
import time
import csv
from datetime import datetime
import argparse
import os
import threading

class ArduinoTester:
    def __init__(self, puerto, baudrate=9600, timeout=2):
        """
        Inicializa la comunicación con Arduino
        
        Args:
            puerto (str): Puerto COM donde está conectado Arduino
            baudrate (int): Velocidad de comunicación
            timeout (int): Tiempo de espera para la comunicación serial
        """
        self.puerto = puerto
        self.baudrate = baudrate
        self.timeout = timeout
        self.arduino = None
        self.log_file = None
        self.csv_file = None
        self.csv_writer = None
        self.lock = threading.Lock()
         
    def conectar(self):
        """
        Establece la conexión con Arduino
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            self.arduino = serial.Serial(
                port=self.puerto,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Esperar a que Arduino se reinicie
            self.limpiar_buffer()
            print(f"Conexión establecida con Arduino en {self.puerto}")
            return True
        except serial.SerialException as e:
            print(f"Error al conectar con Arduino: {e}")
            return False
    
    def desconectar(self):
        """
        Cierra la conexión con Arduino
        """
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Conexión con Arduino cerrada")
    
    def limpiar_buffer(self):
        """
        Limpia el buffer de entrada serial
        """
        if self.arduino:
            self.arduino.reset_input_buffer()
            self.arduino.reset_output_buffer()
    
    def enviar_comando(self, comando):
        """
        Envía un comando a Arduino y espera la respuesta
        
        Args:
            comando (str): Comando a enviar
            
        Returns:
            list: Lista de líneas de respuesta de Arduino
        """
        if not self.arduino or not self.arduino.is_open:
            print("Error: No hay conexión con Arduino")
            return []
        
        # Limpiar buffer antes de enviar
        self.limpiar_buffer()
        
        # Enviar comando
        self.arduino.write(f"{comando}\n".encode('utf-8'))
        
        time.sleep(0.5)  # Esperar un momento para que Arduino proces
        
        # Leer respuesta
        respuesta = []
        while True:
            if self.arduino.in_waiting > 0:
                linea = self.arduino.readline().decode('utf-8').strip()
                if linea:
                    respuesta.append(linea)
                    print(f"Arduino > {linea}")
                    break
                 
        return respuesta
    
    def encender_modulo(self, numero_modulo):
        """
        Enciende un módulo específico
        
        Args:
            numero_modulo (int): Número del módulo a encender (1-3)
            
        Returns:
            bool: True si el comando fue exitoso, False en caso contrario
        """
        if numero_modulo < 1 or numero_modulo > 3:
            print(f"Error: Número de módulo inválido ({numero_modulo})")
            return False
        
        comando = f"ON:{numero_modulo}"
        respuesta = self.enviar_comando(comando)
        
        # Verificar respuesta
        for linea in respuesta:
            if f"Módulo {numero_modulo} encendido" in linea:
                self.registrar_evento(f"Módulo {numero_modulo} encendido")
                return True
        
        return False
    
    def apagar_modulo(self, numero_modulo):
        """
        Apaga un módulo específico
        
        Args:
            numero_modulo (int): Número del módulo a apagar (1-3)
            
        Returns:
            bool: True si el comando fue exitoso, False en caso contrario
        """
        if numero_modulo < 1 or numero_modulo > 3:
            print(f"Error: Número de módulo inválido ({numero_modulo})")
            return False
        
        comando = f"OFF:{numero_modulo}"
        respuesta = self.enviar_comando(comando)
        
        # Verificar respuesta
        for linea in respuesta:
            if f"Módulo {numero_modulo} apagado" in linea:
                self.registrar_evento(f"Módulo {numero_modulo} apagado")
                return True
        
        return False
    
    def obtener_estado_modulos(self):
        """
        Obtiene el estado actual de todos los módulos
        
        Returns:
            dict: Diccionario con el estado de cada módulo
        """
        respuesta = self.enviar_comando("STATUS")
        estados = {}
        
        for linea in respuesta:
            if "Módulo" in linea and ("ON" in linea or "OFF" in linea):
                partes = linea.split()
                if len(partes) >= 3:
                    try:
                        num_modulo = int(partes[1].replace(':', ''))
                        estado = partes[2] == "ON"
                        estados[num_modulo] = estado
                    except (ValueError, IndexError):
                        pass
        
        return estados
    
    def leer_temperatura(self):
        """
        Lee la temperatura actual del sensor TMP36
        
        Returns:
            float: Temperatura en grados Celsius, o None si hubo un error
        """
        respuesta = self.enviar_comando("TEMP")
        
        for linea in respuesta:
            if "Temperatura:" in linea:
                try:
                    # Extraer el valor numérico
                    temp_str = linea.split("Temperatura:")[1].split("°C")[0].strip()
                    temperatura = float(temp_str)
                    self.registrar_temperatura(temperatura)
                    return temperatura
                except (ValueError, IndexError):
                    pass
        
        return None
    
    def iniciar_registro(self, nombre_base="arduino_test"):
        """
        Inicia el registro de eventos y datos en archivos
        
        Args:
            nombre_base (str): Nombre base para los archivos de registro
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Crear archivo de log
        log_filename = f"{nombre_base}_log_{timestamp}.txt"
        self.log_file = open(log_filename, 'w', encoding='utf-8')
        self.log_file.write(f"=== Registro de pruebas Arduino - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
        
        # Crear archivo CSV para datos de temperatura
        csv_filename = f"{nombre_base}_temp_{timestamp}.csv"
        self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Timestamp', 'Temperatura (°C)', 'Evento'])
        
        print(f"Registro iniciado: {log_filename} y {csv_filename}")
    
    def finalizar_registro(self):
        """
        Cierra los archivos de registro
        """
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
    
    def registrar_evento(self, evento):
        """
        Registra un evento en el archivo de log
        
        Args:
            evento (str): Descripción del evento
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"[{timestamp}] {evento}"
        
        print(mensaje)
        
        if self.log_file:
            self.log_file.write(mensaje + "\n")
            self.log_file.flush()
    
    def registrar_temperatura(self, temperatura, evento=""):
        """
        Registra una lectura de temperatura en el archivo CSV
        
        Args:
            temperatura (float): Valor de temperatura
            evento (str): Evento asociado (opcional)
        """
        if self.csv_writer:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.csv_writer.writerow([timestamp, temperatura, evento])
            self.csv_file.flush()
    
    def ejecutar_secuencia_prueba(self, comandos=[], ciclos=1):
        """
        Ejecuta una secuencia de prueba basada en un array de comandos
        
        Args:
            comandos (list): Lista de comandos a ejecutar
            ciclos (int): Número de ciclos de prueba
        """
        self.registrar_evento(f"Iniciando secuencia de prueba: {ciclos} ciclos")

        try:
            for ciclo in range(1, ciclos + 1):
                self.registrar_evento(f"Iniciando ciclo {ciclo}/{ciclos}")

                for comando in comandos:
                    with self.lock:
                        wait_time = 0
                        self.registrar_evento(f"Ejecutando comando: {comando}")
                        if comando.startwith("TEMP:"):
                            evento = comando.split(":")[1]
                            temperatura = self.leer_temperatura()
                            self.registrar_temperatura(temperatura, evento=evento)
                            continue
                        respuesta = self.enviar_comando(comando)
                        for linea in respuesta:
                            self.registrar_evento(f"Respuesta: {linea}")
                if ciclo < ciclos:
                    self.registrar_evento(f"Esperando {intervalo}s antes del siguiente ciclo")
                    time.sleep(intervalo)

            self.registrar_evento("Secuencia de prueba completada")
            return True

        except Exception as e:
            print(e)
            self.registrar_evento(f"Error durante la secuencia de prueba: {e}")
            return False


def listar_puertos():
    """
    Lista los puertos seriales disponibles
    
    Returns:
        list: Lista de puertos disponibles
    """
    import serial.tools.list_ports
    puertos = serial.tools.list_ports.comports()
    return [p.device for p in puertos]


def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Automatización de pruebas para Arduino')
    parser.add_argument('-p', '--puerto', help='Puerto COM donde está conectado Arduino')
    parser.add_argument('-c', '--ciclos', type=int, default=1, help='Número de ciclos de prueba')
    parser.add_argument('-l', '--listar', action='store_true', help='Listar puertos disponibles')
    parser.add_argument('-s', '--secuencia', nargs='+', help='Secuencia de comandos a ejecutar')
    parser.add_argument('-n', '--nombre', help='Nombre base para los archivos de registro')
    args = parser.parse_args()
    
    # Listar puertos si se solicita
    if args.listar:
        puertos = listar_puertos()
        print("Puertos disponibles:")
        for puerto in puertos:
            print(f"  - {puerto}")
        return
    
    # Solicitar puerto si no se especificó
    puerto = args.puerto
    if not puerto:
        puertos = listar_puertos()
        if not puertos:
            print("No se encontraron puertos seriales disponibles")
            return
        
        print("Puertos disponibles:")
        for i, p in enumerate(puertos):
            print(f"  {i+1}. {p}")
        
        seleccion = input(f"Seleccione un puerto (1-{len(puertos)}): ")
        try:
            indice = int(seleccion) - 1
            if 0 <= indice < len(puertos):
                puerto = puertos[indice]
            else:
                print("Selección inválida")
                return
        except ValueError:
            print("Entrada inválida")
            return
    
    # Crear instancia del tester de Arduino
    tester = ArduinoTester(puerto)
    
    # Conectar al Arduino
    if not tester.conectar():
        print("No se pudo establecer conexión con Arduino")
        return
    
    # Iniciar registro
    nombre_base = args.nombre if args.nombre else "arduino_test"
    tester.iniciar_registro(nombre_base=nombre_base)
    
    # Ejecutar secuencia de prueba con comandos personalizados
    comandos = args.secuencia if args.secuencia else []
    if not tester.ejecutar_secuencia_prueba(comandos=comandos, ciclos=args.ciclos):
        print("Error durante la ejecución de la secuencia de prueba")
    
    # Finalizar registro
    tester.finalizar_registro()
    
    # Desconectar del Arduino
    tester.desconectar()

if __name__ == "__main__":
    main()