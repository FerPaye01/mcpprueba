import { useEffect, useRef } from 'react';
import vegaEmbed from 'vega-embed';

interface VegaLiteChartProps {
  data: any[];
  chartSpec: {
    type: 'line' | 'bar' | 'scatter' | 'pie' | 'none';
    x: string;
    y: string;
    series?: string | null;
  };
  title?: string;
}

export function VegaLiteChart({ data, chartSpec, title }: VegaLiteChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !data || data.length === 0 || chartSpec.type === 'none') return;

    // Map OSAM chart types to Vega-Lite marks
    let mark: any = 'line';
    if (chartSpec.type === 'bar') {
      mark = 'bar';
    } else if (chartSpec.type === 'scatter') {
      mark = 'point';
    } else if (chartSpec.type === 'pie') {
      mark = 'arc';
    }

    // Obtener las claves reales del primer objeto de datos (ignora mayúsculas/minúsculas y caracteres especiales de agregación como sum(x))
    const firstRow = data[0] || {};
    const dataKeys = Object.keys(firstRow);

    const findBestMatch = (field: string) => {
      if (!field) return '';
      const cleaned = field.toLowerCase().replace(/[^a-z0-9_]/g, '');
      
      // 1. Coincidencia exacta (insensible a mayúsculas)
      const exactMatch = dataKeys.find(k => k.toLowerCase() === field.toLowerCase());
      if (exactMatch) return exactMatch;
      
      // 2. Coincidencia limpia (quitando paréntesis o funciones como SUM, AVG)
      const cleanMatch = dataKeys.find(k => k.toLowerCase() === cleaned);
      if (cleanMatch) return cleanMatch;
      
      // 3. Coincidencia por subcadena (si la clave de los datos está dentro del campo solicitado o viceversa)
      const substringMatch = dataKeys.find(k => {
        const kLower = k.toLowerCase();
        const fLower = field.toLowerCase();
        return fLower.includes(kLower) || kLower.includes(fLower);
      });
      if (substringMatch) return substringMatch;
      
      return field; // por defecto si no hay coincidencia
    };

    const xField = findBestMatch(chartSpec.x);
    const yField = findBestMatch(chartSpec.y);
    const seriesField = chartSpec.series ? findBestMatch(chartSpec.series) : null;

    const encoding: any = {
      x: {
        field: xField,
        type: 'nominal',
        axis: { 
          labelAngle: -45, 
          title: chartSpec.x ? chartSpec.x.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) : '',
          labelFont: 'Poppins, sans-serif',
          titleFont: 'Poppins, sans-serif'
        }
      },
      y: {
        field: yField,
        type: 'quantitative',
        axis: { 
          title: chartSpec.y ? chartSpec.y.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) : '',
          labelFont: 'Poppins, sans-serif',
          titleFont: 'Poppins, sans-serif'
        }
      }
    };

    // If it's a pie chart, restructure encoding
    if (chartSpec.type === 'pie') {
      encoding.theta = { field: yField, type: 'quantitative' };
      encoding.color = { 
        field: xField, 
        type: 'nominal',
        legend: {
          labelFont: 'Poppins, sans-serif',
          titleFont: 'Poppins, sans-serif'
        }
      };
      delete encoding.x;
      delete encoding.y;
    } else if (seriesField) {
      encoding.color = {
        field: seriesField,
        type: 'nominal',
        legend: { 
          title: chartSpec.series ? chartSpec.series.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()) : '',
          labelFont: 'Poppins, sans-serif',
          titleFont: 'Poppins, sans-serif'
        }
      };
    }

    // Build the Vega-Lite specification
    const spec: any = {
      $schema: 'https://vega.github.io/schema/vega-lite/v5.json',
      description: title || 'OSAM Analítico',
      width: 'container',
      height: 250,
      data: { values: data },
      mark: { 
        type: mark, 
        tooltip: true, 
        interpolate: 'monotone',
        size: chartSpec.type === 'bar' ? 30 : undefined
      },
      encoding: encoding,
      config: {
        background: '#ffffff',
        font: 'Poppins, sans-serif',
        view: { stroke: 'transparent' }
      }
    };

    const viewPromise = vegaEmbed(containerRef.current, spec, { 
      actions: false, 
      mode: 'vega-lite',
      renderer: 'svg'
    });

    return () => {
      viewPromise.then(res => res.view.finalize()).catch(() => {});
    };
  }, [data, chartSpec, title]);

  return (
    <div className="w-full bg-white p-6 border border-slate-100 rounded-[2rem] shadow-xl shadow-slate-100/50 mb-6">
      <h4 className="font-black text-sm text-slate-800 tracking-tight mb-4 uppercase tracking-[0.1em] text-osi-blue opacity-80">
        {title || 'Visualización de Datos'}
      </h4>
      <div ref={containerRef} className="w-full min-h-[260px] vega-embed-container"></div>
    </div>
  );
}
