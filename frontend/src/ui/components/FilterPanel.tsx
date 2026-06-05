import { useState, useRef, useEffect } from 'react';
import { Lock, Filter, Search, ChevronDown, Check } from 'lucide-react';
import type { IFilterState } from '../../domain/types/chat';

// All 24 departments of Peru + Sede Nacional
const DEPARTAMENTOS = [
  'Sede Nacional',
  'Amazonas',
  'Áncash',
  'Apurímac',
  'Arequipa',
  'Ayacucho',
  'Cajamarca',
  'Callao',
  'Cusco',
  'Huancavelica',
  'Huánuco',
  'Ica',
  'Junín',
  'La Libertad',
  'Lambayeque',
  'Lima',
  'Loreto',
  'Madre de Dios',
  'Moquegua',
  'Pasco',
  'Piura',
  'Puno',
  'San Martín',
  'Tacna',
  'Tumbes',
  'Ucayali'
];

interface FilterPanelProps {
  filters: IFilterState;
  loading: boolean;
  onGeographyChange: (val: string) => void;
  onEnergyToggle: (key: string) => void;
  onApply: () => void;
}

export const FilterPanel = ({ filters, loading, onGeographyChange, onEnergyToggle, onApply }: FilterPanelProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Normalizes accents and search string to prevent indexing mismatches (e.g. Huanuco vs Huánuco)
  const normalizeStr = (str: string) => 
    str.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  const filteredDepartments = DEPARTAMENTOS.filter(dep => 
    normalizeStr(dep).includes(normalizeStr(searchTerm))
  );

  return (
    <aside className="w-80 bg-slate-50 border-l border-slate-200 flex flex-col h-full shrink-0 p-6 space-y-6">
      
      {/* Governance Security Status Panel */}
      <div className="bg-white border border-slate-200 rounded-[2.5rem] p-6 shadow-sm">
        <h3 className="font-black text-xs text-osi-blue mb-4 flex items-center gap-2 uppercase tracking-widest">
          <Lock className="w-4 h-4" /> Gobernanza OpenEnergy
        </h3>
        <div className="space-y-4">
          <div className="bg-green-50/50 border border-green-100 p-4 rounded-2xl">
            <span className="text-[11px] font-black text-green-700 block mb-1 uppercase tracking-tighter">✓ Estatus: Operación Segura</span>
            <p className="text-[10px] text-green-600/70 font-bold leading-relaxed">Conexión Oracle Cifrada y auditoría activa [RF-15].</p>
          </div>
        </div>
      </div>

      {/* Main Filter Panel */}
      <div className="bg-white border border-slate-200 rounded-[2.5rem] p-7 shadow-2xl shadow-slate-200 flex-1 flex flex-col overflow-hidden">
        <h3 className="font-black text-xs text-slate-400 mb-8 flex items-center gap-2 uppercase tracking-[0.2em]">
          <Filter className="w-4 h-4 text-osi-blue"/> Filtros de Refinado
        </h3>
        
        <div className="space-y-8 overflow-y-auto flex-1 pr-1 custom-scrollbar">
          
          {/* Autocomplete Department Search Filter */}
          <div className="space-y-3 relative" ref={dropdownRef}>
            <label className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Región Administrativa</label>
            
            {/* Input Selection Button Trigger */}
            <div 
              onClick={() => { if (!loading) setIsOpen(!isOpen); }}
              className={`w-full border-2 rounded-2xl px-5 py-4 text-sm font-black text-slate-700 flex items-center justify-between cursor-pointer transition-all ${
                isOpen 
                  ? 'border-osi-blue bg-white shadow-lg shadow-blue-50/50' 
                  : 'border-slate-50 bg-slate-50 hover:bg-slate-100/50'
              } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <span className="truncate">{filters.geography}</span>
              <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-300 ${isOpen ? 'rotate-180 text-osi-blue' : ''}`} />
            </div>

            {/* Dropdown Floating Panel */}
            {isOpen && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white border border-slate-100 rounded-3xl shadow-2xl z-30 p-4 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                {/* Search Text Box */}
                <div className="relative">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Buscar departamento..."
                    className="w-full bg-slate-50 border-2 border-transparent focus:border-osi-blue/10 focus:bg-white rounded-xl pl-10 pr-4 py-2.5 text-xs font-semibold text-slate-700 outline-none transition-all shadow-inner"
                    onClick={(e) => e.stopPropagation()} // Prevents dropdown closing when clicking input
                    autoFocus
                  />
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                </div>

                {/* Filtered list of Departments */}
                <div className="max-h-48 overflow-y-auto space-y-0.5 custom-scrollbar pr-1">
                  {filteredDepartments.length > 0 ? (
                    filteredDepartments.map((dep) => {
                      const isSelected = filters.geography === dep;
                      return (
                        <div
                          key={dep}
                          onClick={() => {
                            onGeographyChange(dep);
                            setIsOpen(false);
                            setSearchTerm('');
                          }}
                          className={`flex items-center justify-between px-4 py-2.5 rounded-xl cursor-pointer text-xs font-bold transition-all ${
                            isSelected 
                              ? 'bg-blue-50 text-osi-blue' 
                              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'
                          }`}
                        >
                          <span className="truncate">{dep}</span>
                          {isSelected && <Check className="w-3.5 h-3.5 text-osi-blue shrink-0" />}
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-4 text-center text-xs text-slate-400 italic font-semibold">
                      No se encontraron resultados
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Energy Matrix Multi-Select Checkboxes */}
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
        
        {/* Action button */}
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
