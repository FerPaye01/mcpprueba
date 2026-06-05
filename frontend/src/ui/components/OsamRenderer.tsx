import { useState } from 'react';
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
  FileSpreadsheet
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
        chart: {
          type: 'line' | 'bar' | 'scatter' | 'pie' | 'none';
          x: string;
          y: string;
          series?: string | null;
        };
      };
      provenance: {
        source_tables: string[];
        source_systems: string[];
        filters_applied: string[];
        query_hash: string;
        generated_at: string;
      };
    };
    analysis?: {
      insights: { type: string; text: string }[];
    };
  };
}

export function OsamRenderer({ payload }: OsamRendererProps) {
  const [showProvenance, setShowProvenance] = useState(false);
  const { report, analysis } = payload;
  const { columns, data, presentation, provenance } = report;

  const hasChart = presentation && presentation.chart && presentation.chart.type !== 'none';
  const hasInsights = analysis && analysis.insights && analysis.insights.length > 0;

  // Function to download data to CSV
  const downloadCSV = () => {
    if (!data || data.length === 0) return;
    
    // Header
    const headers = columns.map(c => c.label).join(',');
    
    // Rows
    const rows = data.map(row => 
      columns.map(c => {
        const val = row[c.id];
        return val !== null && val !== undefined ? `"${String(val).replace(/"/g, '""')}"` : '';
      }).join(',')
    );
    
    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    const timestamp = new Date().toISOString().split('T')[0];
    link.setAttribute('download', `reporte_openenergy_${timestamp}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="w-full flex flex-col my-6 animate-in fade-in duration-500">
      
      {/* 1. RENDER CHARTS (Vega-Lite) */}
      {hasChart && (
        <VegaLiteChart 
          data={data} 
          chartSpec={presentation.chart} 
          title="Tendencias & Gráficos Analíticos" 
        />
      )}

      {/* 2. RENDER TABLE (TanStack Table) */}
      <div className="relative group">
        <div className="flex justify-between items-center px-2 mb-2">
          <h4 className="font-black text-sm text-slate-800 tracking-tight uppercase tracking-[0.1em] text-osi-blue opacity-80">
            Reporte de Datos Estructurado
          </h4>
          <button
            onClick={downloadCSV}
            className="flex items-center gap-1.5 px-4 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-black rounded-xl border border-emerald-200/50 transition-all cursor-pointer active:scale-95 shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" /> Exportar CSV
          </button>
        </div>
        
        <OsamTable columns={columns} data={data} />
      </div>

      {/* 3. INSIGHTS SECTION */}
      {hasInsights && (
        <div className="bg-blue-50/50 border border-blue-100 rounded-3xl p-6 mb-6">
          <div className="flex items-center gap-2 mb-4 text-osi-blue">
            <Lightbulb className="w-5 h-5 text-osi-yellow fill-osi-yellow/20 shrink-0" />
            <h5 className="font-black text-xs uppercase tracking-widest text-slate-700">Interpretaciones Analíticas de IA</h5>
          </div>
          <ul className="space-y-3">
            {analysis.insights.map((insight, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="mt-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-[8px] font-black rounded-md uppercase tracking-wider">
                  {insight.type}
                </span>
                <p className="text-[13px] text-slate-600 font-medium leading-relaxed">
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
          className="w-full flex items-center justify-between px-6 py-4.5 text-left text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-all cursor-pointer"
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
                <span className="font-black text-slate-700">{provenance.source_tables?.join(', ')}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs">
                <Database className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Sistemas Origen:</span>
                <span className="font-black text-slate-700">{provenance.source_systems?.join(', ')}</span>
              </div>
              <div className="flex items-center gap-2.5 text-xs">
                <Hash className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Hash de Consulta:</span>
                <span className="font-mono text-slate-600 select-all truncate text-[11px]" title={provenance.query_hash}>
                  {provenance.query_hash}
                </span>
              </div>
            </div>
            <div className="space-y-3.5">
              <div className="flex items-center gap-2.5 text-xs">
                <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider">Generado El:</span>
                <span className="font-black text-slate-700">
                  {provenance.generated_at ? new Date(provenance.generated_at).toLocaleString() : '-'}
                </span>
              </div>
              <div className="flex items-start gap-2.5 text-xs">
                <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <span className="font-bold text-slate-400 w-28 uppercase text-[9px] tracking-wider mt-0.5">Seguridad RLS:</span>
                <div className="flex flex-wrap gap-1">
                  {provenance.filters_applied?.map((filt, idx) => (
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
