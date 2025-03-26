#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from API_Rest.meadow_tester import MeadowTester

# Configuración del sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"pruebas_meadow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SecuenciaPrueba:
    """Clase base para definir secuencias de prueba"""
    
    def __init__(self, nombre: str, descripcion: str):
        self.nombre = nombre
        self.descripcion = descripcion
        self.resultados: List[Dict[str, Any]] = []
        
    def ejecutar(self, tester: MeadowTester) -> bool:
        """Método a implementar por las clases hijas"""
        raise NotImplementedError("Las clases hijas deben implementar este método")
    
    def registrar_resultado(self, paso: str, exito: bool, valor: Any = None, mensaje: str = "") -> None:
        """Registra el resultado de un paso de la prueba"""
        timestamp = datetime.now()
        resultado = {
            "timestamp": timestamp,
            "paso": paso,
            "exito": exito,
            "valor": valor,
            "mensaje": mensaje
        }
        self.resultados.append(resultado)
        
        estado = "ÉXITO" if exito else "FALLO"
        log_msg = f"[{self.nombre}] {paso}: {estado}"
        if valor is not None:
            log_msg += f" - Valor: {valor}"
        if mensaje:
            log_msg += f" - {mensaje}"
            
        if exito:
            logger.info(log_msg)
        else:
            logger.error(log_msg)
    
    def generar_informe(self) -> Dict[str, Any]:
        """Genera un informe con los resultados de la prueba"""
        total_pasos = len(self.resultados)
        pasos_exitosos = sum(1 for r in self.resultados if r["exito"])
        
        return {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "inicio": self.resultados[0]["timestamp"] if self.resultados else None,
            "fin": self.resultados[-1]["timestamp"] if self.resultados else None,
            "total_pasos": total_pasos,
            "pasos_exitosos": pasos_exitosos,
            "porcentaje_exito": (pasos_exitosos / total_pasos * 100) if total_pasos > 0 else 0,
            "resultados": self.resultados
        }


class PruebaEncendidoApagado(SecuenciaPrueba):
    """Prueba de ciclos de encendido y apagado de módulos"""
    
    def __init__(self, modulos: List[int] = [1, 2, 3], ciclos: int = 1, tiempo_espera: int = 1000):
        super().__init__(
            nombre="Ciclos de Encendido/Apagado", 
            descripcion=f"Prueba de {ciclos} ciclos de encendido/apagado para los módulos {modulos}"
        )
        self.modulos = modulos
        self.ciclos = ciclos
        self.tiempo_espera = tiempo_espera
    
    def ejecutar(self, tester: MeadowTester) -> bool:
        logger.info(f"Iniciando {self.nombre}: {self.descripcion}")
        
        # Verificar estado inicial
        estado_inicial = tester.obtener_estado_modulos()
        self.registrar_resultado("Verificación estado inicial", estado_inicial is not None, estado_inicial)
        
        exito_total = True
        
        # Ejecutar ciclos de encendido/apagado
        for ciclo in range(1, self.ciclos + 1):
            logger.info(f"Iniciando ciclo {ciclo}/{self.ciclos}")
            
            # Encender módulos
            for modulo in self.modulos:
                resultado = tester.encender_modulo(modulo)
                self.registrar_resultado(f"Ciclo {ciclo} - Encendido módulo {modulo}", resultado)
                exito_total = exito_total and resultado
            
            # Esperar
            tester.esperar(self.tiempo_espera)
            
            # Verificar que todos estén encendidos
            estado = tester.obtener_estado_modulos()
            if estado:
                todos_encendidos = all(estado.get(modulo, False) for modulo in self.modulos)
                self.registrar_resultado(f"Ciclo {ciclo} - Verificación encendido", todos_encendidos, estado)
                exito_total = exito_total and todos_encendidos
            
            # Apagar módulos
            for modulo in self.modulos:
                resultado = tester.apagar_modulo(modulo)
                self.registrar_resultado(f"Ciclo {ciclo} - Apagado módulo {modulo}", resultado)
                exito_total = exito_total and resultado
            
            # Esperar
            tester.esperar(self.tiempo_espera)
            
            # Verificar que todos estén apagados
            estado = tester.obtener_estado_modulos()
            if estado:
                todos_apagados = all(not estado.get(modulo, True) for modulo in self.modulos)
                self.registrar_resultado(f"Ciclo {ciclo} - Verificación apagado", todos_apagados, estado)
                exito_total = exito_total and todos_apagados
        
        logger.info(f"Finalizada prueba {self.nombre}: {'ÉXITO' if exito_total else 'FALLO'}")
        return exito_total


class PruebaTemperatura(SecuenciaPrueba):
    """Prueba de medición de temperatura bajo diferentes condiciones"""
    
    def __init__(self, umbral_min: float = 10.0, umbral_max: float = 40.0, 
                 mediciones: int = 5, tiempo_entre_mediciones: int = 2000):
        super().__init__(
            nombre="Monitoreo de Temperatura", 
            descripcion=f"Prueba de {mediciones} mediciones de temperatura con umbrales {umbral_min}°C-{umbral_max}°C"
        )
        self.umbral_min = umbral_min
        self.umbral_max = umbral_max
        self.mediciones = mediciones
        self.tiempo_entre_mediciones = tiempo_entre_mediciones
    
    def ejecutar(self, tester: MeadowTester) -> bool:
        logger.info(f"Iniciando {self.nombre}: {self.descripcion}")
        
        exito_total = True
        temperaturas = []
        
        # Realizar mediciones
        for i in range(1, self.mediciones + 1):
            nombre_evento = f"Medición {i}/{self.mediciones}"
            temperatura = tester.leer_temperatura(nombre_evento)
            
            if temperatura is not None:
                dentro_rango = self.umbral_min <= temperatura <= self.umbral_max
                mensaje = f"Temperatura: {temperatura:.2f}°C - {'Dentro de rango' if dentro_rango else 'Fuera de rango'}"
                self.registrar_resultado(nombre_evento, dentro_rango, temperatura, mensaje)
                exito_total = exito_total and dentro_rango
                temperaturas.append(temperatura)
            else:
                self.registrar_resultado(nombre_evento, False, None, "Error al leer temperatura")
                exito_total = False
            
            if i < self.mediciones:  # No esperar después de la última medición
                tester.esperar(self.tiempo_entre_mediciones)
        
        # Calcular estadísticas
        if temperaturas:
            temp_min = min(temperaturas)
            temp_max = max(temperaturas)
            temp_avg = sum(temperaturas) / len(temperaturas)
            
            self.registrar_resultado(
                "Estadísticas", True,
                {"min": temp_min, "max": temp_max, "avg": temp_avg},
                f"Min: {temp_min:.2f}°C, Max: {temp_max:.2f}°C, Promedio: {temp_avg:.2f}°C"
            )
        
        logger.info(f"Finalizada prueba {self.nombre}: {'ÉXITO' if exito_total else 'FALLO'}")
        return exito_total


class PruebaEstres(SecuenciaPrueba):
    """Prueba de estrés para los módulos"""
    
    def __init__(self, duracion_segundos: int = 60, intervalo_ms: int = 500):
        super().__init__(
            nombre="Prueba de Estrés", 
            descripcion=f"Prueba de estrés de {duracion_segundos} segundos con cambios cada {intervalo_ms}ms"
        )
        self.duracion_segundos = duracion_segundos
        self.intervalo_ms = intervalo_ms
    
    def ejecutar(self, tester: MeadowTester) -> bool:
        logger.info(f"Iniciando {self.nombre}: {self.descripcion}")
        
        tiempo_inicio = time.time()
        tiempo_fin = tiempo_inicio + self.duracion_segundos
        ciclo = 0
        exito_total = True
        
        # Asegurar que todos los módulos estén apagados al inicio
        for modulo in range(1, 4):
            tester.apagar_modulo(modulo)
        
        try:
            while time.time() < tiempo_fin:
                ciclo += 1
                logger.info(f"Ciclo de estrés {ciclo}")
                
                # Patrón 1: Encender todos secuencialmente, luego apagar todos
                for modulo in range(1, 4):
                    resultado = tester.encender_modulo(modulo)
                    self.registrar_resultado(f"Ciclo {ciclo} - Encendido secuencial {modulo}", resultado)
                    exito_total = exito_total and resultado
                    tester.esperar(self.intervalo_ms)
                
                # Medir temperatura después de encender todos
                temp = tester.leer_temperatura(f"Ciclo {ciclo} - Temperatura con todos encendidos")
                self.registrar_resultado(f"Ciclo {ciclo} - Temperatura", temp is not None, temp)
                
                for modulo in range(1, 4):
                    resultado = tester.apagar_modulo(modulo)
                    self.registrar_resultado(f"Ciclo {ciclo} - Apagado secuencial {modulo}", resultado)
                    exito_total = exito_total and resultado
                    tester.esperar(self.intervalo_ms)
                
                # Patrón 2: Alternar módulos (encender impares, apagar pares)
                tester.encender_modulo(1)
                tester.encender_modulo(3)
                tester.esperar(self.intervalo_ms)
                
                estado = tester.obtener_estado_modulos()
                if estado:
                    patron_correcto = estado.get(1, False) and not estado.get(2, True) and estado.get(3, False)
                    self.registrar_resultado(f"Ciclo {ciclo} - Patrón alternado", patron_correcto, estado)
                    exito_total = exito_total and patron_correcto
                
                # Apagar todos para el siguiente ciclo
                for modulo in range(1, 4):
                    tester.apagar_modulo(modulo)
                
                tester.esperar(self.intervalo_ms)
                
                # Verificar si hemos alcanzado el tiempo límite
                if time.time() >= tiempo_fin:
                    break
        
        except Exception as ex:
            logger.error(f"Error durante la prueba de estrés: {str(ex)}")
            self.registrar_resultado("Error en prueba de estrés", False, None, str(ex))
            exito_total = False
        
        # Asegurar que todos los módulos estén apagados al finalizar
        for modulo in range(1, 4):
            tester.apagar_modulo(modulo)
        
        duracion_real = time.time() - tiempo_inicio
        logger.info(f"Finalizada prueba {self.nombre}: {'ÉXITO' if exito_total else 'FALLO'} - Duración: {duracion_real:.2f}s")
        return exito_total


def ejecutar_pruebas(url_api: str, pruebas: List[SecuenciaPrueba]) -> Dict[str, Any]:
    """Ejecuta una lista de pruebas y genera un informe"""
    logger.info(f"Iniciando ejecución de {len(pruebas)} pruebas en {url_api}")
    
    tester = MeadowTester(url_api)
    resultados = []
    exito_total = True
    
    tiempo_inicio = datetime.now()
    
    for prueba in pruebas:
        try:
            exito = prueba.ejecutar(tester)
            resultados.append(prueba.generar_informe())
            exito_total = exito_total and exito
        except Exception as ex:
            logger.error(f"Error al ejecutar prueba {prueba.nombre}: {str(ex)}")
            exito_total = False
    
    tiempo_fin = datetime.now()
    duracion = (tiempo_fin - tiempo_inicio).total_seconds()
    
    informe = {
        "fecha_inicio": tiempo_inicio,
        "fecha_fin": tiempo_fin,
        "duracion_segundos": duracion,
        "total_pruebas": len(pruebas),
        "pruebas_exitosas": sum(1 for r in resultados if r["porcentaje_exito"] == 100),
        "exito_total": exito_total,
        "resultados": resultados
    }
    
    logger.info(f"Finalizada ejecución de pruebas: {'ÉXITO' if exito_total else 'FALLO'}")
    logger.info(f"Duración total: {duracion:.2f} segundos")
    
    return informe


def main():
    parser = argparse.ArgumentParser(description="Pruebas automatizadas para Meadow Tester")
    parser.add_argument("--url", default="http://localhost:5000", help="URL base de la API REST")
    parser.add_argument("--prueba", choices=["encendido", "temperatura", "estres", "todas"], 
                        default="todas", help="Tipo de prueba a ejecutar")
    args = parser.parse_args()
    
    pruebas = []
    
    if args.prueba == "encendido" or args.prueba == "todas":
        pruebas.append(PruebaEncendidoApagado(ciclos=1))
    
    if args.prueba == "temperatura" or args.prueba == "todas":
        pruebas.append(PruebaTemperatura(mediciones=1))
    
    if args.prueba == "estres" or args.prueba == "todas":
        pruebas.append(PruebaEstres(duracion_segundos=30))
    
    if not pruebas:
        logger.error("No se ha seleccionado ninguna prueba válida")
        return
    
    informe = ejecutar_pruebas(args.url, pruebas)
    
    # Mostrar resumen final
    print("\n" + "=" * 50)
    print(f"RESUMEN DE PRUEBAS")
    print("=" * 50)
    print(f"Fecha: {informe['fecha_inicio'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duración: {informe['duracion_segundos']:.2f} segundos")
    print(f"Pruebas ejecutadas: {informe['total_pruebas']}")
    print(f"Pruebas exitosas: {informe['pruebas_exitosas']}")
    print(f"Resultado global: {'ÉXITO' if informe['exito_total'] else 'FALLO'}")
    print("=" * 50)
    
    for resultado in informe["resultados"]:
        print(f"\n{resultado['nombre']}: {resultado['porcentaje_exito']:.1f}% de éxito")
        print(f"  {resultado['descripcion']}")
        print(f"  Pasos: {resultado['pasos_exitosos']}/{resultado['total_pasos']}")


if __name__ == "__main__":
    main()