import { FileText, Table as TableIcon } from 'lucide-react';

interface IDatasetItem {
  title: string;
  description: string;
}

interface SidebarProps {
  connected: boolean;
  importedDatasets: IDatasetItem[];
}

export const Sidebar = ({ connected, importedDatasets }: SidebarProps) => {
  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-full shrink-0 shadow-sm z-20">
      <div className="p-6 border-b border-slate-100 flex items-center justify-between">
        <span className="font-black text-xl tracking-tighter text-osi-blue">OsiData <span className="text-slate-200 font-light">|</span> v2</span>
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 animate-pulse'}`}></span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-8">
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

        <section>
          <h3 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-4">Resultados</h3>
          <div className="space-y-3">
            {importedDatasets.length > 0 ? (
              <div className="bg-slate-50 border border-slate-200 p-3 rounded-2xl flex items-center gap-3 cursor-pointer hover:border-osi-blue/30 transition-all group animate-in fade-in duration-300">
                <div className="w-10 h-10 rounded-xl bg-white border border-slate-100 flex items-center justify-center">
                    <TableIcon className="w-5 h-5 text-osi-blue group-hover:scale-110 transition-transform" />
                </div>
                <div>
                    <span className="block text-[11px] font-black text-slate-800">Tabla Resumen Q3</span>
                    <span className="block text-[9px] text-slate-400 font-bold uppercase">Reporte Activo</span>
                </div>
              </div>
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
