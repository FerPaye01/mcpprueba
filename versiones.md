# Inventario de Versiones — OpenEnergy 
> Última revisión: 2026-06-10 | Responsable: Equipo TI Osinergmin

---

## 🐍 Backend (Python)

| Componente | Versión Actual | Última Estable | ¿Actualizar? | Licencia | Riesgo de Cambio | Comando de Verificación |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Python** | `3.13.13` | `3.13.13` ✅ | ⏸ Fijar | PSF-2.0 | 🔴 Crítico | `python --version` |
| **Chainlit** | `2.11.1` | `2.11.1` ✅ | ⏸ Fijar | Apache-2.0 ⚠️ | 🔴 Crítico | `pip show chainlit` |
| **FastAPI** | `0.136.3` | `0.136.3` ✅ | ✅ Al día | MIT | 🟡 Medio | `pip show fastapi` |
| **Uvicorn** | `0.48.0` | `0.48.0` ✅ | ✅ Al día | BSD-3 | 🟡 Medio | `pip show uvicorn` |
| **Starlette** | `1.1.0` | `1.1.0` ✅ | ✅ Al día | BSD-3 | 🟡 Medio | `pip show starlette` |
| **DuckDB** | `1.5.3` | `1.5.3` ✅ | ✅ Al día | MIT | 🔴 Crítico | `pip show duckdb` |
| **Pandas** | `3.0.3` | `3.0.3` ✅ | ✅ Al día | BSD-3 | 🟡 Medio | `pip show pandas` |
| **MCP SDK** | `1.27.1` | `1.27.1` ✅ | ✅ Al día | MIT | 🟡 Medio | `pip show mcp` |
| **OpenAI SDK** *(cliente Gemini)* | `2.38.0` | `2.41.0` 🔼 | ✅ Sí | Apache-2.0 | 🟢 Bajo | `pip show openai` |
| **Pydantic** | `2.13.4` | `2.13.4` ✅ | ✅ Al día | MIT | 🟡 Medio | `pip show pydantic` |
| **httpx** | `0.28.1` | `0.28.1` ✅ | ✅ Al día | BSD-3 | 🟢 Bajo | `pip show httpx` |
| **PyJWT** | `2.13.0` | `2.13.0` ✅ | ✅ Al día | MIT | 🟡 Medio | `pip show pyjwt` |
| **python-socketio** | `5.16.2` | `5.16.2` ✅ | ✅ Al día | MIT | 🟡 Medio | `pip show python-socketio` |
| **Matplotlib** | `3.10.9` | `3.10.9` ✅ | ✅ Al día | PSF/BSD | 🟢 Bajo | `pip show matplotlib` |
| **Plotly** | `6.7.0` | `6.8.0` 🔼 | ✅ Sí | MIT | 🟢 Bajo | `pip show plotly` |
| **python-dotenv** | `1.2.2` | `1.2.2` ✅ | ✅ Al día | BSD-3 | 🟢 Bajo | `pip show python-dotenv` |
| **requests** | `2.34.2` | `2.34.2` ✅ | ✅ Al día | Apache-2.0 | 🟢 Bajo | `pip show requests` |

---

## ⚛️ Frontend (Node / React)

| Componente | Versión Actual | Última Estable | ¿Actualizar? | Licencia | Riesgo de Cambio | Comando de Verificación |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Node.js** | `v24.15.0` | `v24.x (LTS)` ✅ | ✅ Al día | MIT | 🔴 Crítico | `node --version` |
| **pnpm** | *(verificar)* | `10.x` | *(verificar)* | MIT | 🟢 Bajo | `pnpm --version` |
| **Vite** | `^8.0.12` | `8.x` ✅ | ✅ Al día | MIT | 🟡 Medio | `pnpm list vite` |
| **TypeScript** | `~6.0.2` | `6.x` ✅ | ✅ Al día | Apache-2.0 | 🟡 Medio | `pnpm list typescript` |
| **React** | `^18.3.1` | `19.2.7` 🔼 | ⏸ Esperar | MIT | 🔴 Crítico | `pnpm list react` |
| **React DOM** | `^18.3.1` | `19.2.7` 🔼 | ⏸ Esperar | MIT | 🔴 Crítico | `pnpm list react-dom` |
| **@chainlit/react-client** | `^0.4.2` | `0.4.2` ✅ | ⏸ Fijar | Apache-2.0 | 🔴 Crítico | `pnpm list @chainlit/react-client` |
| **@tanstack/react-table** | `^8.21.3` | `8.21.3` ✅ | ✅ Al día | MIT | 🟡 Medio | `pnpm list @tanstack/react-table` |
| **Vega** | `^6.2.0` | `6.2.0` ✅ | ✅ Al día | BSD-3 | 🟡 Medio | `pnpm list vega` |
| **Vega-Lite** | `^6.4.3` | `6.4.3` ✅ | ✅ Al día | BSD-3 | 🟡 Medio | `pnpm list vega-lite` |
| **vega-embed** | `^7.1.0` | `7.1.0` ✅ | ✅ Al día | BSD-3 | 🟡 Medio | `pnpm list vega-embed` |
| **socket.io-client** | `^4.8.3` | `4.8.3` ✅ | ✅ Al día | MIT | 🟡 Medio | `pnpm list socket.io-client` |
| **Recoil** | `^0.7.7` | `0.7.7` ✅ | ⏸ Esperar | MIT | 🟡 Medio | `pnpm list recoil` |
| **react-markdown** | `^10.1.0` | `10.1.0` ✅ | ✅ Al día | MIT | 🟢 Bajo | `pnpm list react-markdown` |
| **lucide-react** | `^1.17.0` | `1.17.0` ✅ | ✅ Al día | ISC | 🟢 Bajo | `pnpm list lucide-react` |
| **TailwindCSS** | `^4.3.0` | `4.3.0` ✅ | ✅ Al día | MIT | 🟢 Bajo | `pnpm list tailwindcss` |
| **swr** | `^2.4.1` | `2.4.1` ✅ | ✅ Al día | MIT | 🟢 Bajo | `pnpm list swr` |

---

## 🔑 Leyenda

### ¿Actualizar?
| Símbolo | Significado |
| :--- | :--- |
| ✅ Al día | Versión actual = última estable. No hay acción requerida. |
| 🔼 Sí | Hay una versión más nueva disponible. Actualización recomendada. |
| ⏸ Esperar | Hay versión más nueva pero implica breaking changes o dependencias cruzadas. Evaluar con calma. |
| 🔒 Fijar | La versión actual es la máxima compatible con el ecosistema actual. No actualizar. |

### Riesgo de Cambio
| Nivel | Criterio |
| :--- | :--- |
| 🔴 Crítico | Un cambio de versión puede romper el sistema o requiere refactorización significativa. |
| 🟡 Medio | Puede requerir ajustes menores en configuración o código existente. |
| 🟢 Bajo | Actualización segura. Normalmente solo correcciones y mejoras de rendimiento. |

---

## ⚠️ Alertas Activas

> **Chainlit (2.11.1):** El equipo original abandonó el proyecto en mayo 2025. Ahora es mantenido por la comunidad. Evaluar alternativas a mediano plazo.

> **React 18 → 19:** React 19 ya es la versión activa de desarrollo. React 18 no recibirá nuevas funcionalidades. Migrar en el siguiente ciclo mayor del proyecto.

> **OpenAI SDK (2.38 → 2.41):** Actualización menor, sin breaking changes conocidos. Recomendado actualizar en el próximo sprint.

> **Plotly (6.7 → 6.8):** Actualización menor de mantenimiento. Recomendado actualizar.

> **TanStack Table v9:** Beta activa con cambios de arquitectura importantes. No migrar aún, esperar estabilización.
