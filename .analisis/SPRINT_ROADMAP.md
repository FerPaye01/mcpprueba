# Hoja de Ruta del Proyecto & Plan de Sprints

## 1. Cronograma de Desarrollo por Componentes
### Semana 1: Capa de Ingesta y Preparación de Datos
* **Enfoque:** Construcción de adaptadores de entrada, validación de contratos de datos y manejo de excepciones iniciales.
* **Entregables Técnicos:** `[nombre_modulo]_adapter.py`, scripts de validación de esquemas, configuración de almacenamiento base.

### Semana 2: Core Lógico y Procesamiento Determínistico
* **Enfoque:** Implementación de algoritmos principales, extracción de características (features) y lógica pura de negocio.
* **Entregables Técnicos:** Módulos de procesamiento centralizados, pipelines de transformación optimizados (operaciones vectorizadas/paralelas).

### Semana 3: Orquestación, Integración de Servicios y Enrutamiento
* **Enfoque:** Conexión entre la capa rápida de procesamiento y servicios de alta fidelidad o APIs externas mediante lógica orientada a la incertidumbre o costos.
* **Entregables Técnicos:** Orquestadores de flujo, manejadores de reintentos (Exponential Backoff), lógica de enrutamiento dinámico.

### Semana 4: Interfaces de Consumo, Validación y Cierre
* **Enfoque:** Interfaces de usuario (Dashboards/APIs públicas), validación del sistema contra datos de control y versionamiento final.
* **Entregables Técnicos:** Aplicación de visualización / API Endpoint, datasets de control versionados, congelamiento de código (`git tag`).

---

## 2. Dependencias de Bloqueo Críticas (Ruta Crítica)
1.  **Validación de Entrada (Hito Día X):** Si la capa de adaptación no normaliza los esquemas de forma limpia, los componentes lógicos de la Semana 2 procesarán datos corruptos, invalidando las pruebas unitarias.
2.  **Optimización del Core (Hito Día Y):** Si el procesamiento no se vectoriza o paraleliza en la fase temprana, los SLAs de rendimiento fallarán masivamente al integrar el pipeline completo.
3.  **Contrato de Interfaces (Hito Día Z):** Las vistas de presentación dependen directamente de la estructura de metadatos generada por los orquestadores; cambios tardíos romperán la UI de forma catastrófica.