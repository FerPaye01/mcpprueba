# Configuración del Proyecto - Servidores

Este archivo contiene los comandos necesarios para levantar los servicios del proyecto localmente en tu terminal de PowerShell.

## 1. Levantar Servidor MCP (Oracle Real)

Ejecuta el siguiente comando en una terminal de PowerShell para levantar el servidor MCP en el puerto `8001`:

```powershell
$env:PORT="8001"; .venv\Scripts\python.exe mcp_server.py
```

---

## 2. Levantar Agente Web (Chainlit)

Ejecuta el siguiente comando en una **segunda terminal** de PowerShell para iniciar la interfaz de Chainlit en el puerto `8000`:

```powershell
.venv\Scripts\chainlit run agente-mcp/app.py --host 0.0.0.0 --port 8000
```
