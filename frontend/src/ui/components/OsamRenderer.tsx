import { useState, useEffect, useMemo } from 'react';
import { VegaLiteChart } from './VegaLiteChart';
import { OsamTable } from './OsamTable';
import { 
  ShieldCheck, 
  Database, 
  Calendar, 
  Hash, 
  ChevronDown, 
  ChevronUp, 
  Lightbulb,
  FileSpreadsheet,
  Filter,
  CheckSquare,
  Square,
  Search,
  Sliders,
  Table,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

interface OsamRendererProps {
  payload: {
    report: {
      query: {
        fields: { name: string; aggregation: string }[];
        dimensions: string[];
        filters: { field: string; operator: string; value: any }[];
      };
      columns: { id: string; label: string; type: string; format: string }[];
      data: any[];
      presentation: {
        default_view?: 'chart' | 'table';
        chart: {
          type: 'line' | 'bar' | 'scatter' | 'pie' | 'none';
          x: string;
          y: string;
          series?: string | null;
        };
      };
      provenance?: {
        source_tables?: string[];
        source_systems?: string[];
        filters_applied?: string[];
        query_hash?: string;
        generated_at?: string;
      };
    };
    analysis?: {
      insights: { type: string; text: string }[];
    };
  };
  settings?: {
    showTable: boolean;
    showChart: boolean;
  };
}

interface ColumnFilter {
  id: string;
  label: string;
  type: 'nominal' | 'quantitative' | 'temporal';
  
  // Categorical (nominal)
  allValues: string[];
  selectedValues: string[];
  searchValue: string;
  
  // Quantitative (numeric)
  min: number;
  max: number;
  currentMin: number;
  currentMax: number;
  
  // Temporal (date)
  minDate: string;
  maxDate: string;
  currentMinDate: string;
  currentMaxDate: string;
}

export function OsamRenderer({ payload, settings = { showTable: true, showChart: true } }: OsamRendererProps) {
  const [showProvenance, setShowProvenance] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  const { report, analysis } = payload;
  const { columns, data, presentation, provenance } = report;

  // Estado para los filtros locales activos y destinos
  const [localFilters, setLocalFilters] = useState<Record<string, ColumnFilter>>({});
  const [filterTargets, setFilterTargets] = useState({
    table: true,
    chart: true
  });

  // Inicializar filtros dinámicamente según la naturaleza de los datos
  useEffect(() => {
    if (!data || !columns) return;
    
    const initialFilters: Record<string, ColumnFilter> = {};
    
    columns.forEach(col => {
      const rawValues = data.map(row => row[col.id]);
      const nonNullValues = rawValues.filter(v => v !== null && v !== undefined);
      
      // Determinar la naturaleza de los datos para esta columna:
      // A. Temporal si tiene formato fecha ISO estándar (YYYY-MM-DD)
      const allAreISO = nonNullValues.length > 0 && nonNullValues.every(v => /^\d{4}-\d{2}-\d{2}$/.test(String(v)));
      const isColTemporal = col.type === 'temporal' || allAreISO;
      
      // B. Cuantitativo si todos los valores son numéricos y no es fecha
      const allAreNumbers = nonNullValues.length > 0 && nonNullValues.every(v => {
        const num = Number(v);
        return !isNaN(num);
      });
      const isColQuantitative = col.type === 'quantitative' || (allAreNumbers && !isColTemporal);
      
      if (isColTemporal) {
        const dateStrings = nonNullValues.map(v => String(v));
        const sortedDates = [...dateStrings].sort();
        const minD = sortedDates[0] || '';
        const maxD = sortedDates[sortedDates.length - 1] || '';
        
        initialFilters[col.id] = {
          id: col.id,
          label: col.label,
          type: 'temporal',
          allValues: [],
          selectedValues: [],
          searchValue: '',
          min: 0,
          max: 0,
          currentMin: 0,
          currentMax: 0,
          minDate: minD,
          maxDate: maxD,
          currentMinDate: minD,
          currentMaxDate: maxD
        };
      } else if (isColQuantitative) {
        const numValues = nonNullValues.map(v => Number(v));
        const minN = numValues.length > 0 ? Math.min(...numValues) : 0;
        const maxN = numValues.length > 0 ? Math.max(...numValues) : 0;
        
        initialFilters[col.id] = {
          id: col.id,
          label: col.label,
          type: 'quantitative',
          allValues: [],
          selectedValues: [],
          searchValue: '',
          min: minN,
          max: maxN,
          currentMin: minN,
          currentMax: maxN,
          minDate: '',
          maxDate: '',
          currentMinDate: '',
          currentMaxDate: ''
        };
      } else {
        const stringValues = rawValues.map(v => v === null || v === undefined ? '' : String(v));
        const uniqueValues = Array.from(new Set(stringValues));
        
        initialFilters[col.id] = {
          id: col.id,
          label: col.label,
          type: 'nominal',
          allValues: uniqueValues,
          selectedValues: uniqueValues,
          searchValue: '',
          min: 0,
          max: 0,
          currentMin: 0,
          currentMax: 0,
          minDate: '',
          maxDate: '',
          currentMinDate: '',
          currentMaxDate: ''
        };
      }
    });
    
    setLocalFilters(initialFilters);
  }, [data, columns]);

  // Manejar cambio de checkbox de filtro nominal (categorías)
  const toggleNominalValue = (columnId: string, value: string) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'nominal') return prev;
      
      const selected = filter.selectedValues;
      const nextSelected = selected.includes(value)
        ? selected.filter(v => v !== value)
        : [...selected, value];
        
      return {
        ...prev,
        [columnId]: {
          ...filter,
          selectedValues: nextSelected
        }
      };
    });
  };

  // Seleccionar o deseleccionar todo el grupo nominal
  const selectAllNominal = (columnId: string, selectAll: boolean) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'nominal') return prev;
      
      return {
        ...prev,
        [columnId]: {
          ...filter,
          selectedValues: selectAll ? [...filter.allValues] : []
        }
      };
    });
  };

  // Cambiar el buscador de un filtro nominal
  const handleNominalSearch = (columnId: string, searchText: string) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'nominal') return prev;
      
      return {
        ...prev,
        [columnId]: {
          ...filter,
          searchValue: searchText
        }
      };
    });
  };

  // Cambiar rango numérico
  const handleNumericChange = (columnId: string, bound: 'min' | 'max', value: string) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'quantitative') return prev;
      
      const num = value === '' ? (bound === 'min' ? filter.min : filter.max) : Number(value);
      if (isNaN(num)) return prev;
      
      return {
        ...prev,
        [columnId]: {
          ...filter,
          currentMin: bound === 'min' ? num : filter.currentMin,
          currentMax: bound === 'max' ? num : filter.currentMax
        }
      };
    });
  };

  const resetNumericFilter = (columnId: string) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'quantitative') return prev;
      
      return {
        ...prev,
        [columnId]: {
          ...filter,
          currentMin: filter.min,
          currentMax: filter.max
        }
      };
    });
  };

  // Cambiar fechas
  const handleDateChange = (columnId: string, bound: 'min' | 'max', value: string) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'temporal') return prev;
      
      return {
        ...prev,
        [columnId]: {
          ...filter,
          currentMinDate: bound === 'min' ? value : filter.currentMinDate,
          currentMaxDate: bound === 'max' ? value : filter.currentMaxDate
        }
      };
    });
  };

  const resetDateFilter = (columnId: string) => {
    setLocalFilters(prev => {
      const filter = prev[columnId];
      if (!filter || filter.type !== 'temporal') return prev;
      
      return {
        ...prev,
        [columnId]: {
          ...filter,
          currentMinDate: filter.minDate,
          currentMaxDate: filter.maxDate
        }
      };
    });
  };

  // Limpiar todos los filtros locales
  const resetAllFilters = () => {
    setLocalFilters(prev => {
      const resetFilters: Record<string, ColumnFilter> = {};
      Object.entries(prev).forEach(([id, filter]) => {
        if (filter.type === 'nominal') {
          resetFilters[id] = {
            ...filter,
            selectedValues: [...filter.allValues],
            searchValue: ''
          };
        } else if (filter.type === 'quantitative') {
          resetFilters[id] = {
            ...filter,
            currentMin: filter.min,
            currentMax: filter.max
          };
        } else if (filter.type === 'temporal') {
          resetFilters[id] = {
            ...filter,
            currentMinDate: filter.minDate,
            currentMaxDate: filter.maxDate
          };
        }
      });
      return resetFilters;
    });
  };

  // Filtrar los datos locales
  const filteredData = useMemo(() => {
    if (Object.keys(localFilters).length === 0) return data;
    
    return data.filter(row => {
      return Object.entries(localFilters).every(([colId, filter]) => {
        const val = row[colId];
        
        if (filter.type === 'nominal') {
          const strVal = val === null || val === undefined ? '' : String(val);
          return filter.selectedValues.includes(strVal);
        }
        
        if (filter.type === 'quantitative') {
          if (val === null || val === undefined) return true;
          const num = Number(val);
          if (isNaN(num)) return true;
          return num >= filter.currentMin && num <= filter.currentMax;
        }
        
        if (filter.type === 'temporal') {
          if (val === null || val === undefined) return true;
          const strVal = String(val);
          return strVal >= filter.currentMinDate && strVal <= filter.currentMaxDate;
        }
        
        return true;
      });
    });
  }, [data, localFilters]);

  // Verificar si hay algún filtro activo modificado
  const isAnyFilterActive = useMemo(() => {
    return Object.values(localFilters).some(filter => {
      if (filter.type === 'nominal') {
        return filter.selectedValues.length < filter.allValues.length;
      }
      if (filter.type === 'quantitative') {
        return filter.currentMin > filter.min || filter.currentMax < filter.max;
      }
      if (filter.type === 'temporal') {
        return filter.currentMinDate > filter.minDate || filter.currentMaxDate < filter.maxDate;
      }
      return false;
    });
  }, [localFilters]);

  const hasChartRaw = presentation && presentation.chart && presentation.chart.type !== 'none';
  const hasChart = hasChartRaw && settings.showChart;
  
  // Mostrar pestañas solo si se permiten ambos entregables y hay un gráfico disponible
  const showTabs = settings.showTable && settings.showChart && hasChart;

  const defaultTab = (presentation && presentation.default_view) || (hasChart ? 'chart' : 'table');
  const [activeTab, setActiveTab] = useState<'chart' | 'table'>(defaultTab);

  useEffect(() => {
    const nextDefault = (presentation && presentation.default_view) || (hasChart ? 'chart' : 'table');
    setActiveTab(nextDefault);
  }, [hasChart, presentation]);

  const hasInsights = analysis && analysis.insights && analysis.insights.length > 0;

  // Datos asignados según el target seleccionado
  const tableData = filterTargets.table ? filteredData : data;
  const chartData = filterTargets.chart ? filteredData : data;

  // Calcular frecuencias de valores
  const getValueCounts = (columnId: string) => {
    const counts: Record<string, number> = {};
    data.forEach(row => {
      const val = row[columnId];
      const strVal = val === null || val === undefined ? '' : String(val);
      counts[strVal] = (counts[strVal] || 0) + 1;
    });
    return counts;
  };

  // Exportar a CSV (UTF-8 con BOM para Excel)
  const downloadCSV = () => {
    if (!tableData || tableData.length === 0) return;
    
    const headers = columns.map(c => c.label).join(',');
    
    const rows = tableData.map(row => 
      columns.map(c => {
        const val = row[c.id];
        return val !== null && val !== undefined ? `"${String(val).replace(/"/g, '""')}"` : '';
      }).join(',')
    );
    
    const csvContent = '\uFEFF' + [headers, ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const encodedUri = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    const timestamp = new Date().toISOString().split('T')[0];
    link.setAttribute('download', `reporte_filtrado_openenergy_${timestamp}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="w-full flex flex-col my-6 animate-in fade-in duration-500">
      
      {/* 0. PANEL DE FILTROS LOCALES DINÁMICOS */}
      {columns.length > 0 && (
        <div className="border border-slate-200/80 rounded-[1.5rem] overflow-hidden bg-slate-50/20 mb-6 transition-all shadow-sm">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="w-full flex items-center justify-between px-6 py-4.5 text-left text-slate-600 hover:text-slate-800 hover:bg-slate-50 transition-all cursor-pointer select-none"
          >
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-osi-blue shrink-0" />
              <span className="text-xs font-black uppercase tracking-wider">Filtros locales interactivos</span>
              
              <span className="px-2 py-0.5 bg-osi-blue/10 text-osi-blue text-[9px] font-black rounded-full uppercase tracking-wider">
                {isAnyFilterActive ? 'Filtros Activos' : 'Mostrar todo'}
              </span>
            </div>
            {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>

          {showFilters && (
            <div className="px-6 pb-6 pt-4 border-t border-slate-100 bg-white space-y-6 animate-in slide-in-from-top-2 duration-300">
              
              {/* Configuración superior */}
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div className="flex flex-col gap-1">
                  <h5 className="text-xs font-black text-slate-800 uppercase tracking-wider">
                    Configuración de Filtros Locales
                  </h5>
                  <p className="text-[10px] text-slate-400 font-bold">
                    Filtre el conjunto de datos actual de forma dinámica según la naturaleza de sus campos. Ningún dato saldrá de su navegador.
                  </p>
                </div>
                
                {isAnyFilterActive && (
                  <button
                    onClick={resetAllFilters}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-[10px] font-black rounded-xl border border-rose-200/50 transition-all cursor-pointer active:scale-95 shadow-sm uppercase tracking-wider"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Restaurar Todo
                  </button>
                )}
              </div>

              {/* Destinos de filtrado (Target Selector) */}
              <div className="bg-slate-50/50 p-4.5 rounded-[1.25rem] border border-slate-200/60 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-osi-blue shrink-0" />
                  <div>
                    <span className="font-black text-[10px] text-slate-400 uppercase tracking-widest block">
                      Destino del Filtrado (Checks de Componentes)
                    </span>
                    <span className="text-[11px] font-bold text-slate-600">
                      Marque qué elementos del reporte responderán a los filtros locales
                    </span>
                  </div>
                </div>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2.5 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200/60 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-800 cursor-pointer select-none group transition-all shadow-sm">
                    <input
                      type="checkbox"
                      checked={filterTargets.table}
                      onChange={() => setFilterTargets(prev => ({ ...prev, table: !prev.table }))}
                      className="hidden"
                    />
                    {filterTargets.table ? (
                      <CheckSquare className="w-4 h-4 text-osi-blue fill-osi-blue/5 shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-300 shrink-0 group-hover:text-slate-400" />
                    )}
                    <Table className="w-3.5 h-3.5 text-slate-400 group-hover:text-osi-blue transition-colors shrink-0" />
                    <span className={filterTargets.table ? 'font-black text-slate-800' : ''}>
                      Tabla de Datos
                    </span>
                  </label>

                  {hasChart && (
                    <label className="flex items-center gap-2.5 px-4 py-2 bg-white hover:bg-slate-50 border border-slate-200/60 rounded-xl text-xs font-bold text-slate-600 hover:text-slate-800 cursor-pointer select-none group transition-all shadow-sm">
                      <input
                        type="checkbox"
                        checked={filterTargets.chart}
                        onChange={() => setFilterTargets(prev => ({ ...prev, chart: !prev.chart }))}
                        className="hidden"
                      />
                      {filterTargets.chart ? (
                        <CheckSquare className="w-4 h-4 text-osi-blue fill-osi-blue/5 shrink-0" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-300 shrink-0 group-hover:text-slate-400" />
                      )}
                      <TrendingUp className="w-3.5 h-3.5 text-slate-400 group-hover:text-osi-blue transition-colors shrink-0" />
                      <span className={filterTargets.chart ? 'font-black text-slate-800' : ''}>
                        Gráfico Analítico
                      </span>
                    </label>
                  )}
                </div>
              </div>

              {/* Grid de Controles Generados */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                {Object.entries(localFilters).map(([colId, filter]) => {
                  const counts = getValueCounts(colId);
                  
                  return (
                    <div key={colId} className="flex flex-col bg-slate-50/20 border border-slate-200/60 rounded-[1.25rem] p-4.5 gap-3 shadow-sm hover:shadow transition-all hover:bg-slate-50/40">
                      
                      {/* Card Header */}
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                        <div className="flex flex-col min-w-0">
                          <span className="font-black text-[11px] text-slate-800 uppercase tracking-wide truncate max-w-xs" title={filter.label}>
                            {filter.label}
                          </span>
                          <span className="text-[8px] font-black tracking-widest text-slate-400 uppercase">
                            {filter.type === 'nominal' ? 'Categoría' : filter.type === 'quantitative' ? 'Rango Numérico' : 'Rango de Fecha'}
                          </span>
                        </div>
                        
                        {/* Indicador de filtrado activo */}
                        {filter.type === 'nominal' && filter.selectedValues.length < filter.allValues.length && (
                          <span className="px-1.5 py-0.5 bg-osi-orange/10 text-osi-orange text-[8px] font-black rounded uppercase tracking-wider shrink-0 animate-pulse">
                            Filtrado
                          </span>
                        )}
                        {filter.type === 'quantitative' && (filter.currentMin > filter.min || filter.currentMax < filter.max) && (
                          <span className="px-1.5 py-0.5 bg-osi-orange/10 text-osi-orange text-[8px] font-black rounded uppercase tracking-wider shrink-0 animate-pulse">
                            Filtrado
                          </span>
                        )}
                        {filter.type === 'temporal' && (filter.currentMinDate > filter.minDate || filter.currentMaxDate < filter.maxDate) && (
                          <span className="px-1.5 py-0.5 bg-osi-orange/10 text-osi-orange text-[8px] font-black rounded uppercase tracking-wider shrink-0 animate-pulse">
                            Filtrado
                          </span>
                        )}
                      </div>

                      {/* Card Body */}
                      <div className="flex-1 flex flex-col justify-center min-h-[5rem]">
                        {filter.type === 'nominal' && (
                          <div className="flex flex-col gap-2.5">
                            {/* Caja de Búsqueda para Categorías (>6 opciones) */}
                            {filter.allValues.length > 6 && (
                              <div className="relative">
                                <input
                                  type="text"
                                  placeholder={`Buscar...`}
                                  value={filter.searchValue || ''}
                                  onChange={e => handleNominalSearch(colId, e.target.value)}
                                  className="w-full bg-white border border-slate-200 rounded-lg pl-7 pr-3 py-1 text-[11px] font-bold text-slate-600 outline-none focus:border-osi-blue/20 transition-all shadow-inner"
                                />
                                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400" />
                              </div>
                            )}

                            {/* Acciones Rápidas */}
                            <div className="flex gap-2">
                              <button
                                onClick={() => selectAllNominal(colId, true)}
                                className="text-[9px] font-black text-osi-blue hover:text-osi-blue-dark uppercase tracking-wider cursor-pointer"
                              >
                                Todo
                              </button>
                              <span className="text-slate-200 text-[9px] font-black select-none">|</span>
                              <button
                                onClick={() => selectAllNominal(colId, false)}
                                className="text-[9px] font-black text-osi-blue hover:text-osi-blue-dark uppercase tracking-wider cursor-pointer"
                              >
                                Ninguno
                              </button>
                            </div>

                            {/* Lista de Checkboxes */}
                            <div className="flex flex-col gap-1.5 max-h-32 overflow-y-auto pr-1 custom-scrollbar">
                              {filter.allValues
                                .filter(val => {
                                  const search = (filter.searchValue || '').toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                                  const target = val.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                                  return target.includes(search);
                                })
                                .map(val => {
                                  const isChecked = filter.selectedValues.includes(val);
                                  const count = counts[val] || 0;
                                  return (
                                    <label key={val} className="flex items-center justify-between text-xs font-bold text-slate-600 hover:text-slate-800 cursor-pointer select-none group">
                                      <div className="flex items-center gap-1.5 min-w-0">
                                        <input
                                          type="checkbox"
                                          checked={isChecked}
                                          onChange={() => toggleNominalValue(colId, val)}
                                          className="hidden"
                                        />
                                        {isChecked ? (
                                          <CheckSquare className="w-3.5 h-3.5 text-osi-blue fill-osi-blue/5 shrink-0 animate-in zoom-in-75 duration-150" />
                                        ) : (
                                          <Square className="w-3.5 h-3.5 text-slate-300 shrink-0 group-hover:text-slate-400" />
                                        )}
                                        <span className={`truncate ${isChecked ? 'font-black text-slate-800' : ''}`} title={val}>
                                          {val === '' ? '(Vacío)' : val}
                                        </span>
                                      </div>
                                      <span className="px-1.5 py-0.5 bg-slate-100 text-slate-400 text-[9px] font-black rounded-md shrink-0">
                                        {count}
                                      </span>
                                    </label>
                                  );
                                })
                              }
                            </div>
                          </div>
                        )}

                        {filter.type === 'quantitative' && (
                          <div className="flex flex-col gap-2">
                            <div className="flex items-center gap-3">
                              <div className="flex-1 flex flex-col gap-1">
                                <span className="text-[9px] text-slate-400 font-black uppercase tracking-wider">Mínimo</span>
                                <input
                                  type="number"
                                  step="any"
                                  value={filter.currentMin}
                                  onChange={e => handleNumericChange(colId, 'min', e.target.value)}
                                  className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-black text-slate-700 outline-none focus:border-osi-blue/20 transition-all shadow-inner"
                                />
                              </div>
                              <div className="flex-1 flex flex-col gap-1">
                                <span className="text-[9px] text-slate-400 font-black uppercase tracking-wider">Máximo</span>
                                <input
                                  type="number"
                                  step="any"
                                  value={filter.currentMax}
                                  onChange={e => handleNumericChange(colId, 'max', e.target.value)}
                                  className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-black text-slate-700 outline-none focus:border-osi-blue/20 transition-all shadow-inner"
                                />
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-between text-[9px] text-slate-400 font-bold mt-1">
                              <span>Límites de origen:</span>
                              <span className="font-mono text-slate-600 bg-slate-100 px-1 py-0.5 rounded">
                                {filter.min} a {filter.max}
                              </span>
                            </div>
                            
                            {(filter.currentMin > filter.min || filter.currentMax < filter.max) && (
                              <button
                                onClick={() => resetNumericFilter(colId)}
                                className="text-[9px] font-black text-osi-blue hover:text-osi-blue-dark uppercase tracking-wider self-start cursor-pointer mt-1"
                              >
                                Restaurar Rango
                              </button>
                            )}
                          </div>
                        )}

                        {filter.type === 'temporal' && (
                          <div className="flex flex-col gap-2">
                            <div className="flex items-center gap-3">
                              <div className="flex-1 flex flex-col gap-1">
                                <span className="text-[9px] text-slate-400 font-black uppercase tracking-wider">Desde</span>
                                <input
                                  type="date"
                                  value={filter.currentMinDate}
                                  onChange={e => handleDateChange(colId, 'min', e.target.value)}
                                  className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-black text-slate-700 outline-none focus:border-osi-blue/20 transition-all shadow-inner"
                                />
                              </div>
                              <div className="flex-1 flex flex-col gap-1">
                                <span className="text-[9px] text-slate-400 font-black uppercase tracking-wider">Hasta</span>
                                <input
                                  type="date"
                                  value={filter.currentMaxDate}
                                  onChange={e => handleDateChange(colId, 'max', e.target.value)}
                                  className="w-full bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs font-black text-slate-700 outline-none focus:border-osi-blue/20 transition-all shadow-inner"
                                />
                              </div>
                            </div>

                            <div className="flex items-center justify-between text-[9px] text-slate-400 font-bold mt-1">
                              <span>Rango original:</span>
                              <span className="font-mono text-slate-600 bg-slate-100 px-1 py-0.5 rounded">
                                {filter.minDate} a {filter.maxDate}
                              </span>
                            </div>

                            {(filter.currentMinDate > filter.minDate || filter.currentMaxDate < filter.maxDate) && (
                              <button
                                onClick={() => resetDateFilter(colId)}
                                className="text-[9px] font-black text-osi-blue hover:text-osi-blue-dark uppercase tracking-wider self-start cursor-pointer mt-1"
                              >
                                Restaurar Fechas
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

            </div>
          )}
        </div>
      )}
      
      {/* 1. SECCIÓN DE PESTAÑAS (TABS) PARA CONTROL DE VISTAS */}
      {showTabs && (
        <div className="flex items-center justify-between border-b border-slate-200 mb-6 bg-slate-50/50 p-1.5 rounded-2xl border shadow-sm">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('chart')}
              className={`flex items-center gap-2 px-6 py-2.5 text-xs font-black uppercase tracking-wider rounded-xl transition-all cursor-pointer ${
                activeTab === 'chart'
                  ? 'bg-osi-blue text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Vista Gráfico
            </button>
            <button
              onClick={() => setActiveTab('table')}
              className={`flex items-center gap-2 px-6 py-2.5 text-xs font-black uppercase tracking-wider rounded-xl transition-all cursor-pointer ${
                activeTab === 'table'
                  ? 'bg-osi-blue text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-100'
              }`}
            >
              <Table className="w-4 h-4" />
              Vista Tabla
            </button>
          </div>
          
          {activeTab === 'table' && (
            <button
              onClick={downloadCSV}
              disabled={tableData.length === 0}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-50 hover:bg-emerald-100 disabled:opacity-50 disabled:pointer-events-none text-emerald-700 text-xs font-black rounded-xl border border-emerald-200/50 transition-all cursor-pointer active:scale-95 shadow-sm uppercase tracking-wider mr-2"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" /> Exportar CSV
            </button>
          )}
        </div>
      )}

      {/* 1. RENDER CHARTS (Vega-Lite) utilizando los datos asignados */}
      {hasChart && (showTabs ? activeTab === 'chart' : settings.showChart) && (
        <VegaLiteChart 
          data={chartData} 
          chartSpec={presentation.chart} 
          title="Tendencias & Gráficos Analíticos" 
        />
      )}

      {/* 2. RENDER TABLE (TanStack Table) utilizando los datos asignados */}
      {settings.showTable && (showTabs ? activeTab === 'table' : !hasChart) && (
        <div className="relative group animate-in fade-in duration-300">
          <div className="flex justify-between items-center px-2 mb-2">
            <h4 className="font-black text-sm text-slate-800 tracking-tight uppercase tracking-[0.1em] text-osi-blue opacity-80">
              Reporte de Datos Estructurado
            </h4>
            {!showTabs && (
              <button
                onClick={downloadCSV}
                disabled={tableData.length === 0}
                className="flex items-center gap-1.5 px-4 py-2 bg-emerald-50 hover:bg-emerald-100 disabled:opacity-50 disabled:pointer-events-none text-emerald-700 text-xs font-black rounded-xl border border-emerald-200/50 transition-all cursor-pointer active:scale-95 shadow-sm"
              >
                <FileSpreadsheet className="w-3.5 h-3.5" /> Exportar CSV
              </button>
            )}
          </div>
          
          <OsamTable columns={columns} data={tableData} />
        </div>
      )}

      {/* Warning si se intentó renderizar tabla pero está desactivada por config */}
      {!settings.showTable && !hasChart && (
        <div className="bg-rose-50 border border-rose-100 rounded-3xl p-6 text-center text-rose-700 text-xs font-black uppercase tracking-wider mb-6">
          ⚠️ Reporte Tabular Oculto: Habilite las Tablas de Datos en la configuración de entregables para ver el reporte.
        </div>
      )}

      {/* 3. INSIGHTS SECTION */}
      {hasInsights && (
        <div className="bg-blue-50/50 border border-blue-100 rounded-3xl p-6 mb-6 mt-6">
          <div className="flex items-center gap-2 mb-4 text-osi-blue">
            <Lightbulb className="w-5 h-5 text-osi-yellow fill-osi-yellow/20 shrink-0" />
            <h5 className="font-black text-xs uppercase tracking-widest text-slate-700">Interpretaciones Analíticas de IA</h5>
          </div>
          <ul className="space-y-3">
            {analysis.insights.map((insight, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="mt-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-[8px] font-black rounded-md uppercase tracking-wider shrink-0 self-start">
                  {insight.type}
                </span>
                <p className="flex-1 min-w-0 text-[13px] text-slate-600 font-medium leading-relaxed">
                  {insight.text}
                </p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 4. PROVENANCE / TRAZABILIDAD (Collapsible) */}
      <div className="border border-slate-200/80 rounded-[1.5rem] overflow-hidden bg-slate-50/30">
        <button
          onClick={() => setShowProvenance(!showProvenance)}
          className="w-full flex items-center justify-between px-6 py-4.5 text-left text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-all cursor-pointer select-none"
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="text-xs font-black uppercase tracking-wider">Linaje de Datos y Trazabilidad RLS</span>
          </div>
          {showProvenance ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showProvenance && (
          <div className="px-6 pb-6 pt-2 grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-100 bg-white animate-in slide-in-from-top-2 duration-300">
            <div className="space-y-3.5">
              <div className="flex items-center gap-2.5 text-xs">
                <Database className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Tablas Origen:</span>
                <span className="font-black text-slate-700">{provenance?.source_tables?.join(', ')}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs">
                <Database className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Sistemas Origen:</span>
                <span className="font-black text-slate-700">{provenance?.source_systems?.join(', ')}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs">
                <Hash className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Hash de Consulta:</span>
                <span className="font-mono text-slate-600 select-all truncate text-[11px]" title={provenance?.query_hash}>
                  {provenance?.query_hash}
                </span>
              </div>
            </div>
            <div className="space-y-3.5">
              <div className="flex items-center gap-2.5 text-xs">
                <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Generado El:</span>
                <span className="font-black text-slate-700">
                  {provenance?.generated_at ? new Date(provenance.generated_at).toLocaleString() : '-'}
                </span>
              </div>
              <div className="flex items-start gap-2.5 text-xs">
                <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider mt-0.5">Seguridad RLS:</span>
                <div className="flex flex-wrap gap-1">
                  {provenance?.filters_applied?.map((filt, idx) => (
                    <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-600 font-mono text-[10px] rounded border border-slate-200">
                      {filt}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
