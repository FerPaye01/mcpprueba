import { Lock, Filter } from 'lucide-react';
import type { IFilterState } from '../../domain/types/chat';

interface FilterPanelProps {
  filters: IFilterState;
  loading: boolean;
  onGeographyChange: (val: string) => void;
  onEnergyToggle: (key: string) => void;
  onApply: () => void;
}

export const FilterPanel = ({ filters, loading, onGeographyChange, onEnergyToggle, onApply }: FilterPanelProps) => {
  return (
    <aside className="w-80 bg-slate-50 border-l border-slate-200 flex flex-col h-full shrink-0 p-6 space-y-6">
      <div className="bg-white border border-slate-200 rounded-[2.5rem] p-6 shadow-sm">
        <h3 className="font-black text-xs text-osi-blue mb-4 flex items-center gap-2 uppercase tracking-widest">
          <Lock className="w-4 h-4" /> Gobernanza OsiData
        </h3>
        <div className="space-y-4">
          <div className="bg-green-50/50 border border-green-100 p-4 rounded-2xl">
            <span className="text-[11px] font-black text-green-700 block mb-1 uppercase tracking-tighter">✓ Estatus: Operación Segura</span>
            <p className="text-[10px] text-green-600/70 font-bold leading-relaxed">Conexión Oracle Cifrada y auditoría activa [RF-15].</p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-[2.5rem] p-7 shadow-2xl shadow-slate-200 flex-1 flex flex-col overflow-hidden">
        <h3 className="font-black text-xs text-slate-400 mb-8 flex items-center gap-2 uppercase tracking-[0.2em]">
          <Filter className="w-4 h-4 text-osi-blue"/> Filtros de Refinado
        </h3>
        <div className="space-y-8 overflow-y-auto flex-1 pr-1 custom-scrollbar">
          <div className="space-y-3">
            <label className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Región Administrativa</label>
            <div className="relative">
              <select 
                  value={filters.geography}
                  onChange={(e) => onGeographyChange(e.target.value)}
                  className="w-full border-2 border-slate-50 rounded-2xl px-5 py-4 text-sm bg-slate-50 font-black text-slate-700 outline-none focus:border-osi-blue/10 transition-all appearance-none cursor-pointer"
              >
                  <option>Sede Nacional</option>
                  <option>Arequipa</option>
                  <option>Moquegua</option>
                  <option>Cusco</option>
                  <option>Piura</option>
              </select>
              <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-300">▼</div>
            </div>
          </div>

          <div className="space-y-4 pt-2">
            <label className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Matriz Energética</label>
            <div className="space-y-2">
              {Object.keys(filters.energyMatrix).map((key) => (
                <label key={key} className={`flex items-center gap-4 p-4 rounded-[1.25rem] cursor-pointer transition-all border-2 group ${filters.energyMatrix[key] ? 'bg-blue-50 border-osi-blue/20 shadow-sm' : 'bg-transparent border-transparent hover:bg-slate-50'}`}>
                  <div className="relative">
                      <input 
                          type="checkbox" 
                          checked={filters.energyMatrix[key]} 
                          onChange={() => onEnergyToggle(key)}
                          className="sr-only" 
                      />
                      <div className={`w-6 h-6 rounded-lg border-2 transition-all flex items-center justify-center ${filters.energyMatrix[key] ? 'bg-osi-blue border-osi-blue' : 'bg-white border-slate-200'}`}>
                          {filters.energyMatrix[key] && <div className="w-2 h-2 bg-white rounded-full"></div>}
                      </div>
                  </div>
                  <span className={`text-[13px] font-black transition-colors ${filters.energyMatrix[key] ? 'text-osi-blue' : 'text-slate-500 group-hover:text-slate-800'}`}>
                      {key}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
        
        <button 
          onClick={onApply}
          disabled={loading}
          className="w-full bg-slate-900 text-white py-5 rounded-[1.5rem] font-black text-[11px] mt-8 hover:bg-osi-blue transition-all shadow-xl shadow-slate-200 uppercase tracking-[0.2em] active:scale-95 cursor-pointer disabled:opacity-50"
        >
          {loading ? 'Sincronizando...' : 'Aplicar Parámetros'}
        </button>
      </div>
    </aside>
  );
};
