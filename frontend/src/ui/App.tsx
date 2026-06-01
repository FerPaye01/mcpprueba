import { useState, useEffect } from 'react';
import { 
  useChatSession, 
  useChatMessages, 
  useChatInteract,
  useChatData
} from '@chainlit/react-client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Search, RefreshCw } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { FilterPanel } from './components/FilterPanel';
import { DatasetCard } from './components/DatasetCard';
import { IFilterState } from '../domain/types/chat';

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

  const { connect, connected } = useChatSession();
  const { messages } = useChatMessages();
  const { sendMessage } = useChatInteract();
  const { loading } = useChatData();

  useEffect(() => {
    connect({ userEnv: {} });
  }, [connect]);

  const handleSendMessage = (messageOverride?: string) => {
    const textToSend = messageOverride || inputValue;
    if (textToSend.trim() === '' || loading) return;
    
    sendMessage({ 
        name: 'user', 
        type: 'user_message', 
        output: textToSend, 
        createdAt: new Date().toISOString() 
    }, []);
    
    if (!messageOverride) setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSendMessage();
  };

  const applyFilters = () => {
    const activeEnergies = Object.entries(filters.energyMatrix)
        .filter(([_, active]) => active)
        .map(([name]) => name)
        .join(', ');
    
    const filterCommand = `Actualizar filtros de análisis: \n- Geografía: ${filters.geography}\n- Matriz Energética: ${activeEnergies || 'Ninguna'}`;
    handleSendMessage(filterCommand);
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-slate-50 text-slate-800 font-sans text-[15px]">
      <Sidebar connected={connected} />

      {/* Panel Central de Chat */}
      <main className="flex-1 flex flex-col h-full bg-slate-100 p-4 min-w-0">
        <div className="bg-white rounded-[2.5rem] shadow-2xl shadow-slate-200 border border-slate-100 flex-1 flex flex-col overflow-hidden relative">
          <header className="p-6 px-8 border-b border-slate-50 bg-white/50 backdrop-blur-2xl shrink-0 flex items-center justify-between">
            <h2 className="font-black text-2xl text-slate-800 tracking-tight flex items-center gap-3">
              Refinar Resultados Asistido <span className="px-3 py-1 bg-slate-900 text-white text-[10px] rounded-full tracking-widest uppercase font-black">RF-07</span>
            </h2>
          </header>
          
          <div className="flex-1 overflow-y-auto p-8 space-y-10 scroll-smooth bg-gradient-to-b from-white to-slate-50/30">
            {messages.length === 0 ? (
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
                messages.map((message) => {
                    const isUser = message.type === 'user_message';
                    const hasDatasets = !isUser && message.output.toLowerCase().includes("conjuntos de datos") && message.output.toLowerCase().includes("encontrados");

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
                                      strong: ({node, ...props}) => <strong className="font-black" {...props} />
                                    }}
                                  >
                                    {message.output}
                                  </ReactMarkdown>
                                </div>
                            </div>

                            {hasDatasets && (
                              <div className="mt-6 w-full animate-in fade-in slide-in-from-left-4 duration-700 delay-300">
                                <div className="flex gap-5 overflow-x-auto pb-6 px-2 no-scrollbar">
                                  <DatasetCard 
                                    title="Generación Solar Q1 2024" 
                                    description="Detalle de la generación de energía renovable (fotovoltaica) en el primer trimestre de 2024."
                                    format="CSV, JSON" license="Open Data" organization="MINEM"
                                  />
                                  <DatasetCard 
                                    title="Estadísticas Hidroeléctricas" 
                                    description="Reporte consolidado de producción hidroeléctrica por cuenca y departamento durante 2023."
                                    format="CSV" license="Osinergmin" organization="OSINERGMIN"
                                  />
                                </div>
                              </div>
                            )}
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