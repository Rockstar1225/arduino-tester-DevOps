/*
 * Arduino Control - Prueba de encendido/apagado de LEDs
 *
 * Este sketch permite encender y apagar dos LEDs a través de comandos seriales.
 */

// Definición de pines para los LEDs
#define NUM_LEDS 2
const int pinLeds[] = {12, 8}; // Pines digitales para los LEDs

// Buffer para recibir comandos
String inputBuffer = "";
bool commandComplete = false;

void setup()
{
    // Inicializar comunicación serial
    Serial.begin(9600);

    // Configurar pines de los LEDs como salida
    for (int i = 0; i < NUM_LEDS; i++)
    {
        pinMode(pinLeds[i], OUTPUT);
        digitalWrite(pinLeds[i], LOW); // Inicialmente apagados
    }

    // Mensaje de inicio
    Serial.println("Sistema de prueba de LEDs iniciado");
    Serial.println("Comandos disponibles:");
    Serial.println("  ON:n - Encender LED n (1-2)");
    Serial.println("  OFF:n - Apagar LED n (1-2)");
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

    // Comando para encender un LED
    if (comando.startsWith("ON:"))
    {
        int led = comando.substring(3).toInt();
        if (led >= 1 && led <= NUM_LEDS)
        {
            encenderLed(led - 1); // Ajustar índice (0-1)
            Serial.print("LED ");
            Serial.print(led);
            Serial.println(" encendido");
        }
        else
        {
            Serial.println("Error: Número de LED inválido");
        }
    }

    // Comando para apagar un LED
    else if (comando.startsWith("OFF:"))
    {
        int led = comando.substring(4).toInt();
        if (led >= 1 && led <= NUM_LEDS)
        {
            apagarLed(led - 1); // Ajustar índice (0-1)
            Serial.print("LED ");
            Serial.print(led);
            Serial.println(" apagado");
        }
        else
        {
            Serial.println("Error: Número de LED inválido");
        }
    }
    // Comando para esperar un tiempo específico
    else if (comando.startsWith("WAIT:"))
    {
        int tiempoEspera = comando.substring(5).toInt();
        Serial.print("Esperando ");
        Serial.print(tiempoEspera);
        Serial.println(" ms");
        delay(tiempoEspera);
        Serial.println("DONE waiting");
    }
    // Comando no reconocido
    else
    {
        Serial.print("Comando no reconocido: ");
        Serial.println(comando);
    }
}

void encenderLed(int indice)
{
    digitalWrite(pinLeds[indice], HIGH);
}

void apagarLed(int indice)
{
    digitalWrite(pinLeds[indice], LOW);
}