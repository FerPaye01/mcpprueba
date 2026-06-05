# Guía de Despliegue en Intranet Corporativa - Proyecto OpenEnergy

Esta guía documenta rigurosamente el proceso de diagnóstico, resolución y despliegue del proyecto **OpenEnergy** en una intranet corporativa. Su objetivo es educativo y técnico, permitiendo a cualquier desarrollador comprender los problemas de red, puertos, políticas de seguridad del navegador y configuración híbrida (desarrollo/producción) que surgieron durante el proceso.

---

## 1. Contexto del Problema

El proyecto **OpenEnergy** utiliza una arquitectura desacoplada que consta de:

*   **Backend (Python + Chainlit):** Administra la lógica del chatbot de IA, las conexiones con los modelos LLM, y la comunicación interactiva a través de WebSockets (Socket.IO). Además, se conecta al Servidor MCP para consultar bases de datos relacionales en caliente.
*   **Frontend (React + Vite + TypeScript):** Una interfaz de usuario personalizada de alto rendimiento con gráficos dinámicos y controles de filtrado.
*   **Servidor MCP (Model Context Protocol):** Expone herramientas de consulta a bases de datos corporativas a través de APIs locales seguras.

En el entorno de desarrollo inicial, el frontend corre mediante un servidor de desarrollo de Vite (puerto `5173`) y el backend corre en Chainlit (puerto `8080`).

### Localhost vs. IP de Red (Intranet)
Cuando se trabaja en una máquina local (`localhost` o `127.0.0.1`), las llamadas de red se resuelven internamente dentro de la interfaz de bucle de retorno (*loopback*). Sin embargo, al publicar la aplicación para que otros compañeros de la intranet accedan usando la dirección IP física de la máquina servidor (ej. `http://11.170.16.146:8000`), entran en juego estrictas políticas de red y seguridad del navegador que no ocurren en un entorno puramente local.

---

## 2. Síntomas Observados

Durante la prueba de despliegue en la red de la intranet, se registraron los siguientes comportamientos:

1.  **Carga Infinita (Loader Bloqueado):**
    Al abrir la interfaz en el navegador, el sistema se quedaba de forma permanente mostrando la pantalla de carga: *"Asignando Identidad de Analista..."*.
2.  **Consola de React (`connected: undefined`):**
    En los registros de la consola del navegador, el estado de la conexión WebSocket devuelto por el hook `@chainlit/react-client` se quedaba en:
    ```json
    React app state update: { connected: undefined, messagesCount: 0, loading: false }
    ```
3.  **Acceso Parcial:**
    El backend de Chainlit estándar era visible desde otras máquinas de la intranet en el puerto `8000`, pero la interfaz personalizada no cargaba o se desconectaba al instante.
4.  **Error de Recursos No Encontrados y Conexiones Rechazadas:**
    ```text
    GET http://11.170.16.146:8080/auth/config net::ERR_CONNECTION_REFUSED
    TypeError: Failed to fetch
    ```
5.  **Advertencia de Seguridad en Chrome (Cross-Origin Frame):**
    ```text
    Unsafe attempt to load URL http://11.170.16.146:8000/ from frame with URL chrome-error://chromewebdata/. Domains, protocols and ports must match.
    ```

---

## 3. Diagnóstico Realizado y Evaluación de Hipótesis

Para dar con la causa raíz, se formularon y testearon las siguientes hipótesis:

### Hipótesis 1: Bloqueo de Cortafuegos (Firewall)
*   *Idea:* El firewall de Windows o de la red corporativa estaba bloqueando el puerto de entrada.
*   *Diagnóstico:* Descartada parcialmente. Al probar el acceso al puerto `8000`, la red respondía, pero fallaba en el puerto `8080` con un error `ERR_CONNECTION_REFUSED`. El bloqueo no era de red a nivel de firewall, sino que no había ningún servicio escuchando activamente en el puerto `8080` de esa IP específica.

### Hipótesis 2: Host Binding Incorrecto (`localhost` vs. `0.0.0.0`)
*   *Idea:* El servidor de backend solo estaba escuchando en `localhost` (127.0.0.1) y rechazaba peticiones desde IPs externas de la intranet.
*   *Diagnóstico:* Confirmada en parte. Se solucionó configurando la bandera `--host 0.0.0.0` al levantar Chainlit, indicándole al sistema operativo que escuche en todas las interfaces de red disponibles de la máquina servidor.

### Hipótesis 3: Discrepancia de Origen y Puerto (CORS y Same-Origin Policy)
*   *Idea:* El cliente de React compilado tenía configurado un puerto estático en el código que no correspondía al puerto en el que corría el servidor.
*   *Diagnóstico:* **CONFIRMADA.** En el código de `chainlitClient.ts` existía la siguiente línea hardcodeada:
    ```typescript
    const CHAINLIT_SERVER_URL = `${window.location.protocol}//${window.location.hostname}:8080`;
    ```
    Si el servidor Chainlit se iniciaba en el puerto `8000`, el frontend de React seguía intentando consumir los endpoints de autenticación y de sockets en el puerto `8080`. Como no había nada escuchando en el `8080`, el navegador lanzaba un error de conexión rechazada y Chrome bloqueaba la comunicación.

### Hipótesis 4: Rechazo de Cookies JWT por Configuración de IP
*   *Idea:* La cookie de sesión JWT (`credentials`) necesaria para autenticar el WebSocket no se guardaba en el navegador por diferencias entre la URL de acceso del usuario y el parámetro `CHAINLIT_URL` del archivo `.env`.
*   *Diagnóstico:* **CONFIRMADA.** Si el usuario accedía a `http://localhost:8000` pero en el archivo `.env` del servidor la variable estaba configurada como `CHAINLIT_URL=http://11.170.16.146:8000`, el navegador consideraba el origen como cruzado y bloqueaba la cookie de autenticación de Chainlit, provocando que la sesión WebSocket nunca se autorizara y quedara colgada en `connected: undefined`.

---

## 4. Conceptos Técnicos Aprendidos

### `localhost` vs. `0.0.0.0`
*   **`localhost` (127.0.0.1):** Es la interfaz de loopback virtual. Si un servicio se enlaza a `localhost`, solo acepta conexiones que provengan de la misma máquina física.
*   **`0.0.0.0`:** No es una dirección IP real, sino una instrucción especial que le indica al socket del servidor que se enlace a **todas** las interfaces de red físicas y virtuales de la máquina. Es indispensable para que un servidor sea accesible desde otros dispositivos de la intranet.

### Same-Origin Policy (SOP) y CORS
El navegador bloquea por seguridad cualquier petición HTTP/WebSocket iniciada por un script que intente acceder a un recurso de un origen diferente (diferente protocolo, dominio o **puerto**). Al tener el frontend de React buscando al backend en el puerto `8080` mientras el usuario navegaba en el `8000`, el navegador aplicaba la política de mismo origen y abortaba la carga.

### Cookies de Sesión y JWT
Chainlit gestiona las sesiones de chat a través de un token JWT firmado almacenado en una cookie de navegador. El navegador solo enviará y guardará esta cookie de forma segura si la URL configurada en el servidor (`CHAINLIT_URL`) coincide exactamente con el origen desde el cual el usuario final está cargando el sitio.

### Frontend Dev Server vs. Frontend Build (Static Hosting)
*   **Vite Dev Server (`pnpm run dev`):** Compila módulos React al vuelo en memoria RAM y los sirve en el puerto `5173`. Es ideal para desarrollo rápido local con autorecarga (HMR).
*   **Vite Build (`pnpm run build`):** Traduce todo el código React y TypeScript a archivos estáticos HTML, JS y CSS minificados optimizados en la carpeta `dist`.
*   **Static Hosting:** En lugar de mantener dos servidores activos, el propio servidor web de Chainlit sirve estos archivos estáticos en su puerto. Esto unifica la API y la UI bajo el mismo puerto, anulando por completo los problemas de CORS y puertos cruzados.

---

## 5. Solución Implementada

Para resolver todos los síntomas descritos de forma limpia y definitiva, se aplicaron dos cambios fundamentales en el proyecto:

### A) Enrutamiento Dinámico e Inteligente en el Cliente de API
Modificamos el archivo [chainlitClient.ts](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/frontend/src/api/chainlitClient.ts) para detectar en caliente el puerto del navegador:

```typescript
import { ChainlitAPI } from '@chainlit/react-client';

// Detección automática del entorno de ejecución:
// 1. Si estamos en desarrollo con Vite (puerto 5173), apuntamos al backend en el puerto 8000.
// 2. Si estamos en producción/intranet (servido por Chainlit), usamos el origen dinámico de la página.
const isDev = window.location.port === "5173";
const CHAINLIT_SERVER_URL = isDev
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;

export const apiClient = new ChainlitAPI(CHAINLIT_SERVER_URL, "webapp");
```

### B) Unificación del Hosting mediante `custom_build`
Descomentamos y configuramos la variable de construcción en el archivo de configuración de Chainlit [.chainlit/config.toml](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/.chainlit/config.toml#L164-L167):

```toml
# Especifica el directorio donde se ubica el build compilado de React
custom_build = "frontend/dist"
```

### C) Compilación y Despliegue en un Solo Comando
1.  Compilamos el frontend de React para generar los estáticos finales en `frontend/dist`:
    ```bash
    cd frontend
    pnpm run build
    ```
2.  Iniciamos la aplicación escuchando en la IP de la intranet en el puerto `8000`:
    ```bash
    chainlit run agente-mcp/app.py --host 0.0.0.0 --port 8000
    ```

---

## 6. Arquitectura Final de Red

El siguiente diagrama detalla cómo fluyen las peticiones de red y la entrega de recursos bajo el nuevo esquema unificado:

```text
Entorno Corporativo (Intranet)
=============================================================================

  Usuario en la Intranet             Servidor Físico (OpenEnergy Host)
 [ IP: 11.170.16.XXX ]               [ IP: 11.170.16.146 ]
+----------------------+            +---------------------------------------+
|  Navegador Web       |            |  Chainlit Server (Puerto: 8000)       |
|                      |            |                                       |
|  http://IP:8000  --------GET----->|  1. Sirve Frontend Estático           |
|                      |            |     (Desde: frontend/dist)            |
|                      |            |                                       |
|  Carga HTML/JS/CSS  <---RETORNA---|                                       |
|  (UI OpenEnergy)     |            |  2. Expone Endpoints de API           |
|                      |            |     (/auth/config, /user, etc.)       |
|  Conecta WebSocket   |            |                                       |
|  (ws://IP:8000)  <=====WS/WSs====>|  3. Conexiones WebSocket en Vivo      |
+----------------------+            +-------------------+-------------------+
                                                        |
                                                        v (Llamadas Locales)
                                            +-------------------------------+
                                            |  Servidor MCP (Puerto: 8001)  |
                                            |  - Herramientas SQL           |
                                            |  - Acceso a base de datos     |
                                            +-------------------------------+
```

---

## 7. Checklist para Futuros Despliegues en Intranet

Antes de publicar cualquier actualización en la red corporativa, verifica los siguientes puntos:

- [ ] **Compilación de Frontend Realizada:** ¿Has ejecutado `pnpm run build` en la carpeta del frontend tras modificar archivos React/CSS?
- [ ] **Directiva `custom_build` Activa:** ¿Está descomentada la línea `custom_build = "frontend/dist"` en `.chainlit/config.toml`?
- [ ] **Coincidencia de `CHAINLIT_URL`:** ¿La IP y el puerto en la variable `CHAINLIT_URL` del archivo `.env` coinciden exactamente con la dirección a la que accederán los usuarios desde sus navegadores?
- [ ] **Secretos de Autenticación Seguros:** ¿La variable `CHAINLIT_AUTH_SECRET` en el `.env` tiene una longitud segura de al menos 32 caracteres?
- [ ] **Binding del Host:** ¿Se está iniciando el servidor con la bandera `--host 0.0.0.0` para permitir accesos externos?
- [ ] **Configuración del Servidor MCP:** ¿La variable `MCP_SERVER_URL` del `.env` apunta a la IP correcta del servidor MCP que está corriendo?
- [ ] **Limpieza de Cookies de Sesión:** Si la página se queda pegada tras cambiar de IP o puerto, ¿se borraron los datos del sitio desde la consola de desarrollador del navegador (o en una ventana de incógnito)?

---

## 8. Lecciones Aprendidas

1.  **Cero Puertos Fijos en Código de Cliente:** Los frontends nunca deben asumir en qué puerto o dominio está corriendo su backend en producción. Usar rutas relativas o `window.location.origin` es fundamental para la portabilidad.
2.  **La Simplicidad de un Puerto Único:** Separar frontend y backend en diferentes procesos durante el desarrollo es cómodo, pero en producción, alojar el frontend compilado como archivos estáticos dentro del propio backend simplifica el despliegue a una sola línea de comando, eliminando dolores de cabeza por CORS, certificados SSL cruzados y firewalls.
3.  **Seguridad y Contexto en Redes Corporativas:** Las redes internas corporativas imponen restricciones más duras sobre cookies y sockets. Probar siempre desde una pestaña de incógnito limpia al cambiar configuraciones previene falsos negativos por almacenamiento en caché de credenciales desactualizadas.
