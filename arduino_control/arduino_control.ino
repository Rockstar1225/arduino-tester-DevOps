/*
 * Arduino Control - Pruebas de módulos de hardware y sensor TMP36
 *
 * Este sketch permite controlar módulos de hardware (encendido/apagado)
 * y leer datos de un sensor de temperatura TMP36 a través de comunicación serial.
 */

// Definición de pines para los módulos de hardware
#define NUM_MODULOS 3                // Número de módulos a controlar
const int pinModulos[] = {12, 8, 7}; // Pines digitales para los módulos

// Pin analógico para el sensor TMP36
#define PIN_TMP36 A0

// Variables para almacenar el estado de los módulos
bool estadoModulos[NUM_MODULOS] = {false, false, false};

// Buffer para recibir comandos
String inputBuffer = "";
bool commandComplete = false;

void setup()
{
    // Inicializar comunicación serial
    Serial.begin(9600);

    // Configurar pines de los módulos como salida
    for (int i = 0; i < NUM_MODULOS; i++)
    {
        pinMode(pinModulos[i], OUTPUT);
        digitalWrite(pinModulos[i], HIGH); // Inicialmente apagados
    }

    // Mensaje de inicio
    Serial.println("Sistema de pruebas de módulos iniciado");
    Serial.println("Comandos disponibles:");
    Serial.println("  ON:n - Encender módulo n (1-4)");
    Serial.println("  OFF:n - Apagar módulo n (1-4)");
    Serial.println("  STATUS - Ver estado de todos los módulos");
    Serial.println("  TEMP - Leer temperatura del sensor TMP36");
}

void loop()
{
    // Leer datos del puerto serial
    while (Serial.available() > 0)
    {
        char inChar = (char)Serial.read();
        if (inChar == '\n')
        {
            commandComplete = true;
        }
        else
        {
            inputBuffer += inChar;
        }
    }

    // Procesar comando si está completo
    if (commandComplete)
    {
        procesarComando(inputBuffer);
        inputBuffer = "";
        commandComplete = false;
    }
}

void procesarComando(String comando)
{
    comando.trim(); // Eliminar espacios en blanco

    // Comando para encender un módulo
    if (comando.startsWith("ON:"))
    {
        int modulo = comando.substring(3).toInt();
        if (modulo >= 1 && modulo <= NUM_MODULOS)
        {
            encenderModulo(modulo - 1); // Ajustar índice (0-3)
            Serial.print("Módulo ");
            Serial.print(modulo);
            Serial.println(" encendido");
        }
        else
        {
            Serial.println("Error: Número de módulo inválido");
        }
    }

    // Comando para apagar un módulo
    else if (comando.startsWith("OFF:"))
    {
        int modulo = comando.substring(4).toInt();
        if (modulo >= 1 && modulo <= NUM_MODULOS)
        {
            apagarModulo(modulo - 1); // Ajustar índice (0-3)
            Serial.print("Módulo ");
            Serial.print(modulo);
            Serial.println(" apagado");
        }
        else
        {
            Serial.println("Error: Número de módulo inválido");
        }
    }

    // Comando para ver el estado de todos los módulos
    else if (comando == "STATUS")
    {
        mostrarEstadoModulos();
    }

    // Comando para leer la temperatura
    else if (comando == "TEMP")
    {
        leerTemperatura();
    }
    // Comando para esperar un tiempo específico
    else if (comando.startsWith("WAIT:"))
    {
        int tiempoEspera = comando.substring(5).toInt();
        Serial.print("Esperando ");
        Serial.print(tiempoEspera);
        Serial.println(" ms");
        delay(tiempoEspera);
    }
    // Comando no reconocido
    else
    {
        Serial.print("Comando no reconocido: ");
        Serial.println(comando);
    }
}

void encenderModulo(int indice)
{
    digitalWrite(pinModulos[indice], LOW);
    estadoModulos[indice] = true;
}

void apagarModulo(int indice)
{
    digitalWrite(pinModulos[indice], HIGH);
    estadoModulos[indice] = false;
}

void mostrarEstadoModulos()
{
    Serial.println("Estado de los módulos:");
    for (int i = 0; i < NUM_MODULOS; i++)
    {
        Serial.print("Módulo ");
        Serial.print(i + 1);
        Serial.print(": ");
        Serial.println(estadoModulos[i] ? "ON" : "OFF");
    }
}

void leerTemperatura()
{
    // Leer el valor analógico del sensor TMP36
    int valorSensor = analogRead(PIN_TMP36);

    // Convertir la lectura a voltaje (0-5V)
    float voltaje = valorSensor * (5.0 / 1023.0);

    // Convertir el voltaje a temperatura en grados Celsius
    // El TMP36 tiene un offset de 0.5V y una escala de 10mV/°C
    float temperatura = (voltaje - 0.5) * 100.0;

    // Enviar la temperatura por serial
    Serial.print("Temperatura: ");
    Serial.print(temperatura);
    Serial.println(" °C");
}