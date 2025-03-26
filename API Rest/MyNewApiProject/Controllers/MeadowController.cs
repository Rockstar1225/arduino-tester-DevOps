using System;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Meadow.Foundation.Sensors.Temperature;
using Meadow.Hardware;
using Iot.Device.Adc;
using System.Device.Spi;

[ApiController]
[Route("api/[controller]")]
public class MeadowController : ControllerBase
{
    private readonly IDigitalOutputPort[] _modules;
    private readonly Mcp3008 _adc;
    private readonly int _adcPin;

    public MeadowController(IDigitalOutputPort[] modules, int adcPin)
    {
        _modules = modules;
        var spiSettings = new SpiConnectionSettings(0, 0); // Bus ID and Chip Select Line
        var spiDevice = SpiDevice.Create(spiSettings);
        _adc = new Mcp3008(spiDevice); // Pass the SpiDevice instance
        _adcPin = adcPin;
    }

    [HttpGet("temperature")]
    public IActionResult GetTemperature(string eventName = null)
    {
        var adcChannel = _adc.CreateChannel(_adcPin);
        double voltage = adcChannel.ReadValue() * (3.3 / 1023.0); // Assuming 10-bit ADC
        double temperatureCelsius = (voltage - 0.5) * 100; // TMP36 conversion
        var response = new
        {
            Temperature = temperatureCelsius,
            Event = eventName,
            Timestamp = DateTime.UtcNow
        };

        return Ok(response);
    }

    [HttpPost("module/{id}/on")]
    public IActionResult TurnModuleOn(int id)
    {
        if (id < 1 || id > _modules.Length)
        {
            return BadRequest($"Módulo inválido: {id}");
        }

        _modules[id - 1].State = true;
        return Ok($"Módulo {id} encendido");
    }

    [HttpPost("module/{id}/off")]
    public IActionResult TurnModuleOff(int id)
    {
        if (id < 1 || id > _modules.Length)
        {
            return BadRequest($"Módulo inválido: {id}");
        }

        _modules[id - 1].State = false;
        return Ok($"Módulo {id} apagado");
    }

    [HttpPost("wait")]
    public async Task<IActionResult> Wait([FromQuery] int milliseconds)
    {
        if (milliseconds <= 0)
        {
            return BadRequest("El tiempo de espera debe ser mayor que 0");
        }

        await Task.Delay(milliseconds);
        return Ok("DONE waiting");
    }

    [HttpGet("status")]
    public IActionResult GetModulesStatus()
    {
        var status = new bool[_modules.Length];
        for (int i = 0; i < _modules.Length; i++)
        {
            status[i] = _modules[i].State;
        }

        return Ok(new { ModuleStatus = status });
    }
}