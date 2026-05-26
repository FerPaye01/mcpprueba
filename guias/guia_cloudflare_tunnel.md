# Guía de Configuración: Cloudflare Tunnel para el Servidor MCP

Esta guía explica paso a paso cómo exponer tu **Servidor MCP privado** (que corre en el puerto `x` de la máquina interna `y`) hacia Internet usando **Cloudflare Tunnel**, de modo que tu aplicación en **Railway** pueda comunicarse con él.

---

## 🛠️ Método A: Túnel Rápido (Quick Tunnel)
*Ideal para pruebas inmediatas y demos. No requiere cuenta de Cloudflare ni dominio propio. Genera una URL pública aleatoria.*

### Paso 1: Descargar `cloudflared`
En la máquina donde corre el servidor MCP (``):

1. **Windows** (PowerShell como Administrador):
   Instala `cloudflared` usando winget o descárgalo manualmente:
   ```powershell
   winget install Cloudflare.cloudflared
   ```
   *Nota: Si prefieres descargar el ejecutable `.exe` directamente, lo encuentras en: [https://github.com/cloudflare/cloudflared/releases](https://github.com/cloudflare/cloudflared/releases)*

2. **Linux** (Debian/Ubuntu):
   ```bash
   curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   sudo dpkg -i cloudflared.deb
   ```

---

### Paso 2: Iniciar el túnel rápido
Ejecuta la siguiente línea de comando apuntando al puerto de tu servidor MCP (`8001`):

```bash
cloudflared tunnel --url http://localhost:8001
```

*(Si el servidor MCP corre en la misma máquina. Si corre en otra máquina de la misma red local, cambia `localhost` por la IP ``)*

### Paso 3: Obtener la URL y configurar tu App
Al ejecutar el comando, verás un bloque de logs similar a este en la terminal:

```text
+--------------------------------------------------------------------------------------------+
|  Your quick tunnel has been created! Visit it at:                                         |
|  https://some-random-words-try.cloudflare.com                                              |
+--------------------------------------------------------------------------------------------+
```

1. Copia esa URL (ej. `https://some-random-words-try.cloudflare.com`).
2. Actualiza tu archivo **`.env`** en la raíz del proyecto para apuntar a esa dirección:
   ```ini
   MCP_SERVER_URL=https://some-random-words-try.cloudflare.com
   ```
3. Reinicia tu app de Chainlit. ¡Ahora tu Chainlit local (o en Railway) se conectará a través de esa URL HTTPS segura de forma directa!

---

## 🔒 Método B: Túnel Persistente / Permanente (Zero Trust)
*Recomendado para producción. Requiere una cuenta gratuita de Cloudflare y un dominio propio registrado en ella (ej. `midominio.com`).*

### Paso 1: Crear el Túnel en Cloudflare Zero Trust
1. Ve a [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2. En la barra lateral, ve a **Networks** -> **Tunnels**.
3. Haz clic en **Add a tunnel** y selecciona **Cloudflare Tunnel** (el método recomendado).
4. Dale un nombre identificativo (ej. `mcp-osinergmin-server`) y guárdalo.

### Paso 2: Instalar el Conector en el Servidor MCP
El panel de Cloudflare te mostrará el comando exacto para tu sistema operativo. 

* **Ejemplo para Windows (PowerShell como Administrador)**:
  ```powershell
  # Esto descarga e instala cloudflared como un servicio de Windows
  cloudflared.exe service install <TU_TOKEN_UNICO>
  ```
  Al instalarlo como servicio, el túnel **se iniciará automáticamente al arrancar la computadora**, asegurando disponibilidad 24/7 sin tener terminales abiertas.

### Paso 3: Configurar la Ruta Pública (Public Hostname)
En el mismo asistente de Cloudflare Zero Trust:
1. En la pestaña **Public Hostname**, haz clic en **Add a public hostname**.
2. Completa los campos:
   * **Subdomain**: `mcp-api` (o el que gustes).
   * **Domain**: Selecciona tu dominio registrado (ej. `midominio.com`).
   * **Service Type**: `HTTP` (o `HTTPS` si el servidor MCP ya usa SSL).
   * **URL**: `localhost:y` (o `x:y`).
3. Guarda la configuración.

### Paso 4: Actualizar la Configuración de tu App
Ahora tu API del servidor MCP es pública en: `https://mcp-api.midominio.com`

* **Local**: Modifica tu `.env` de la raíz:
  ```ini
  MCP_SERVER_URL=https://mcp-api.midominio.com
  ```
* **Railway**: Ve a tu panel de Railway -> Variables -> añade o edita `MCP_SERVER_URL` con el valor `https://mcp-api.midominio.com`.

---

## 🛡️ Medida de Seguridad Opcional (Para el Método B)
Dado que tu base de datos y herramientas ahora se exponen mediante la URL de Cloudflare, es recomendable protegerla para que **solo tu app de Railway** pueda llamarla:

1. En el Zero Trust Dashboard de Cloudflare, ve a **Access** -> **Applications**.
2. Crea una política de acceso para `https://mcp-api.midominio.com`.
3. Configura una regla para permitir únicamente peticiones que incluyan una cabecera personalizada (ej. `X-MCP-Token`), o restringe el acceso a la IP pública de tu app en Railway.
