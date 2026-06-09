# Arquitectura de Ecosistema Tecnológico: OpenEnergy / OSAM v2

Este documento redefine el proyecto **OpenEnergy** no solo como un sistema de software aislado, sino como un **ecosistema tecnológico integrado**. Un ecosistema se caracteriza por la interacción y coadaptación de múltiples entidades autónomas: usuarios con roles específicos, proveedores de identidad centralizados (Keycloak), modelos de lenguaje de inteligencia artificial (Google Gemini), protocolos de comunicación semántica (MCP) y almacenes de datos institucionales (Oracle), todos integrados a través de fronteras de red híbridas.

---

## 1. Visión del Ecosistema Tecnológico

El ecosistema de OpenEnergy está diseñado bajo un paradigma de **desacoplamiento total, gobernanza semántica y seguridad perimetral**. Los componentes no dependen de ubicaciones fijas ni de integraciones rígidas, sino que colaboran mediante contratos bien definidos (APIs, WebSockets, payloads estructurados y protocolos estandarizados).

```mermaid
graph TB
    %% Definición de Zonas del Ecosistema
    subgraph Zona_Usuario ["1. Entorno de Usuario"]
        U_Analista["👤 Analista de Energía (Región/Sede)"]
        U_Gerente["👤 Gerente Corporativo (Operaciones/Comercial)"]
    end

    subgraph Zona_Nube ["2. Nube Pública o Servidor de Aplicación"]
        FE["💻 Frontend React (SPA)<br>• TanStack Table<br>• Vega-Lite Canvas"]
        BE["⚙️ Backend Chainlit (Python)<br>• WebSocket Server<br>• RLS Engine"]
    end

    subgraph Zona_IAM ["3. Capa de Identidad (IAM)"]
        KC["🔐 Keycloak Corporativo<br>• OIDC / OAuth2<br>• Token JWT firmado"]
    end

    subgraph Zona_IA ["4. Capa Cognitiva (Google AI)"]
        Gemini["🧠 Gemini LLM Router<br>• Mapeo Semántico en Caliente<br>• Inferencia OSAM"]
    end

    subgraph Zona_Intranet ["5. Intranet Corporativa (Osinergmin)"]
        direction TB
        tunnel["☁️ Cloudflare Tunnel / VPN Client"]
        MCP["🔌 Servidor MCP (FastAPI)<br>• Catalogo Semántico<br>• Oracle Dictionary Reader"]
        Oracle[("🗄️ Base de Datos Oracle<br>• ES_DATGOB_CV")]
    end

    %% Relaciones y Canales de Comunicación
    U_Analista -->|Accede vía Web HTTPS| FE
    U_Gerente -->|Accede vía Web HTTPS| FE
    
    %% Autenticación
    FE -->|1. Redirección OIDC| KC
    KC -->|2. Retorna Token JWT| FE
    FE -->|3. WebSocket Auth (JWT Token)| BE
    
    %% Flujo de Inferencia y Datos
    BE -->|4. Prompt Inyectado con RLS Claims| Gemini
    Gemini -->|5. Tool Call (json-osam)| BE
    BE -->|6. Petición Segura a MCP| tunnel
    tunnel -->|7. Proxy Inverso Seguro| MCP
    MCP -->|8. SQL Seguro (DQL)| Oracle
    Oracle -->|9. Metadata y Registros| MCP
    MCP -->|10. Data JSON| BE
    BE -->|11. Mensaje con bloque json-osam| FE
    
    %% Estilos de los nodos para calidad visual
    classDef usuario fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;
    classDef nube fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#14532d;
    classDef iam fill:#faf5ff,stroke:#9333ea,stroke-width:2px,color:#581c87;
    classDef ia fill:#fff7ed,stroke:#ea580c,stroke-width:2px,color:#7c2d12;
    classDef intranet fill:#f8fafc,stroke:#475569,stroke-width:2px,color:#0f172a;

    class U_Analista,U_Gerente usuario;
    class FE,BE nube;
    class KC iam;
    class Gemini ia;
    class tunnel,MCP,Oracle intranet;
```

---

## 2. Los Ejes del Ecosistema

### 2.1. Identidad, Seguridad y Autorización (Keycloak + RLS)
La seguridad del ecosistema no reside en el backend ni en la base de datos de forma aislada, sino que se gestiona mediante un flujo continuo de **delegación de identidad**:

1.  **Autenticación Delegada (OIDC):** El usuario no ingresa credenciales directas en la base de datos ni en el backend de OpenEnergy. La autenticación se delega completamente a **Keycloak Corporativo** mediante el protocolo OpenID Connect (OIDC).
2.  **Propagación de Identidad:** Una vez autenticado, Keycloak emite un token JWT firmado. El frontend (React) envía este token en el apretón de manos de WebSocket hacia el backend de Chainlit.
3.  **Extracción de Claims y Row-Level Security (RLS):** El backend descodifica el JWT de forma segura (verificando la firma con el set de llaves públicas JWKS de Keycloak) y extrae atributos del usuario (ej: `departamento_sede`, `rol_institucional`).
4.  **Inyección Determinista de Filtros:** El rol del usuario define un filtro geográfico estricto. Si el usuario pertenece a la sede *Moquegua*, el Gateway de datos de OpenEnergy (`osam_gateway.py`) inyecta automáticamente la cláusula `DEPARTAMENTO = 'MOQUEGUA'` en la consulta física final que se hace en base de datos. Ningún usuario puede ver registros fuera de su jurisdicción autorizada por Keycloak.

> [!IMPORTANT]
> **Seguridad Anti-Inyección (DML/DDL):** El ecosistema restringe por arquitectura el envío de comandos de modificación de datos. El LLM solo genera intenciones de lectura (`fields`, `dimensions`, `filters`) de lectura libre de SQL directo, y el compilador de base de datos compila e inyecta parámetros de forma totalmente tipada sobre DuckDB u Oracle.

---

### 2.2. Integración Semántica y Catálogo en Caliente (MCP)
El Model Context Protocol (MCP) actúa como el **traductor y mediador universal** entre el catálogo físico de base de datos y la capa cognitiva de inteligencia artificial:

*   **Catálogo Dinámico desde Oracle:** En lugar de mantener archivos de definición estáticos o modelos hardcodeados en el backend, el servidor MCP realiza consultas al diccionario del sistema de Oracle (`USER_TAB_COMMENTS` y `USER_COL_COMMENTS`).
*   **Enriquecimiento en Caliente:** El MCP expone a la IA descripciones ricas de cada tabla y columna (ej: *`CMO_TX_CENTRAL_GEN` almacena la generación horaria de centrales eléctricas en megavatios*).
*   **Inferencia Semántica del LLM:** La IA de Google Gemini recibe el catálogo dinámico y traduce la intención conversacional del usuario (lenguaje natural) a contratos lógicos de OSAM. El LLM no necesita saber si una columna cambió de nombre; simplemente lee el catálogo expuesto por el MCP y realiza el mapeo semántico en tiempo real.

---

### 2.3. Conectividad e Infraestructura Híbrida (La Frontera de Redes)
Dado que el servidor MCP y la base de datos Oracle residen dentro de la intranet privada de Osinergmin (restringida por estrictos Firewalls) y el cliente/servidor de UI puede estar hospedado en Railway (nube pública), el ecosistema implementa estrategias de **túnel inverso y redes mesh**:

*   **Estrategia Cloudflare Tunnel (cloudflared):** Un agente liviano de Cloudflare levantado en la intranet corporativa crea una conexión TLS de salida hacia la red de Cloudflare. Esto permite exponer el puerto del MCP de forma segura a través de un subdominio HTTPS estático (`https://mcp-api.osinergmin.gob.pe`) sin abrir puertos de entrada en el Firewall corporativo.
*   **Restricción por IP / Token:** El túnel inverso restringe el acceso de modo que solo peticiones con el encabezado `Authorization` o originadas desde el clúster de Railway puedan consumir el catálogo de datos.
*   **Resiliencia por Mock Local:** Si el túnel de red o la intranet experimentan un corte de conectividad, el backend activa automáticamente un módulo de resiliencia local que responde consultas utilizando simulaciones idénticas de las tablas corporativas, garantizando la continuidad de la experiencia de usuario (UX).

---

## 3. Matriz de Interacción del Ecosistema

La siguiente tabla describe la participación y responsabilidades de cada componente dentro del ecosistema tecnológico:

| Componente | Tipo de Entidad | Protocolo / Interfaz | Control de Seguridad | Rol en el Ecosistema |
| :--- | :--- | :--- | :--- | :--- |
| **Keycloak Corporativo** | Externo (IAM) | OAuth2 / OIDC | HTTPS, Firmas JWT (JWKS) | Proveedor centralizado de identidad y claims de autorización de usuario. |
| **Frontend React / Vite** | Interno (Presentación) | WebSockets / REST | TLS, Almacenamiento seguro de tokens | Renderizado interactivo, captura de tokens y parsing de payloads analíticos. |
| **Backend app.py (Chainlit)** | Interno (Orquestador) | WebSocket / HTTP | Validación JWT, Sanitización de payloads | Orquestador conversacional, validador de roles y distribuidor de intenciones. |
| **OSAM Gateway (Python)** | Interno (Compilador) | Python API | Row-Level Security (RLS) determinista | Validador de columnas y compilador de SQL seguro sobre DuckDB/Oracle. |
| **Google Gemini API** | Externo (Cognitivo) | HTTPS REST (Google AI) | API Keys seguras, límites de cuota | Traductor de lenguaje natural a intenciones estructuradas del metamodelo OSAM. |
| **Cloudflare Tunnel** | Infraestructura (Red) | TLS Túnel Inverso (Saliente) | Listas Blancas de IP, Autenticación de Origen | Enlace seguro que puentea la nube pública con la Intranet corporativa privada. |
| **Servidor MCP (FastAPI)** | Interno (Datos) | Model Context Protocol | Filtros DML, solo lectura (Selects) | Catálogo dinámico y pasarela de datos gobernados desde Oracle. |
| **Oracle Database** | Externo (Persistencia) | SQL Net / TCP | Privilegios mínimos (Only Select), RLS físico | Fuente definitiva de la verdad analítica y comentarios de negocio de Osinergmin. |

---

## 4. Flujo de Datos Transversal del Ecosistema

Para ilustrar el funcionamiento conjunto, examinemos el ciclo de vida de una consulta:

```
[Usuario] 
   │ 1. Se autentica en Keycloak ➔ Recibe JWT
   ▼
[React UI] 
   │ 2. Envía pregunta en lenguaje natural + JWT a través de WebSocket
   ▼
[Chainlit Backend]
   │ 3. Valida JWT ➔ Extrae claim "DEPARTAMENTO = 'MOQUEGUA'"
   │ 4. Envía a Gemini: Contexto + Pregunta + Filtro Geográfico Obligatorio
   ▼
[Gemini LLM]
   │ 5. Mapea la pregunta al catálogo dinámico leído desde el MCP
   │ 6. Retorna Tool Call: query_data_osam(fields=['POTENCIA_MW'], filter={'DEPARTAMENTO': 'MOQUEGUA'})
   ▼
[OSAM Gateway]
   │ 7. Valida que 'POTENCIA_MW' existe en el catálogo para evitar inyección SQL
   │ 8. Fuerza la inyección de RLS: "DEPARTAMENTO = 'MOQUEGUA'"
   │ 9. Ejecuta la consulta SQL segura compilada en DuckDB / Oracle (vía MCP)
   ▼
[React UI]
   │ 10. Recibe payload json-osam con datos procesados + Provenance (Linaje)
   │ 11. Renderiza Gráfico Vega-Lite interactivo filtrado exclusivamente para Moquegua
```

Con esta arquitectura, **OpenEnergy** se consagra como un ecosistema dinámico que equilibra la flexibilidad analítica de la inteligencia artificial con las estrictas políticas de gobernanza, seguridad de red y seguridad de datos de **Osinergmin**.
