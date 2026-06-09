import React, { useState, useEffect } from 'react';
import { 
  useChatSession, 
  useChatMessages, 
  useChatInteract,
  useChatData,
  useAuth
} from '@chainlit/react-client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Search, RefreshCw, LogOut, X, Trash2, Mail, Lock, ShieldAlert, Settings, ChevronDown, CheckSquare, Square } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import type { IResultItem } from './components/Sidebar';
import { FilterPanel } from './components/FilterPanel';
import { DatasetCard } from './components/DatasetCard';
import { OsamRenderer } from './components/OsamRenderer';
import { apiClient } from '../api/chainlitClient';
import type { IFilterState } from '../domain/types/chat';

const flattenMessages = (items: any[]): any[] => {
  let flat: any[] = [];
  items.forEach((item) => {
    if (item.type === 'user_message' || item.type === 'assistant_message') {
      flat.push(item);
    }
    if (item.steps && item.steps.length > 0) {
      flat = flat.concat(flattenMessages(item.steps));
    }
  });
  return flat;
};

export default function App() {
  const [inputValue, setInputValue] = useState('');
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const [importedDatasets, setImportedDatasets] = useState<{ title: string; description: string; schema?: string; id_catalogo?: number }[]>([]);
  
  // --- Estado de Filtros Centralizado ---
  const [filters, setFilters] = useState<IFilterState>({
    geography: 'Sede Nacional',
    energyMatrix: {
      Solar: true,
      Eólica: false,
      Hidráulica: false,
      Biomasa: false
    }
  });

  // --- Estado de Autenticación de Demo ---
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const [emailInput, setEmailInput] = useState('');
  const [passwordInput, setPasswordInput] = useState('');

  const { user, isAuthenticated, isReady } = useAuth();
  const { connect, disconnect } = useChatSession();
  const { messages } = useChatMessages();
  const { sendMessage, updateChatSettings, clear } = useChatInteract();
  const { loading, connected } = useChatData();
  
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settings, setSettings] = useState({
    showTable: true,
    showChart: true
  });
  const [tempSettings, setTempSettings] = useState({ showTable: true, showChart: true });

  // Cargar configuraciones de local storage
  useEffect(() => {
    const saved = localStorage.getItem('osam_user_settings');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSettings(parsed);
        setTempSettings(parsed);
      } catch (e) {
        // ignore
      }
    }
  }, []);

  // Controlar click fuera del menú de perfil para cerrarlo
  useEffect(() => {
    if (!showProfileMenu) return;
    const handleOutsideClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('.profile-menu-container')) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener('click', handleOutsideClick);
    return () => document.removeEventListener('click', handleOutsideClick);
  }, [showProfileMenu]);

  // Sincronizar tempSettings cuando se abre el modal
  useEffect(() => {
    if (showSettingsModal) {
      setTempSettings(settings);
    }
  }, [showSettingsModal, settings]);

  const handleSaveSettings = (newSettings: { showTable: boolean; showChart: boolean }) => {
    setSettings(newSettings);
    localStorage.setItem('osam_user_settings', JSON.stringify(newSettings));
  };
  
  const flatMessages = flattenMessages(messages);

  useEffect(() => {
    if (isReady) {
      if (isAuthenticated) {
        const username = user?.display_name || user?.identifier || '';
        if (username.toLowerCase().includes('solar')) {
          // Limpiar sesión obsoleta que tiene "solar" del sprint anterior
          apiClient.logout().then(() => window.location.reload());
        } else {
          connect({ userEnv: {} });
        }
      }
    }
  }, [isReady, isAuthenticated, user]);

  useEffect(() => {
    if (connected) {
      console.log("Synchronizing settings and imported datasets after connect/reconnect:", importedDatasets);
      const activeEnergies = Object.entries(filters.energyMatrix)
          .filter(([_, active]) => active)
          .map(([name]) => name);
      updateChatSettings({
        ubicacion: filters.geography,
        periodo: "Todos",
        categoria: activeEnergies,
        entidad: [],
        datasets_activos: importedDatasets.map(d => ({
          table_name: d.title,
          schema: d.schema || '',
          id_catalogo: d.id_catalogo || 0
        }))
      });
    }
  }, [connected]);

  const handleLogin = async (e?: React.FormEvent, emailVal?: string, passVal?: string) => {
    if (e) e.preventDefault();
    const finalEmail = (emailVal !== undefined ? emailVal : emailInput).trim();
    const finalPass = passVal !== undefined ? passVal : passwordInput;
    
    if (!finalEmail) {
      setLoginError('Por favor ingrese su correo corporativo.');
      return;
    }
    if (!finalPass) {
      setLoginError('Por favor ingrese su contraseña corporativa.');
      return;
    }
    
    setLoginError('');
    setLoginLoading(true);
    try {
      const formData = new FormData();
      formData.append("username", finalEmail);
      formData.append("password", finalPass);
      
      const userRes = await apiClient.passwordAuth(formData);
      if (userRes) {
        window.location.reload();
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setLoginError(err.message || 'Credenciales inválidas o acceso no autorizado.');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleOffice365Login = () => {
    setLoginError('');
    setLoginLoading(true);
    // Simular redirección y autenticación exitosa a través de Office 365 (OIDC)
    setTimeout(() => {
      handleLogin(undefined, 'gerente.energia@osinergmin.gob.pe', 'Osi2026!');
    }, 1200);
  };

  useEffect(() => {
    const logSteps = (steps: any[], space: string) => {
      steps.forEach((s) => {
        console.log(`${space}-> Step:`, { id: s.id, type: s.type, name: s.name, output: s.output, content: s.content });
        if (s.steps && s.steps.length > 0) {
          logSteps(s.steps, space + "  ");
        }
      });
    };

    console.log("React app state update:", { connected, messagesCount: messages.length, loading });
    if (messages.length > 0) {
      console.log("MESSAGES DETAILS:");
      messages.forEach((m, idx) => {
        console.log(`Msg ${idx}:`, {
          id: m.id,
          type: m.type,
          name: m.name,
          output: m.output,
          content: (m as any).content
        });
        if (m.steps && m.steps.length > 0) {
          logSteps(m.steps, "  ");
        }
      });
    }
  }, [connected, messages, loading]);

  const handleSendMessage = (messageOverride?: string) => {
    const textToSend = messageOverride || inputValue;
    console.log("handleSendMessage triggered. Input:", textToSend);
    if (textToSend.trim() === '' || loading) {
      console.log("Message sending blocked: empty or loading state active.");
      return;
    }
    
    console.log("Calling sendMessage with payload:", { output: textToSend });
    sendMessage({ 
        name: 'user', 
        type: 'user_message', 
        output: textToSend, 
        content: textToSend,
        createdAt: new Date().toISOString() 
    } as any, []);
    
    if (!messageOverride) setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  const handleClearChat = () => {
    console.log("handleClearChat triggered");
    try {
      clear();
      disconnect();
      setTimeout(() => {
        connect({ userEnv: {} });
      }, 100);
    } catch (err) {
      console.error("Error clearing chat session:", err);
    }
  };

  const applyFilters = () => {
    const activeEnergies = Object.entries(filters.energyMatrix)
        .filter(([_, active]) => active)
        .map(([name]) => name);
    
    updateChatSettings({
      ubicacion: filters.geography,
      periodo: "Todos",
      categoria: activeEnergies,
      entidad: [],
      datasets_activos: importedDatasets.map(d => ({
        table_name: d.title,
        schema: d.schema || '',
        id_catalogo: d.id_catalogo || 0
      }))
    });
  };

  // Extraer dinámicamente gráficos y tablas generados en los mensajes
  const getGeneratedResults = (): IResultItem[] => {
    const results: IResultItem[] = [];
    flatMessages.forEach((msg) => {
      if (msg.role !== 'assistant') return;

      const content = msg.output || (msg as any).content || '';
      
      // A. Buscar bloques json-chart
      const chartRegex = /```(?:json-chart|json)?\s*(\{[\s\S]*?\})\s*```/g;
      let match;
      while ((match = chartRegex.exec(content)) !== null) {
        try {
          const parsed = JSON.parse(match[1]);
          if (parsed && parsed.tipo && parsed.columna_x && parsed.columna_y && parsed.datos) {
            results.push({
              id: `${msg.id}-chart-${parsed.titulo || 'chart'}`,
              type: 'chart',
              title: parsed.titulo || 'Gráfico de Datos',
              subtitle: `Gráfico de ${parsed.tipo.toUpperCase()}`,
              messageId: msg.id
            });
          }
        } catch (e) {
          // No es un json-chart válido
        }
      }

      // B. Buscar si contiene una tabla markdown
      if (content.includes('|') && content.includes('---')) {
        // Buscar nombres de tablas en mayúsculas en el mensaje para usar de título
        const tableMatch = content.match(/\b[A-Z0-9_]{5,}\b/);
        const tableName = tableMatch ? tableMatch[0] : '';
        const title = tableName ? `Reporte: ${tableName}` : 'Reporte Analítico Tabular';
        
        // Evitar duplicados por mensaje
        const exists = results.some(r => r.messageId === msg.id && r.type === 'table');
        if (!exists) {
          results.push({
            id: `${msg.id}-table`,
            type: 'table',
            title,
            subtitle: 'Tabla Resumen',
            messageId: msg.id
          });
        }
      }

      // C. Buscar bloques json-osam
      const osamRegex = /```(?:json-osam)?\s*(\{[\s\S]*?\})\s*```/g;
      let osamMatch;
      while ((osamMatch = osamRegex.exec(content)) !== null) {
        try {
          const parsed = JSON.parse(osamMatch[1]);
          if (parsed && parsed.report && parsed.report.data) {
            const hasChart = parsed.report.presentation?.chart?.type && parsed.report.presentation.chart.type !== 'none';
            const tableTitle = parsed.report.provenance?.source_tables?.[0] 
              ? `Reporte: ${parsed.report.provenance.source_tables[0]}` 
              : 'Reporte Analítico OSAM';
              
            if (hasChart) {
              results.push({
                id: `${msg.id}-osam-chart`,
                type: 'chart',
                title: `Gráfico: ${tableTitle}`,
                subtitle: `Gráfico de ${parsed.report.presentation.chart.type.toUpperCase()}`,
                messageId: msg.id
              });
            }
            
            results.push({
              id: `${msg.id}-osam-table`,
              type: 'table',
              title: tableTitle,
              subtitle: 'Tabla de Datos',
              messageId: msg.id
            });
          }
        } catch (e) {
          // No es un json-osam válido
        }
      }
    });
    return results;
  };

  // Hacer scroll suave hacia el mensaje que originó el resultado
  const scrollToMessage = (messageId: string) => {
    const element = document.getElementById(`msg-${messageId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Efecto visual de parpadeo de enfoque
      element.classList.add('ring-4', 'ring-osi-blue/20', 'transition-all', 'duration-300');
      setTimeout(() => {
        element.classList.remove('ring-4', 'ring-osi-blue/20');
      }, 1500);
    }
  };

  if (!isReady) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 text-slate-400">
        <RefreshCw className="w-10 h-10 animate-spin text-osi-blue mb-4" />
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Cargando Sistema OpenEnergy...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="h-screen w-screen flex flex-col bg-slate-50 relative overflow-hidden font-sans">
        {/* Franja de Identidad Institucional Osinergmin */}
        <div className="w-full h-6 flex shrink-0 select-none">
          <div className="bg-osi-blue w-[80%]"></div>
          <div className="bg-osi-yellow w-[20%]"></div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center p-6">
          <div className="w-full max-w-md bg-white border border-slate-200 rounded-[2.5rem] p-10 shadow-2xl shadow-slate-200 relative overflow-hidden">
            
            {/* Cabecera del Login */}
            <div className="text-center mb-8">
              <span className="px-4 py-1.5 bg-osi-blue/5 text-osi-blue text-[10px] rounded-full tracking-widest uppercase font-black mb-4 inline-block">
                Portal de Inteligencia de Datos
              </span>
              <h1 className="font-black text-3xl text-slate-800 tracking-tight">OpenEnergy</h1>
              <p className="text-xs text-slate-400 font-semibold mt-2">Ingrese sus credenciales de Osinergmin o cuenta Office 365</p>
            </div>

            {/* Formulario */}
            <form onSubmit={(e) => handleLogin(e)} className="space-y-6">
              
              {/* Campo Correo */}
              <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">Correo Corporativo</label>
                <div className="relative">
                  <input
                    type="email"
                    required
                    value={emailInput}
                    onChange={(e) => setEmailInput(e.target.value)}
                    placeholder="usuario@osinergmin.gob.pe"
                    className="w-full bg-slate-50 border-2 border-transparent focus:border-osi-blue/15 focus:bg-white rounded-2xl pl-12 pr-5 py-4 text-sm font-bold text-slate-700 outline-none transition-all"
                  />
                  <Mail className="absolute left-4.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                </div>
              </div>

              {/* Campo Contraseña */}
              <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block">Contraseña de Red</label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-50 border-2 border-transparent focus:border-osi-blue/15 focus:bg-white rounded-2xl pl-12 pr-5 py-4 text-sm font-bold text-slate-700 outline-none transition-all"
                  />
                  <Lock className="absolute left-4.5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                </div>
              </div>

              {/* Mensaje de Error */}
              {loginError && (
                <div className="bg-red-50 border border-red-100 rounded-2xl p-4 flex items-start gap-3">
                  <ShieldAlert className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                  <p className="text-xs text-red-600 font-bold leading-relaxed">{loginError}</p>
                </div>
              )}

              {/* Botones de Login */}
              <div className="flex flex-col gap-4">
                <button
                  type="submit"
                  disabled={loginLoading}
                  className="w-full bg-slate-900 text-white py-5 rounded-[1.5rem] font-black text-[11px] hover:bg-osi-blue transition-all shadow-xl shadow-slate-200 uppercase tracking-[0.2em] active:scale-95 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loginLoading && !emailInput.includes('gerente.energia') ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Iniciando Sesión...
                    </>
                  ) : (
                    'Iniciar Sesión'
                  )}
                </button>

                <div className="relative flex py-2 items-center">
                  <div className="flex-grow border-t border-slate-100"></div>
                  <span className="flex-shrink mx-4 text-slate-300 text-[10px] font-black uppercase tracking-wider">O</span>
                  <div className="flex-grow border-t border-slate-100"></div>
                </div>

                <button
                  type="button"
                  onClick={handleOffice365Login}
                  disabled={loginLoading}
                  className="w-full bg-white hover:bg-slate-50 text-slate-700 border-2 border-slate-200/80 py-4.5 rounded-[1.5rem] font-black text-[11px] transition-all shadow-sm uppercase tracking-[0.2em] active:scale-95 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loginLoading && emailInput.includes('gerente.energia') ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Conectando a OIDC...
                    </>
                  ) : (
                    <>
                      <svg className="w-4.5 h-4.5 shrink-0" viewBox="0 0 23 23" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="0" y="0" width="10.5" height="10.5" fill="#F25022"/>
                        <rect x="11.5" y="0" width="10.5" height="10.5" fill="#7FBA00"/>
                        <rect x="0" y="11.5" width="10.5" height="10.5" fill="#00A4EF"/>
                        <rect x="11.5" y="11.5" width="10.5" height="10.5" fill="#FFB900"/>
                      </svg>
                      <span>Ingresar con Office 365</span>
                    </>
                  )}
                </button>
              </div>
            </form>

          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-50 text-slate-800 font-sans text-[15px]">
      {/* Franja de Identidad Institucional Osinergmin (Manual de Identidad Pág 55) */}
      <div className="w-full h-6 flex shrink-0 select-none">
        <div className="bg-osi-blue w-[80%]"></div>
        <div className="bg-osi-yellow w-[20%]"></div>
      </div>

      <div className="flex-1 flex overflow-hidden w-full h-[calc(100vh-24px)]">
        <Sidebar 
          connected={connected || false} 
          importedDatasets={importedDatasets} 
          results={getGeneratedResults()}
          onResultClick={scrollToMessage}
        />

      {/* Panel Central de Chat */}
      <main className="flex-1 flex flex-col h-full bg-slate-100 p-4 min-w-0">
        <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-slate-200 border border-slate-100 flex-1 flex flex-col overflow-hidden relative">
          <header className="p-6 px-8 border-b border-slate-50 bg-white/50 backdrop-blur-2xl shrink-0 flex items-center justify-between">
            <h2 className="font-black text-2xl text-slate-800 tracking-tight flex items-center gap-3">
              Refinar Resultados Asistido <span className="px-3 py-1 bg-slate-900 text-white text-[10px] rounded-full tracking-widest uppercase font-black">RF-07</span>
            </h2>
            <div className="relative flex items-center gap-3 profile-menu-container">
              <button
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="flex items-center gap-3 px-4 py-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200/60 rounded-2xl cursor-pointer select-none transition-all duration-200 group active:scale-95 shadow-sm"
              >
                <div className="w-8 h-8 rounded-full bg-osi-blue/10 flex items-center justify-center text-osi-blue font-black text-sm uppercase">
                  {user?.display_name ? user.display_name.charAt(0) : 'U'}
                </div>
                
                <div className="flex flex-col text-left min-w-[80px]">
                  <span className="text-xs font-black text-slate-800 tracking-tight leading-none">
                    {user?.display_name || user?.identifier || 'Usuario'}
                  </span>
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">
                    {user?.metadata?.rol || 'Analista'}
                  </span>
                </div>
                
                <ChevronDown className="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
              </button>

              {/* Menú Emergente de Perfil */}
              {showProfileMenu && (
                <div className="absolute right-0 top-14 w-64 bg-white/95 backdrop-blur-2xl rounded-2xl border border-slate-100 shadow-2xl shadow-slate-300/60 p-2 z-50 animate-in fade-in slide-in-from-top-4 duration-200 flex flex-col">
                  {/* Info Perfil */}
                  <div className="px-4 py-3 flex flex-col gap-0.5 border-b border-slate-50">
                    <span className="text-xs font-black text-slate-800 uppercase tracking-wide">
                      {user?.display_name || 'Institucional'}
                    </span>
                    <span className="text-[10px] text-slate-400 font-bold truncate">
                      {user?.identifier || 'gerente.energia@osinergmin.gob.pe'}
                    </span>
                    {user?.metadata?.rol && (
                      <span className="mt-1 self-start px-2 py-0.5 bg-osi-blue/10 text-osi-blue text-[8px] font-black rounded-md uppercase tracking-wider">
                        {user.metadata.rol}
                      </span>
                    )}
                  </div>
                  
                  {/* Opciones */}
                  <div className="py-1 flex flex-col gap-0.5">
                    <button
                      onClick={() => {
                        setShowSettingsModal(true);
                        setShowProfileMenu(false);
                      }}
                      className="flex items-center gap-3 px-4 py-2.5 text-xs font-black uppercase tracking-wider text-slate-600 hover:text-slate-800 hover:bg-slate-50 rounded-xl transition-all cursor-pointer text-left"
                    >
                      <Settings className="w-4 h-4 text-slate-400 shrink-0" />
                      Configuraciones
                    </button>
                    
                    <button
                      onClick={() => {
                        handleClearChat();
                        setShowProfileMenu(false);
                      }}
                      className="flex items-center gap-3 px-4 py-2.5 text-xs font-black uppercase tracking-wider text-slate-600 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all cursor-pointer text-left"
                    >
                      <Trash2 className="w-4 h-4 text-slate-400 shrink-0" />
                      Limpiar Conversación
                    </button>
                  </div>
                  
                  <div className="border-t border-slate-50 mt-1 pt-1">
                    <button
                      onClick={() => {
                        apiClient.logout().then(() => window.location.reload());
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-xs font-black uppercase tracking-wider text-red-600 hover:text-red-700 hover:bg-red-50/50 rounded-xl transition-all cursor-pointer text-left"
                    >
                      <LogOut className="w-4 h-4 text-red-500 shrink-0" />
                      Cerrar Sesión
                    </button>
                  </div>
                </div>
              )}
            </div>
          </header>
          
          <div className="flex-1 overflow-y-auto p-8 space-y-10 scroll-smooth bg-gradient-to-b from-white to-slate-50/30">
            {flatMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-300 space-y-6">
                    <div className="w-24 h-24 rounded-[2.5rem] bg-slate-50 flex items-center justify-center border-2 border-slate-100/50 shadow-inner">
                      <Search className="w-10 h-10 opacity-10" />
                    </div>
                    <div className="text-center">
                        <p className="text-sm font-black uppercase tracking-[0.2em] text-slate-400 mb-1">Terminal de Inteligencia</p>
                        <p className="text-xs font-bold italic opacity-40">Listo para procesar consultas del catálogo nacional...</p>
                    </div>
                </div>
            ) : (
                flatMessages.map((message) => {
                    const isUser = message.type === 'user_message';
                    const messageText = message.output || (message as any).content || '';
                    return (
                        <div id={`msg-${message.id}`} key={message.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-in slide-in-from-bottom-4 duration-500 rounded-3xl p-1`}>
                            <div className={`max-w-[85%] lg:max-w-[70%] p-6 rounded-[2rem] shadow-xl border ${
                                isUser 
                                    ? 'bg-osi-blue text-white border-osi-blue-dark rounded-tr-none' 
                                    : 'bg-white border-slate-200 text-slate-700 rounded-tl-none shadow-slate-100'
                            }`}>
                                <span className={`block text-[10px] uppercase font-black mb-3 tracking-widest opacity-40 ${isUser ? 'text-white' : 'text-osi-blue'}`}>
                                    {isUser ? 'Consulta Ejecutiva' : '🤖 Copiloto OpenEnergy'}
                                </span>
                                
                                <div className={`prose prose-sm max-w-none ${isUser ? 'prose-invert text-white' : 'text-slate-700'} font-medium leading-relaxed`}>
                                  <ReactMarkdown 
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                      table: ({node, ...props}) => (
                                        <div className="overflow-x-auto my-6 rounded-2xl border-2 border-slate-100 shadow-xl bg-white">
                                          <table className="min-w-full divide-y divide-slate-100" {...props} />
                                        </div>
                                      ),
                                      thead: ({node, ...props}) => <thead className="bg-slate-50/50" {...props} />,
                                      th: ({node, ...props}) => <th className="px-5 py-4 text-left text-[10px] font-black uppercase text-osi-blue tracking-widest" {...props} />,
                                      td: ({node, ...props}) => <td className="px-5 py-4 text-[13px] border-t border-slate-50 font-semibold" {...props} />,
                                      strong: ({node, ...props}) => <strong className="font-black" {...props} />,
                                      pre: ({node, children, ...props}) => {
                                        const isCustomBlock = React.Children.toArray(children).some((child: any) => {
                                          return child && child.props && (
                                            child.props.className?.includes('language-json-osam') ||
                                            child.props.className?.includes('language-json-datasets') ||
                                            child.props.className?.includes('language-json-chart')
                                          );
                                        });

                                        if (isCustomBlock) {
                                          return <div className="w-full my-6">{children}</div>;
                                        }
                                        return <pre className="overflow-x-auto my-6 rounded-2xl bg-slate-950 text-slate-100 p-6 font-mono text-xs leading-relaxed" {...props}>{children}</pre>;
                                      },
                                      img: ({node, ...props}) => (
                                        <img 
                                          {...props} 
                                          className="rounded-3xl max-w-full h-auto cursor-zoom-in transition-transform duration-300 hover:scale-[1.01] hover:shadow-2xl shadow-md border border-slate-200/50 my-6 animate-in fade-in zoom-in-95 duration-500"
                                          onClick={() => setLightboxImage(props.src || null)}
                                        />
                                      ),
                                      code: ({node, className, children, ...props}) => {
                                        const match = /language-(\w+)/.exec(className || '');
                                        const lang = match ? match[1] : '';
                                        const codeContent = String(children).trim();
                                        
                                        // 0. Intentar renderizar como Payload OSAM v1 Gobernado
                                        if (lang === 'json-osam' || lang === 'json' || lang === '') {
                                          try {
                                            if (codeContent.startsWith('{')) {
                                              const parsed = JSON.parse(codeContent);
                                              if (parsed && (parsed.report || parsed.analysis)) {
                                                return <OsamRenderer payload={parsed} settings={settings} />;
                                              }
                                            }
                                          } catch (err) {
                                            // No es un JSON OSAM
                                          }
                                        }

                                        // 2. Intentar renderizar como Catálogo de Datasets si cumple con la estructura
                                        if (lang === 'json-datasets' || lang === 'json' || lang === '') {
                                          try {
                                            if (codeContent.startsWith('[')) {
                                              const parsed = JSON.parse(codeContent);
                                              if (Array.isArray(parsed) && parsed.length > 0 && (parsed[0].table_name || parsed[0].title)) {
                                                return (
                                                  <div className="my-6 w-full animate-in fade-in slide-in-from-left-4 duration-500">
                                                    <div className="flex gap-5 overflow-x-auto pb-6 px-1 no-scrollbar">
                                                      {parsed.map((ds: any, i: number) => (
                                                        <DatasetCard 
                                                          key={i}
                                                          title={ds.title || ds.table_name || 'Dataset'} 
                                                          description={ds.description || ds.desc || 'Sin descripción'}
                                                          format={ds.format || 'SQL Table'} 
                                                          license={ds.license || 'Osinergmin'} 
                                                          organization={ds.organization || 'Gobernanza de Datos'}
                                                          schema={ds.schema}
                                                          id_catalogo={ds.id_catalogo}
                                                          onImport={(title, description, schema, id_catalogo) => {
                                                            setImportedDatasets((prev) => {
                                                              const next = prev.some(d => d.title === title) 
                                                                ? prev 
                                                                : [...prev, { title, description, schema, id_catalogo }];
                                                              
                                                              // Sincronizar los datasets activos con el backend de Chainlit
                                                              const activeEnergies = Object.entries(filters.energyMatrix)
                                                                  .filter(([_, active]) => active)
                                                                  .map(([name]) => name);
                                                              updateChatSettings({
                                                                ubicacion: filters.geography,
                                                                periodo: "Todos",
                                                                categoria: activeEnergies,
                                                                entidad: [],
                                                                datasets_activos: next.map(d => ({
                                                                  table_name: d.title,
                                                                  schema: d.schema || '',
                                                                  id_catalogo: d.id_catalogo || 0
                                                                }))
                                                              });
                                                              
                                                              return next;
                                                            });
                                                          }}
                                                        />
                                                      ))}
                                                    </div>
                                                  </div>
                                                );
                                              }
                                            }
                                          } catch (err) {
                                            // No es un JSON de datasets
                                          }
                                        }
                                        
                                        return <code className={className} {...props}>{children}</code>;
                                      }
                                    }}
                                  >
                                    {messageText}
                                  </ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    );
                })
            )}
            {loading && (
                <div className="flex justify-start animate-in fade-in duration-300">
                    <div className="bg-white border border-slate-100 px-6 py-4 rounded-[1.5rem] rounded-tl-none shadow-xl shadow-slate-100 flex items-center gap-4">
                        <div className="flex gap-2">
                            <span className="w-2.5 h-2.5 bg-osi-blue rounded-full animate-bounce"></span>
                            <span className="w-2.5 h-2.5 bg-osi-blue rounded-full animate-bounce [animation-delay:0.2s]"></span>
                            <span className="w-2.5 h-2.5 bg-osi-blue rounded-full animate-bounce [animation-delay:0.4s]"></span>
                        </div>
                        <span className="text-[11px] font-black uppercase text-osi-blue tracking-widest opacity-50">Sincronizando</span>
                    </div>
                </div>
            )}
          </div>

          <div className="p-8 bg-white border-t border-slate-50 shrink-0">
            <div className="relative group max-w-5xl mx-auto">
              <input 
                type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyDown={handleKeyDown}
                placeholder="Solicite análisis, tablas o reportes..." 
                className="w-full border-2 border-slate-100 bg-slate-50/50 rounded-[2rem] pl-8 pr-48 py-6 focus:outline-none focus:border-osi-blue/10 focus:bg-white focus:ring-12 focus:ring-osi-blue/5 transition-all font-bold text-slate-700 shadow-inner" 
              />
              <button 
                  onClick={() => handleSendMessage()}
                  disabled={inputValue.trim() === '' || loading}
                  className="absolute right-3 top-3 bottom-3 bg-osi-blue text-white px-10 rounded-[1.5rem] font-black text-xs hover:bg-osi-blue-dark active:scale-95 transition-all disabled:bg-slate-100 disabled:text-slate-300 shadow-2xl shadow-osi-blue/30 cursor-pointer uppercase tracking-[0.1em]"
              >
                {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : 'Analizar'}
              </button>
            </div>
          </div>
        </div>
      </main>

      <FilterPanel 
        filters={filters}
        loading={loading}
        onGeographyChange={(val) => setFilters(f => ({ ...f, geography: val }))}
        onEnergyToggle={(key) => setFilters(f => ({ ...f, energyMatrix: { ...f.energyMatrix, [key]: !f.energyMatrix[key] } }))}
        onApply={applyFilters}
      />

      {/* Lightbox para imágenes en markdown */}
      {lightboxImage && (
        <div 
          onClick={() => setLightboxImage(null)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/90 backdrop-blur-md p-6 select-none animate-in fade-in duration-200 cursor-zoom-out"
        >
          <button 
            onClick={() => setLightboxImage(null)}
            className="absolute top-6 right-6 p-4 bg-white/10 hover:bg-white/20 hover:scale-105 active:scale-95 text-white rounded-2xl cursor-pointer transition-all duration-300 z-10"
            title="Cerrar Imagen"
          >
            <X className="w-6 h-6" />
          </button>
          <div 
            onClick={(e) => e.stopPropagation()}
            className="relative max-w-5xl max-h-[85vh] overflow-hidden rounded-[2.5rem] bg-white p-3 shadow-2xl border border-white/15 animate-in zoom-in-95 duration-200"
          >
            <img 
              src={lightboxImage} 
              alt="Visualización ampliada" 
              className="w-full h-auto max-h-[80vh] object-contain rounded-[2rem]"
            />
          </div>
        </div>
      )}

      {/* Modal de Configuraciones */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-[2.5rem] shadow-2xl border border-slate-100 max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col">
            {/* Header */}
            <div className="p-6 px-8 border-b border-slate-50 flex items-center justify-between bg-slate-50/30">
              <div className="flex items-center gap-3">
                <Settings className="w-5 h-5 text-osi-blue" />
                <h3 className="font-black text-lg text-slate-800 uppercase tracking-wider">Configuraciones del Sistema</h3>
              </div>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="p-2 hover:bg-slate-100 rounded-full text-slate-400 hover:text-slate-600 transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Body */}
            <div className="p-8 space-y-6">
              <div className="space-y-4">
                <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 border-b border-slate-100 pb-2">
                  Entregables Analíticos
                </h4>
                <p className="text-xs font-semibold text-slate-500 leading-relaxed">
                  Defina qué tipo de componentes visuales se generarán y mostrarán en la pantalla de análisis de datos.
                </p>
                
                <div className="space-y-3.5 pt-2">
                  {/* Checkbox Tabla */}
                  <label className="flex items-start gap-3.5 p-4 bg-slate-50 hover:bg-slate-100/70 border border-slate-200/50 rounded-[1.25rem] cursor-pointer select-none transition-all duration-200 group">
                    <input
                      type="checkbox"
                      checked={tempSettings.showTable}
                      onChange={() => setTempSettings(prev => ({ ...prev, showTable: !prev.showTable }))}
                      className="hidden"
                    />
                    <div className="mt-0.5">
                      {tempSettings.showTable ? (
                        <CheckSquare className="w-5 h-5 text-osi-blue fill-osi-blue/5 shrink-0" />
                      ) : (
                        <Square className="w-5 h-5 text-slate-300 shrink-0 group-hover:text-slate-400" />
                      )}
                    </div>
                    <div>
                      <span className={`block text-xs font-black uppercase tracking-wide ${tempSettings.showTable ? 'text-slate-800' : 'text-slate-600'}`}>
                        Habilitar Tablas de Datos
                      </span>
                      <span className="block text-[11px] font-semibold text-slate-400 mt-1 leading-normal">
                        Permite renderizar y explorar reportes de datos estructurados, con opción de exportación a CSV.
                      </span>
                    </div>
                  </label>
                  
                  {/* Checkbox Gráfico */}
                  <label className="flex items-start gap-3.5 p-4 bg-slate-50 hover:bg-slate-100/70 border border-slate-200/50 rounded-[1.25rem] cursor-pointer select-none transition-all duration-200 group">
                    <input
                      type="checkbox"
                      checked={tempSettings.showChart}
                      onChange={() => setTempSettings(prev => ({ ...prev, showChart: !prev.showChart }))}
                      className="hidden"
                    />
                    <div className="mt-0.5">
                      {tempSettings.showChart ? (
                        <CheckSquare className="w-5 h-5 text-osi-blue fill-osi-blue/5 shrink-0" />
                      ) : (
                        <Square className="w-5 h-5 text-slate-300 shrink-0 group-hover:text-slate-400" />
                      )}
                    </div>
                    <div>
                      <span className={`block text-xs font-black uppercase tracking-wide ${tempSettings.showChart ? 'text-slate-800' : 'text-slate-600'}`}>
                        Habilitar Gráficos Analíticos
                      </span>
                      <span className="block text-[11px] font-semibold text-slate-400 mt-1 leading-normal">
                        Permite visualizar tendencias, curvas y distribuciones mediante gráficos interactivos (Vega-Lite).
                      </span>
                    </div>
                  </label>
                </div>
                
                {/* Validación error */}
                {!tempSettings.showTable && !tempSettings.showChart && (
                  <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-rose-700 text-xs font-bold leading-normal animate-in slide-in-from-top-1">
                    ⚠️ Debe mantener habilitado al menos un tipo de entregable (Tabla o Gráfico) para poder visualizar resultados.
                  </div>
                )}
              </div>
            </div>
            
            {/* Footer */}
            <div className="p-6 px-8 border-t border-slate-50 bg-slate-50/20 flex justify-end gap-3 shrink-0">
              <button
                onClick={() => setShowSettingsModal(false)}
                className="px-5 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-black uppercase tracking-wider rounded-xl transition-all cursor-pointer shadow-sm"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  handleSaveSettings(tempSettings);
                  setShowSettingsModal(false);
                }}
                disabled={!tempSettings.showTable && !tempSettings.showChart}
                className="px-6 py-2.5 bg-osi-blue hover:bg-osi-blue-dark disabled:opacity-50 disabled:pointer-events-none text-white text-xs font-black uppercase tracking-wider rounded-xl shadow-lg shadow-osi-blue/25 transition-all cursor-pointer active:scale-95"
              >
                Guardar Cambios
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}