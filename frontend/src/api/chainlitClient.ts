import { ChainlitAPI } from '@chainlit/react-client';

const CHAINLIT_SERVER_URL = "http://localhost:8080";

// Instanciamos el cliente de la API que manejará WebSockets, Autenticación y Streaming.
export const apiClient = new ChainlitAPI(CHAINLIT_SERVER_URL, "webapp");