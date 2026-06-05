import { FileText, Table as TableIcon } from 'lucide-react';

export interface IResultItem {
  id: string;
  type: 'chart' | 'table';
  title: string;
  subtitle: string;
  messageId: string;
}

interface IDatasetItem {
  title: string;
  description: string;
}

interface SidebarProps {
  connected: boolean;
  importedDatasets: IDatasetItem[];
  results: IResultItem[];
  onResultClick: (messageId: string) => void;
}

export const Sidebar = ({ connected, importedDatasets, results, onResultClick }: SidebarProps) => {
  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-full shrink-0 shadow-sm z-20">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-100 flex items-center justify-between">
        <span className="font-black text-xl tracking-tighter text-osi-blue">OpenEnergy</span>
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 animate-pulse'}`}></span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-8">
        
        {/* Datasets Activos Section */}
        <section>
          <h3 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Datasets Activos</h3>
          <div className="space-y-1">
            {importedDatasets.length === 0 ? (
              <div className="p-4 border-2 border-dashed border-slate-100 rounded-2xl text-center text-xs text-slate-400 font-semibold italic">
                Sin datasets activos. Muestre e importe tablas en el chat.
              </div>
            ) : (
              importedDatasets.map(ds => (
                <div key={ds.title} className="group flex items-center gap-3 p-3 rounded-2xl hover:bg-slate-50 cursor-pointer transition-all border border-transparent hover:border-slate-100 animate-in fade-in slide-in-from-top-1 duration-300">
                  <div className="w-9 h-9 rounded-xl bg-green-50 flex items-center justify-center group-hover:bg-green-100 shrink-0">
                    <FileText className="w-4 h-4 text-green-600" />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-bold text-slate-700 truncate" title={ds.title}>{ds.title}</span>
                    <span className="text-[10px] text-slate-400 truncate leading-tight font-semibold" title={ds.description}>{ds.description}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        {/* Resultados (Charts/Tables Generados) Section */}
        <section>
          <h3 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Resultados</h3>
          <div className="space-y-3">
            {results.length > 0 ? (
              results.map(r => (
                <div 
                  key={r.id}
                  onClick={() => onResultClick(r.messageId)}
                  className="bg-slate-50 border border-slate-200 p-3 rounded-2xl flex items-center gap-3 cursor-pointer hover:border-osi-blue/30 hover:bg-slate-100/50 transition-all group animate-in fade-in duration-300"
                  title="Hacer scroll hacia este resultado"
                >
                  <div className="w-10 h-10 rounded-xl bg-white border border-slate-100 flex items-center justify-center shrink-0 shadow-sm">
                    <TableIcon className="w-5 h-5 text-osi-blue group-hover:scale-110 transition-transform" />
                  </div>
                  <div className="min-w-0">
                    <span className="block text-[11px] font-black text-slate-800 truncate" title={r.title}>{r.title}</span>
                    <span className="block text-[9px] text-slate-400 font-bold uppercase">{r.subtitle}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-4 border-2 border-dashed border-slate-100 rounded-2xl text-center text-xs text-slate-400 font-semibold italic">
                Sin reportes generados.
              </div>
            )}
          </div>
        </section>

      </div>
    </aside>
  );
};
