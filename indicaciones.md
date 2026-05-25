# Guía de Configuración e Instrucciones para Exponer la Interfaz MCP

Este documento detalla los pasos para resolver los problemas de visualización de la interfaz en la red corporativa de **Osinergmin** y las instrucciones de uso para toda la organización.

---

## 1. Diagnóstico de la Situación
Anteriormente se intentó usar el reenvío de puertos (Port Forwarding) integrado de VS Code a través de GitHub. Esto falló o no fue viable por tres motivos principales:
* **Privacidad por defecto:** La redirección requiere estar logueado con la misma cuenta de GitHub o configurar de forma explícita el puerto como público.
* **Restricción de Firewalls corporativos:** Los proxys de seguridad de la red corporativa bloquean el dominio de salida `*.preview.app.github.dev` por políticas de prevención de fuga de datos.
* **Dependencia de la máquina local:** Si tu laptop se apaga, entra en suspensión o se desconecta de la VPN, el servicio web se interrumpe inmediatamente.

---

## 2. Solución Inmediata: Exposición en la Intranet Corporativa
Dado que la máquina local está conectada a la red interna con la dirección IPv4 **`11.170.16.146`**, la interfaz puede servirse directamente a otros usuarios de la corporación que compartan la misma red o estén conectados por la VPN.

### Paso 2.1: Ejecutar la aplicación de Chainlit correcta
El proyecto tiene dos aplicaciones: una en la raíz (`app.py` basada en Streamlit) y otra en la carpeta `agente-mcp/app.py` (basada en Chainlit). 

Para levantar la interfaz de **Chainlit** escuchando en todas las interfaces de red (`0.0.0.0`) y en el puerto `8000`, debes ejecutar desde la raíz del proyecto:

```powershell
chainlit run agente-mcp/app.py --host 0.0.0.0 --port 8000
```

> [!NOTE]
> Si ejecutas `chainlit run app.py` (en la raíz), fallará con un error de *ScriptRunContext / missing Callback* porque esa app está escrita en Streamlit y no en Chainlit.

---

### Paso 2.2: Configuración del Firewall de Windows
Para que las demás computadoras de la red corporativa puedan comunicarse con tu puerto `8000`, debes crear una regla de entrada en tu Firewall de Windows:

1. Presiona la tecla **Windows**, busca **"Firewall de Windows Defender con seguridad avanzada"** y ábrelo.
2. En la barra lateral izquierda, selecciona **Reglas de entrada** (Inbound Rules).
3. En la barra lateral derecha, selecciona **Nueva regla...** (New Rule).
4. Elige el tipo de regla: **Puerto** (Port) y presiona *Siguiente*.
5. Selecciona **TCP** y en *Puertos locales específicos* escribe: **`8000`**. Presiona *Siguiente*.
6. Selecciona **Permitir la conexión** y presiona *Siguiente*.
7. Asegúrate de marcar las casillas **Dominio** (Domain) y **Privado** (Private) (deja desmarcada *Público* por seguridad interna). Presiona *Siguiente*.
8. Asígnale un nombre descriptivo a la regla, por ejemplo: **`Chainlit - Agente MCP Corporativo`**, y haz clic en **Finalizar**.

---

### Paso 2.3: Enlace de Acceso y Credenciales
Con la aplicación corriendo y el puerto abierto en el Firewall, comparte el siguiente enlace con las personas de la corporación:

👉 **URL de Acceso:** `http://11.170.16.146:8000`

#### Credenciales autorizadas para ingresar (Demo):
La aplicación cuenta con una pantalla de Login. Las siguientes credenciales están configuradas actualmente en el código (`agente-mcp/app.py`):

| Rol / Cargo | Usuario | Contraseña |
| :--- | :--- | :--- |
| **Administrador** | `admin` | `admin2026` |
| **Gerente Comercial** | `gerente_comercial` | `comercial2026` |
| **Gerente de Operaciones** | `gerente_operaciones` | `operaciones2026` |

---

## 3. Recomendación de Despliegue Definitivo (Producción)
Para evitar que la interfaz dependa de tu computadora personal y esté disponible 24/7 para toda la corporación:

1. **Hostear en el Servidor de Datos:** Actualmente el backend MCP remoto está en la IP `10.10.17.216:8001`. Se recomienda desplegar la carpeta de esta interfaz en esa misma máquina (o en una máquina virtual Linux/Windows en la misma intranet de Osinergmin).
2. **Ejecutar como Servicio:** Configurar el frontend de Chainlit para que corra como un servicio del sistema mediante herramientas como **PM2** o **Systemd**, asegurando su ejecución continua en segundo plano y su reinicio tras fallos o apagones del servidor.
3. **Mapear un nombre de dominio corporativo:** Solicitar al equipo de TI/Redes mapear un registro DNS interno (por ejemplo: `http://asistente-mcp.osinergmin.gob.pe`) que redireccione de forma transparente a la IP del servidor.
