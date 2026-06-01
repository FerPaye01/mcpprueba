# Plan de Pruebas de Aceptación (UAT) y Robustez

## 1. Matriz de Escenarios de Pruebas de Aceptación de Usuario
| ID | Componente / Caso de Uso | Escenario de Prueba / Estímulo | Resultado Esperado |
| :--- | :--- | :--- | :--- |
| **UAT-01** | Resiliencia de Ingesta | Carga de archivos con columnas desordenadas, tipos de datos mixtos o codificación corrupta. | El sistema normaliza mediante heurísticas o desvía los registros corruptos sin detener el hilo principal. |
| **UAT-02** | Comportamiento Límite | Procesamiento de un registro con valores nulos, vacíos o que exceden la longitud máxima estándar. | Filtrado controlado, truncamiento automático o asignación de valores por defecto (NaN/Null-safe). |
| **UAT-03** | Cumplimiento de SLA | Inyección de carga masiva de datos en el entorno local (Benchmarking de estrés). | El procesamiento finaliza dentro del tiempo estipulado en los RNF sin desbordamiento de memoria (OOM). |
| **UAT-04** | Casos del "Camino Feliz" | Flujo estándar de datos limpios que cumplen perfectamente con el contrato. | Procesamiento directo con métricas de precisión óptimas según los objetivos del negocio. |

## 2. Patrones de Robustez Empresarial
* **Manejo de Errores Estructurados (Dead Letter Queue - DLQ):** El sistema no debe usar simples logs de texto para fallos críticos de datos. Los registros corruptos se desvían de forma estructurada a un sumidero de errores (`errores_[modulo].parquet` / base de datos de auditoría) para permitir auditorías post-mortem sin degradar el pipeline.
* **Snapshotting (Checkpoints de Estado):** En ejecuciones prolongadas, el sistema debe guardar estados intermedios en almacenamiento persistente tras cada fase crítica. Si ocurre una interrupción (caída de energía/red), el proceso debe reanudarse desde el último checkpoint exitoso.
* **Estrategia de Tolerancia a Fallos en APIs Externas:** Toda llamada a servicios de terceros debe estar protegida por políticas de *Exponential Backoff* con aleatoriedad (jitter) y *Circuit Breakers* para evitar el bloqueo indefinido de recursos locales.

## 3. Protocolo de Evaluación y Métricas de Calidad Humana
1.  **Muestreo Estratificado:** Selección de una muestra estadísticamente representativa del universo de datos procesados para su validación manual.
2.  **Cálculo de Consenso (ej. Cohen's Kappa / Fleiss' Kappa):** Si el sistema involucra evaluación humana previa (etiquetado), se debe medir el grado de acuerdo entre evaluadores independientes para asegurar la fiabilidad de los datos de prueba.
3.  **Auditoría de Transparencia (Explicabilidad):** Revisión sistemática de las variables internas que causaron las decisiones del software para garantizar que el modelo no se esté guiando por sesgos de ruido (ej. variables de tiempo o identificadores vacíos).