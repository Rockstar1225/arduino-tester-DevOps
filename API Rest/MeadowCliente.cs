using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Text.Json;
using System.Collections.Generic;

public class MeadowClient
{
    private readonly HttpClient _client;
    private readonly string _baseUrl;

    public MeadowClient(string baseUrl)
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _client = new HttpClient();
    }

    public async Task<bool> EncenderModulo(int numeroModulo)
    {
        if (numeroModulo < 1 || numeroModulo > 3)
        {
            Console.WriteLine($"Error: Número de módulo inválido ({numeroModulo})");
            return false;
        }

        try
        {
            var response = await _client.PostAsync($"{_baseUrl}/api/meadow/module/{numeroModulo}/on", null);
            var content = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                Console.WriteLine($"Módulo {numeroModulo} encendido");
                return true;
            }
            else
            {
                Console.WriteLine($"Error al encender módulo: {content}");
                return false;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error de comunicación: {ex.Message}");
            return false;
        }
    }

    public async Task<bool> ApagarModulo(int numeroModulo)
    {
        if (numeroModulo < 1 || numeroModulo > 3)
        {
            Console.WriteLine($"Error: Número de módulo inválido ({numeroModulo})");
            return false;
        }

        try
        {
            var response = await _client.PostAsync($"{_baseUrl}/api/meadow/module/{numeroModulo}/off", null);
            var content = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                Console.WriteLine($"Módulo {numeroModulo} apagado");
                return true;
            }
            else
            {
                Console.WriteLine($"Error al apagar módulo: {content}");
                return false;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error de comunicación: {ex.Message}");
            return false;
        }
    }

    public async Task<double?> LeerTemperatura(string nombreEvento = null)
    {
        try
        {
            var url = $"{_baseUrl}/api/meadow/temperature";
            if (!string.IsNullOrEmpty(nombreEvento))
            {
                url += $"?eventName={Uri.EscapeDataString(nombreEvento)}";
            }

            var response = await _client.GetAsync(url);
            var content = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                var data = JsonSerializer.Deserialize<TemperatureResponse>(content);
                Console.WriteLine($"Temperatura: {data.Temperature:F2}°C");
                return data.Temperature;
            }
            else
            {
                Console.WriteLine($"Error al leer temperatura: {content}");
                return null;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error de comunicación: {ex.Message}");
            return null;
        }
    }

    public async Task<bool> Esperar(int milisegundos)
    {
        if (milisegundos <= 0)
        {
            Console.WriteLine("Error: El tiempo de espera debe ser mayor que 0");
            return false;
        }

        try
        {
            var response = await _client.PostAsync($"{_baseUrl}/api/meadow/wait?milliseconds={milisegundos}", null);
            var content = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                Console.WriteLine("DONE waiting");
                return true;
            }
            else
            {
                Console.WriteLine($"Error en espera: {content}");
                return false;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error de comunicación: {ex.Message}");
            return false;
        }
    }

    public async Task<Dictionary<int, bool>> ObtenerEstadoModulos()
    {
        try
        {
            var response = await _client.GetAsync($"{_baseUrl}/api/meadow/status");
            var content = await response.Content.ReadAsStringAsync();

            if (response.IsSuccessStatusCode)
            {
                var data = JsonSerializer.Deserialize<ModuleStatusResponse>(content);
                var estados = new Dictionary<int, bool>();

                for (int i = 0; i < data.ModuleStatus.Length; i++)
                {
                    estados[i + 1] = data.ModuleStatus[i];
                    Console.WriteLine($"Módulo {i + 1}: {(data.ModuleStatus[i] ? "ON" : "OFF")}");
                }

                return estados;
            }
            else
            {
                Console.WriteLine($"Error al obtener estado: {content}");
                return null;
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error de comunicación: {ex.Message}");
            return null;
        }
    }

    private class TemperatureResponse
    {
        public double Temperature { get; set; }
        public string Event { get; set; }
        public DateTime Timestamp { get; set; }
    }

    private class ModuleStatusResponse
    {
        public bool[] ModuleStatus { get; set; }
    }
}