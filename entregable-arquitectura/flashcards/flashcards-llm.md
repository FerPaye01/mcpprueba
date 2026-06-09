P: ¿Cuál fue el problema principal al usar inicialmente la serie de modelos \( gemini-3.x \) a través del SDK de OpenAI para llamadas a herramientas en múltiples pasos?
R: Que los modelos \( gemini-3.x \) requieren una firma de pensamiento digitalizada \( thought_signature \) en las llamadas a funciones intermedias. Como el SDK estándar de OpenAI no reconoce este campo no estándar, lo descarta del objeto deserializado de llamada a herramientas, provocando que la API de Google devuelva un error \( 400 INVALID_ARGUMENT \) en el siguiente turno.

P: ¿Cómo se solucionó a nivel de código el error de la firma de pensamiento \( thought_signature \) faltante en los modelos Gemini al procesar el streaming de respuesta?
R: Extrayendo manualmente el campo \( extra_content \) del diccionario interno \( model_extra \) (o la propiedad directa \( extra_content \)) de cada fragmento \( ChoiceDeltaToolCall \) del flujo, y fusionando de vuelta este hash en la propiedad \( extra_content \) de la lista de llamadas a herramientas que se inyectan en el historial de mensajes del asistente.

P: ¿Cuál es el propósito del mecanismo de enrutamiento resiliente (Fallback Loop) implementado al invocar completados de chat en \( app.py \)?
R: Permitir que el sistema intente utilizar secuencialmente una lista de modelos prioritarios (por ejemplo, \( gemini-3.1-flash-lite \) con su alta cuota de 500 peticiones diarias) y, en caso de fallo por saturación de cuota de API \( 429 \) o errores de servidor, caiga automáticamente a modelos de respaldo como \( gemini-2.5-flash-lite \) o proveedores alternativos en \( OpenRouter \).

P: ¿Qué estrategia de reintento temporal se ejecuta en el bucle de modelos ante un error de tipo Rate Limit \( 429 \) para evitar fallos inmediatos de conexión?
R: Se captura el error \( 429 \) y se suspende la ejecución de forma asíncrona mediante \( await asyncio.sleep(4) \) antes de reintentar con el mismo modelo en un segundo intento, dando tiempo a que la ventana de cuota por segundo o minuto se libere.

P: ¿De qué manera el frontend de React facilita la contextualización de datos del LLM en el primer turno de una sesión limpia tras borrar el chat?
R: Al conectarse o reconectarse, el frontend envía un objeto de configuración que contiene el arreglo \( datasets_activos \) con los metadatos completos de las tablas importadas (nombre, \( schema \), e \( id_catalogo \)), el cual se almacena en la sesión del servidor en la variable \( filtros_activos \).

P: ¿Cómo se inyecta el contexto de datasets seleccionados en el prompt del sistema y qué instrucción recibe el LLM para optimizar su toma de decisiones?
R: Se concatena en el System Prompt el nombre, esquema e ID de catálogo de cada tabla activa bajo la etiqueta \( Datasets/Tablas Activos e Importados: \). Se instruye al LLM a priorizar y asumir estas tablas ante consultas analíticas ambiguas, utilizando sus valores correspondientes para rellenar los parámetros obligatorios de la herramienta \( query_data \).

P: ¿Qué limitador de consumo justo (Rate Limiting) se implementó a nivel de sesión de usuario en el backend para salvaguardar la API Key frente a abusos o bucles infinitos?
R: Una función controladora de consumo que rastrea las marcas de tiempo de las peticiones en la sesión y bloquea las llamadas devolviendo un mensaje de advertencia si el usuario excede un umbral máximo de \( 50 \) consultas en una ventana temporal de \( 10 \) minutos.

P: ¿Cómo resuelve el sistema la generación de gráficos interactivos de forma automática (Fallback Heurístico) si el LLM no invoca explícitamente la herramienta \( crear_grafico \)?
R: Analizando al final del turno de mensaje si el usuario incluyó palabras clave de tendencia (ej. \( curva \), \( tendencia \)) y si existen datos tabulares almacenados en \( last_tool_result \). Si se cumplen ambos criterios, se ejecuta la lógica de renderizado gráfico de Plotly de forma automatizada y se inyecta un bloque \( json-chart \) en el mensaje de respuesta.

P: ¿Cómo se personaliza dinámicamente el System Prompt en \( app.py \) dependiendo del perfil/rol del usuario autenticado en el sistema?
R: Al iniciar la sesión en \( @cl.on_chat_start \), el backend identifica el nombre de usuario. Si coincide con un rol de negocio (ej. \( gerente_comercial \) o \( gerente_operaciones \)), anexa instrucciones restrictivas al prompt original para priorizar ciertas perspectivas de análisis, como precios y tarifas (comercial) o infraestructura física y subestaciones (operaciones).

P: ¿Qué optimización de limpieza de historial (Pruning/Flattening) se ejecuta en \( stream_llm_response \) para evitar el consumo excesivo de tokens y colisiones en la API de Gemini?
R: Una rutina que extrae el System Prompt y los mensajes del turno actual de forma intacta, pero simplifica el historial de turnos pasados removiendo todas las llamadas a herramientas intermedias y los voluminosos outputs de JSON devueltos, dejando únicamente los mensajes textuales de tipo \( user \) y \( assistant \).

P: ¿Qué reglas críticas de mapeo de filtros se inyectan en el prompt para evitar que el LLM cometa errores de sintaxis o semántica al filtrar la tabla de centrales \( CMO_TX_CENTRAL_GEN \)?
R: Se le prohíbe explícitamente utilizar la columna \( DE_FUENTE_ENER \) para buscar tecnologías debido a su formato de texto libre; en su lugar, se le obliga a emplear la columna \( TI_TIPO_CENTRAL \) en mayúsculas (ej. \( CENTRAL SOLAR \), \( CENTRAL EOLICA \)), y filtrar el estado operativo mediante \( IN_ESTADO = 'EN SERVICIO' \).
