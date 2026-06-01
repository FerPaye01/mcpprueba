import type { IDataset } from '../../domain/types/chat';
import { FileText, ExternalLink, Download, Info } from 'lucide-react';

interface DatasetCardProps extends IDataset {}

export const DatasetCard = ({ title, description, format, license, organization }: DatasetCardProps) => (
  <div className="w-72 shrink-0 bg-white border border-slate-200 rounded-2xl p-4 flex flex-col shadow-sm hover:shadow-md hover:border-osi-blue/30 transition-all group">
    <div className="flex items-start justify-between mb-2">
      <h4 className="font-black text-sm text-osi-blue leading-tight pr-2 group-hover:text-osi-blue-dark transition-colors">{title}</h4>
      <div className="p-1.5 rounded-lg bg-osi-blue/5">
        <FileText className="w-3.5 h-3.5 text-osi-blue" />
      </div>
    </div>
    <p className="text-[11px] text-slate-500 line-clamp-3 mb-4 leading-relaxed italic">
      "{description}"
    </p>
    <div className="mt-auto space-y-2">
      <div className="flex flex-wrap gap-1.5 mb-3">
        {format.split(',').map((f) => (
          <span key={f} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px] font-bold uppercase">{f.trim()}</span>
        ))}
        <span className="px-2 py-0.5 bg-blue-50 text-osi-blue rounded text-[9px] font-bold uppercase">{license}</span>
      </div>
      <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mb-3 font-medium">
        <Info className="w-3 h-3" />
        <span>Org: {organization}</span>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <button className="flex items-center justify-center gap-1.5 bg-slate-50 border border-slate-200 text-slate-600 rounded-xl py-2 text-[10px] font-bold hover:bg-slate-100 transition-colors cursor-pointer">
          <ExternalLink className="w-3 h-3" /> Detalles
        </button>
        <button className="flex items-center justify-center gap-1.5 bg-osi-blue text-white rounded-xl py-2 text-[10px] font-bold hover:bg-osi-blue-dark transition-colors cursor-pointer shadow-sm shadow-osi-blue/10">
          <Download className="w-3 h-3" /> Importar
        </button>
      </div>
    </div>
  </div>
);
