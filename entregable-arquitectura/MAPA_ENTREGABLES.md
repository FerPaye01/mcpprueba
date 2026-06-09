# Mapa de Entregables de Arquitectura: OpenEnergy / OSAM v2

Este documento sirve como **índice maestro** para navegar por todos los archivos recopilados y organizados dentro del directorio `entregable-arquitectura/`. Los archivos han sido estructurados para representar el ciclo de diseño, la investigación, la conectividad y el desarrollo del ecosistema.

---

## 🗺️ Estructura del Directorio de Entregables

```
entregable-arquitectura/
│
├── MAPA_ENTREGABLES.md                  # Este documento (índice maestro)
├── ecosistema_arquitectura.md           # [Nuevo] Especificación de Arquitectura de Ecosistema
├── propuesta_modularizacion.md          # [Nuevo] Propuesta de estructuración modular del código backend
├── cartografia_arquitectonica.md        # Mapa físico de código fuente y grafo de dependencias
├── mcp_connection_strategy.md           # Opciones de conectividad híbrida Intranet/Nube
├── indicaciones.md                      # Configuración de Firewall y exposición interna
├── prompt_despliegue.md                 # Guía para el despliegue del ecosistema
├── README.md                            # Guía general del proyecto
│
├── .analisis/                           # Diseños y Decisiones Técnicas (ADR)
│   ├── ARCHITECTURE_DESIGN.md           # Diseño desacoplado, ADRs y Matriz de Trazabilidad
│   ├── REQUIREMENTS_SPEC.md             # Requisitos del sistema
│   ├── SPRINT_ROADMAP.md                # Cronograma evolutivo del proyecto
│   ├── TEST_ACCEPTANCE.md               # Criterios de aceptación y pruebas
│   └── PROMPT_ORQUESTADOR_DISENO.md     # Instrucciones del Orquestador de la IA
│
├── .investigacion/                      # Investigaciones y Reportes de Ingeniería
│   ├── Arquitectura Analítica IA.md     # Reporte sobre resiliencia e IA analítica
│   └── Estrategias de Visualización.md  # Análisis de renderizado dinámico Vega-Lite/SVG
│
├── guias/                               # Instrucciones de Infraestructura Paso a Paso
│   └── guia_cloudflare_tunnel.md        # Configuración detallada de Cloudflare Tunnels (Inverso)
│
├── osinergmin-theming/                  # Identidad Visual y Marca
│   └── references/branding.md           # Tokens de diseño, colores institucionales y tipografía
│
├── chart_creation_chainlit/             # Guías de Renderizado Conversacional
│   └── SKILL.md                         # Lineamientos para visualizaciones con Chainlit
│
└── flashcards/                          # Material Formativo y Validación
    ├── flashcards-conexion.md           # Tarjetas didácticas de red y MCP
    ├── flashcards-llm.md                # Tarjetas didácticas sobre prompt-engineering
    └── prompt-examen.md                 # Evaluaciones de conocimiento técnico
```

---

## 📄 Detalle de Entregables Clave

### 🛡️ 1. Arquitectura y Ecosistema
*   **[ecosistema_arquitectura.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/ecosistema_arquitectura.md):** Define la arquitectura global desde el punto de vista del ecosistema (Usuarios + Keycloak IAM + Nube Pública + Intranet Osinergmin + Google Gemini + Servidor MCP). Detalla los flujos de autorización JWT y seguridad Row-Level Security (RLS).
*   **[propuesta_modularizacion.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/propuesta_modularizacion.md):** Propone la descomposición del código backend monolítico en módulos limpios y desacoplados basados en Responsabilidad Única.
*   **[cartografia_arquitectonica.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/cartografia_arquitectonica.md):** Analiza el código fuente actual, definiendo dependencias físicas entre componentes, diagramas de secuencia analítica y de autenticación, y linaje de datos.
*   **[.analisis/ARCHITECTURE_DESIGN.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/.analisis/ARCHITECTURE_DESIGN.md):** Contiene la matriz de trazabilidad de requisitos a componentes y los Registros de Decisiones de Arquitectura (ADRs), justificando las decisiones de diseño.

### 🌐 2. Conectividad, Redes e Infraestructura
*   **[mcp_connection_strategy.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/mcp_connection_strategy.md):** Detalla las 4 estrategias analizadas para unir de forma segura la nube pública (Vite/Chainlit) con la intranet privada de Osinergmin (MCP/Oracle DB).
*   **[guias/guia_cloudflare_tunnel.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/guias/guia_cloudflare_tunnel.md):** Instrucciones paso a paso de comandos e instalación del túnel inverso para saltarse restricciones de puertos y firewalls corporativos.
*   **[indicaciones.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/indicaciones.md):** Configuración recomendada para levantar el agente local expuesto en la intranet y añadir reglas en el Firewall de Windows Defender.

### 🎨 3. Experiencia de Usuario y Presentación
*   **[osinergmin-theming/references/branding.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/osinergmin-theming/references/branding.md):** Define la paleta de colores oficial, tipografía y estilo visual corporativo que implementa el frontend en React para verse premium y alineado con Osinergmin.
*   **[chart_creation_chainlit/SKILL.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/chart_creation_chainlit/SKILL.md):** Lineamientos prácticos de cómo Chainlit y la UI de frontend interpretan y renderizan visualizaciones de datos y gráficos vectoriales dinámicos.

---

## 🚀 Próximos Pasos Recomendados
1.  **Revisión en Equipo de la Arquitectura del Ecosistema ([ecosistema_arquitectura.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/ecosistema_arquitectura.md)):** Validar los flujos de Keycloak y mapeo de RLS regional.
2.  **Configuración del Entorno de Red:** Seguir las instrucciones de [guia_cloudflare_tunnel.md](file:///C:/Users/opaye/Proyectos/MCPdinamicoPrueba/entregable-arquitectura/guias/guia_cloudflare_tunnel.md) para habilitar el canal seguro entre la base de datos de Osinergmin y la interfaz de usuario en la nube.
