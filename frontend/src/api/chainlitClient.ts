import { ChainlitAPI } from '@chainlit/react-client';

// Si estamos en desarrollo con Vite (puerto 5173), apuntamos al backend en el puerto 8000.
// Si estamos en producción/intranet (servido por Chainlit), usamos el origen dinámico de la página.
const isDev = window.location.port === "5173";
const CHAINLIT_SERVER_URL = isDev
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : window.location.origin;

// Instanciamos el cliente de la API que manejará WebSockets, Autenticación y Streaming.
export const apiClient = new ChainlitAPI(CHAINLIT_SERVER_URL, "webapp");