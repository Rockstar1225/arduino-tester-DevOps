using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Meadow.Foundation.Sensors.Temperature;
using Meadow.Hardware;
using System.Device.Spi;

var builder = WebApplication.CreateBuilder(args);

// Agregar servicios al contenedor
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Configurar los módulos digitales y el sensor de temperatura
builder.Services.AddSingleton<IDigitalOutputPort[]>(sp =>
{
    var device = sp.GetRequiredService<IMeadowDevice>();
    return new IDigitalOutputPort[]
    {
        device.CreateDigitalOutputPort(device.Pins.D14),
        device.CreateDigitalOutputPort(device.Pins.D12),
        device.CreateDigitalOutputPort(device.Pins.D11)
    };
});

builder.Services.AddSingleton<Tmp36>(sp =>
{
    var device = sp.GetRequiredService<IMeadowDevice>();
    var analogPort = device.GetAnalogInputPort("A02"); // Use the correct analog port identifier
    return new Tmp36(analogPort);
});

var app = builder.Build();

// Configurar el pipeline de solicitudes HTTP
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();