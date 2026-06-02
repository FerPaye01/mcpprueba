import { useState, useEffect } from 'react';
import { 
  useChatSession, 
  useChatMessages, 
  useChatInteract,
  useChatData,
  useAuth
} from '@chainlit/react-client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Search, RefreshCw, LogOut, CheckCircle2 } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { FilterPanel } from './components/FilterPanel';
import { DatasetCard } from './components/DatasetCard';
import { InteractiveChart } from './components/InteractiveChart';
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

  const { user, isAuthenticated, isReady } = useAuth();
  const { connect } = useChatSession();
  const { messages } = useChatMessages();
  const { sendMessage, updateChatSettings } = useChatInteract();
  const { loading, connected } = useChatData();
  
  const flatMessages = flattenMessages(messages);

  useEffect(() => {
    if (isReady && !isAuthenticated && !loginLoading) {
      // Auto-generar un analista aleatorio de Osinergmin e iniciar sesión al instante
      const prefixes = ['Analista', 'Consultor', 'Fiscalizador', 'Supervisor', 'Coordinador', 'Especialista', 'Auditor'];
      const randomNum = Math.floor(Math.random() * 900) + 100;
      const randomName = `${prefixes[Math.floor(Math.random() * prefixes.length)]} ${randomNum}`;
      
      handleLogin(undefined, randomName);
    } else if (isAuthenticated) {
      connect({ userEnv: {} });
    }
  }, [isReady, isAuthenticated, loginLoading]);

  const handleLogin = async (e?: React.FormEvent, nameOverride?: string) => {
    if (e) e.preventDefault();
    const finalName = (nameOverride || '').trim();
    if (!finalName) {
      setLoginError('Por favor ingrese un nombre para iniciar.');
      return;
    }
    setLoginError('');
    setLoginLoading(true);
    try {
      const formData = new FormData();
      formData.append("username", finalName);
      formData.append("password", "temp2026");
      
      const userRes = await apiClient.passwordAuth(formData);
      if (userRes) {
        window.location.reload();
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setLoginError(err.message || 'Error al iniciar la sesión temporal.');
    } finally {
      setLoginLoading(false);
    }
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

  const applyFilters = () => {
    const activeEnergies = Object.entries(filters.energyMatrix)
        .filter(([_, active]) => active)
        .map(([name]) => name);
    
    // Sincronizar los filtros seleccionados con el backend de Chainlit
    updateChatSettings({
      ubicacion: filters.geography,
      periodo: "Todos",
      categoria: activeEnergies,
      entidad: []
    });
  };

  if (!isReady) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 text-slate-400">
        <RefreshCw className="w-10 h-10 animate-spin text-osi-blue mb-4" />
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">Cargando Sistema OsiData...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-slate-50 text-slate-400">
        <RefreshCw className="w-10 h-10 animate-spin text-osi-blue mb-4" />
        <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500 mb-1">
          {loginError ? 'Error al Iniciar' : 'Asignando Identidad de Analista...'}
        </p>
        {loginError ? (
          <p className="text-xs text-red-500 font-bold max-w-sm text-center px-4 leading-relaxed">
            ⚠️ {loginError}. Intente recargar la página.
          </p>
        ) : (
          <p className="text-[11px] font-semibold text-slate-400/60 italic">
            Creando sesión temporal única para evitar colisión de datos.
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-slate-50 text-slate-800 font-sans text-[15px]">
      <Sidebar connected={connected || false} />

      {/* Panel Central de Chat */}
      <main className="flex-1 flex flex-col h-full bg-slate-100 p-4 min-w-0">
        <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-slate-200 border border-slate-100 flex-1 flex flex-col overflow-hidden relative">
          <header className="p-6 px-8 border-b border-slate-50 bg-white/50 backdrop-blur-2xl shrink-0 flex items-center justify-between">
            <h2 className="font-black text-2xl text-slate-800 tracking-tight flex items-center gap-3">
              Refinar Resultados Asistido <span className="px-3 py-1 bg-slate-900 text-white text-[10px] rounded-full tracking-widest uppercase font-black">RF-07</span>
            </h2>
            <div className="flex items-center gap-4">
              <span className="text-xs font-black uppercase text-osi-blue tracking-wider bg-osi-blue/5 px-4 py-2 rounded-xl flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-osi-blue" />
                {user?.display_name || user?.identifier || 'Institucional'}
              </span>
              <button 
                onClick={() => apiClient.logout().then(() => window.location.reload())}
                className="p-2.5 bg-slate-50 hover:bg-red-50 hover:text-red-500 text-slate-400 rounded-xl transition-all cursor-pointer hover:scale-105"
                title="Cerrar Sesión"
              >
                <LogOut className="w-4 h-4" />
              </button>
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
                        <div key={message.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} animate-in slide-in-from-bottom-4 duration-500`}>
                            <div className={`max-w-[85%] lg:max-w-[70%] p-6 rounded-[2rem] shadow-xl border ${
                                isUser 
                                    ? 'bg-osi-blue text-white border-osi-blue-dark rounded-tr-none' 
                                    : 'bg-white border-slate-200 text-slate-700 rounded-tl-none shadow-slate-100'
                            }`}>
                                <span className={`block text-[10px] uppercase font-black mb-3 tracking-widest opacity-40 ${isUser ? 'text-white' : 'text-osi-blue'}`}>
                                    {isUser ? 'Consulta Ejecutiva' : '🤖 Copiloto OsiData'}
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
                                      code: ({node, className, children, ...props}) => {
                                        const match = /language-(\w+)/.exec(className || '');
                                        if (match && match[1] === 'json-chart') {
                                          try {
                                            const chartData = JSON.parse(String(children));
                                            return <InteractiveChart data={chartData} />;
                                          } catch (err) {
                                            console.error("Error parsing json-chart:", err);
                                            return (
                                              <pre className="bg-slate-50 p-4 rounded-2xl text-xs overflow-x-auto border border-slate-100">
                                                <code>{children}</code>
                                              </pre>
                                            );
                                          }
                                        }
                                        if (match && match[1] === 'json-datasets') {
                                          try {
                                            const datasets = JSON.parse(String(children));
                                            return (
                                              <div className="my-6 w-full animate-in fade-in slide-in-from-left-4 duration-500">
                                                <div className="flex gap-5 overflow-x-auto pb-6 px-1 no-scrollbar">
                                                  {datasets.map((ds: any, i: number) => (
                                                    <DatasetCard 
                                                      key={i}
                                                      title={ds.title || ds.table_name || 'Dataset'} 
                                                      description={ds.description || ds.desc || 'Sin descripción'}
                                                      format={ds.format || 'SQL Table'} 
                                                      license={ds.license || 'Osinergmin'} 
                                                      organization={ds.organization || 'Gobernanza de Datos'}
                                                    />
                                                  ))}
                                                </div>
                                              </div>
                                            );
                                          } catch (err) {
                                            console.error("Error parsing json-datasets:", err);
                                            return (
                                              <pre className="bg-slate-50 p-4 rounded-2xl text-xs overflow-x-auto border border-slate-100">
                                                <code>{children}</code>
                                              </pre>
                                            );
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
    </div>
  );
}