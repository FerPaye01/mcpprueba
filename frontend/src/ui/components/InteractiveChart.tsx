import { useState, useId } from 'react';
import { Download } from 'lucide-react';

interface ChartDataItem {
  [key: string]: any;
}

interface InteractiveChartProps {
  data: {
    tipo: 'barras' | 'lineas' | 'dispersion' | 'pastel';
    titulo: string;
    columna_x: string;
    columna_y: string;
    datos: ChartDataItem[];
  };
}

export function InteractiveChart({ data }: InteractiveChartProps) {
  const { tipo, titulo, columna_x, columna_y, datos } = data;
  const chartId = useId();
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  if (!datos || datos.length === 0) {
    return (
      <div className="p-6 bg-white border border-slate-200 rounded-3xl text-center text-slate-400 font-semibold">
        No hay datos para graficar.
      </div>
    );
  }

  // Dimensiones del SVG
  const width = 650;
  const height = 320;
  const paddingLeft = 65;
  const paddingRight = 30;
  const paddingTop = 40;
  const paddingBottom = 60;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  // Extraer valores de los ejes
  const xValues = datos.map((d) => String(d[columna_x] || ''));
  const yValues = datos.map((d) => {
    const val = Number(d[columna_y]);
    return isNaN(val) ? 0 : val;
  });

  const maxY = Math.max(...yValues, 1) * 1.1; // 10% de margen arriba

  // Paleta de colores Premium
  const colors = [
    '#0039AA', '#0F52BA', '#3F88C5', '#17A398', '#D64550',
    '#E07A5F', '#3D405B', '#81B29A', '#F2CC8F', '#9A8C98'
  ];

  // Función para descargar el SVG como archivo vectorial
  const handleDownloadSVG = () => {
    const svgEl = document.getElementById(chartId);
    if (!svgEl) return;
    const serializer = new XMLSerializer();
    let source = serializer.serializeToString(svgEl);

    // Asegurar namespaces correctos
    if (!source.match(/^<svg[^>]+xmlns="http:\/\/www\.w3\.org\/2000\/svg"/)) {
      source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }
    if (!source.match(/^<svg[^>]+xmlns:xlink="http:\/\/www\.w3\.org\/1999\/xlink"/)) {
      source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
    }

    const svgBlob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${titulo.toLowerCase().replace(/\s+/g, '_') || 'grafico'}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // --- 1. Gráfico de Barras ---
  const renderBars = () => {
    const barWidth = chartWidth / datos.length;
    const spacing = Math.max(2, barWidth * 0.15);
    const itemWidth = barWidth - spacing;

    return yValues.map((yVal, index) => {
      const xVal = xValues[index];
      const barHeight = (yVal / maxY) * chartHeight;
      const x = paddingLeft + index * barWidth + spacing / 2;
      const y = paddingTop + chartHeight - barHeight;

      return (
        <g key={index} className="transition-all duration-300">
          {/* Barra con gradiente */}
          <rect
            x={x}
            y={y}
            width={itemWidth}
            height={Math.max(1, barHeight)}
            fill={hoveredIndex === index ? 'url(#barHoverGrad)' : 'url(#barGrad)'}
            rx={Math.min(4, itemWidth / 3)}
            className="cursor-pointer transition-all duration-300 hover:filter hover:drop-shadow-[0_4px_8px_rgba(0,57,170,0.3)]"
            onMouseEnter={(e) => {
              setHoveredIndex(index);
              const rect = e.currentTarget.getBoundingClientRect();
              const containerRect = e.currentTarget.parentElement?.parentElement?.getBoundingClientRect();
              if (containerRect) {
                setTooltipPos({
                  x: rect.left - containerRect.left + itemWidth / 2,
                  y: rect.top - containerRect.top - 10
                });
              }
            }}
            onMouseLeave={() => setHoveredIndex(null)}
          />
          {/* Label truncado abajo */}
          <text
            x={x + itemWidth / 2}
            y={height - paddingBottom + 18}
            textAnchor="middle"
            className="text-[10px] fill-slate-500 font-bold"
            transform={`rotate(-15, ${x + itemWidth / 2}, ${height - paddingBottom + 18})`}
          >
            {xVal.length > 12 ? `${xVal.substring(0, 10)}...` : xVal}
          </text>
        </g>
      );
    });
  };

  // --- 2. Gráfico de Líneas ---
  const renderLines = () => {
    const step = chartWidth / (datos.length - 1 || 1);
    let pathD = '';
    
    yValues.forEach((yVal, index) => {
      const x = paddingLeft + index * step;
      const y = paddingTop + chartHeight - (yVal / maxY) * chartHeight;
      if (index === 0) {
        pathD = `M ${x} ${y}`;
      } else {
        pathD += ` L ${x} ${y}`;
      }
    });

    return (
      <g>
        {/* Línea principal */}
        <path
          d={pathD}
          fill="none"
          stroke="#0039AA"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Puntos interactivos */}
        {yValues.map((yVal, index) => {
          const x = paddingLeft + index * step;
          const y = paddingTop + chartHeight - (yVal / maxY) * chartHeight;
          const xVal = xValues[index];

          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r={hoveredIndex === index ? 7 : 5}
                fill={hoveredIndex === index ? '#0F52BA' : '#0039AA'}
                stroke="#FFFFFF"
                strokeWidth="2"
                className="cursor-pointer transition-all duration-200"
                onMouseEnter={(e) => {
                  setHoveredIndex(index);
                  const rect = e.currentTarget.getBoundingClientRect();
                  const containerRect = e.currentTarget.parentElement?.parentElement?.getBoundingClientRect();
                  if (containerRect) {
                    setTooltipPos({
                      x: rect.left - containerRect.left + 5,
                      y: rect.top - containerRect.top - 10
                    });
                  }
                }}
                onMouseLeave={() => setHoveredIndex(null)}
              />
              {/* Label del eje X */}
              <text
                x={x}
                y={height - paddingBottom + 18}
                textAnchor="middle"
                className="text-[10px] fill-slate-500 font-bold"
                transform={`rotate(-15, ${x}, ${height - paddingBottom + 18})`}
              >
                {xVal.length > 12 ? `${xVal.substring(0, 10)}...` : xVal}
              </text>
            </g>
          );
        })}
      </g>
    );
  };

  // --- 3. Gráfico de Dispersión ---
  const renderScatter = () => {
    const step = chartWidth / (datos.length - 1 || 1);

    return yValues.map((yVal, index) => {
      const xVal = xValues[index];
      const x = paddingLeft + index * step;
      const y = paddingTop + chartHeight - (yVal / maxY) * chartHeight;

      return (
        <g key={index}>
          <circle
            cx={x}
            cy={y}
            r={hoveredIndex === index ? 9 : 6}
            fill={colors[index % colors.length]}
            className="cursor-pointer opacity-80 hover:opacity-100 transition-all duration-200"
            onMouseEnter={(e) => {
              setHoveredIndex(index);
              const rect = e.currentTarget.getBoundingClientRect();
              const containerRect = e.currentTarget.parentElement?.parentElement?.getBoundingClientRect();
              if (containerRect) {
                setTooltipPos({
                  x: rect.left - containerRect.left + 5,
                  y: rect.top - containerRect.top - 10
                });
              }
            }}
            onMouseLeave={() => setHoveredIndex(null)}
          />
          <text
            x={x}
            y={height - paddingBottom + 18}
            textAnchor="middle"
            className="text-[10px] fill-slate-500 font-bold"
            transform={`rotate(-15, ${x}, ${height - paddingBottom + 18})`}
          >
            {xVal.length > 12 ? `${xVal.substring(0, 10)}...` : xVal}
          </text>
        </g>
      );
    });
  };

  // --- 4. Gráfico de Pastel (Pie) ---
  const renderPie = () => {
    const total = yValues.reduce((sum, current) => sum + current, 0) || 1;
    let accumulatedAngle = 0;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 100;

    return yValues.map((yVal, index) => {
      const xVal = xValues[index];
      const percentage = (yVal / total) * 100;
      const angle = (yVal / total) * 360;

      const radStart = (accumulatedAngle - 90) * (Math.PI / 180);
      const radEnd = (accumulatedAngle + angle - 90) * (Math.PI / 180);

      const x1 = centerX + radius * Math.cos(radStart);
      const y1 = centerY + radius * Math.sin(radStart);
      const x2 = centerX + radius * Math.cos(radEnd);
      const y2 = centerY + radius * Math.sin(radEnd);

      const largeArc = angle > 180 ? 1 : 0;
      const pathD = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} Z`;

      const color = colors[index % colors.length];
      const midAngle = accumulatedAngle + angle / 2 - 90;
      const textX = centerX + (radius * 1.35) * Math.cos(midAngle * (Math.PI / 180));
      const textY = centerY + (radius * 1.35) * Math.sin(midAngle * (Math.PI / 180));

      accumulatedAngle += angle;

      return (
        <g key={index}>
          <path
            d={pathD}
            fill={color}
            stroke="#ffffff"
            strokeWidth="2"
            opacity={hoveredIndex === index ? 0.95 : 0.8}
            className="cursor-pointer transition-all duration-300"
            onMouseEnter={(e) => {
              setHoveredIndex(index);
              const containerRect = e.currentTarget.parentElement?.parentElement?.getBoundingClientRect();
              if (containerRect) {
                // Posicionar tooltip cerca del centro del arco
                const arcCenterX = centerX + (radius * 0.7) * Math.cos(midAngle * (Math.PI / 180));
                const arcCenterY = centerY + (radius * 0.7) * Math.sin(midAngle * (Math.PI / 180));
                setTooltipPos({ x: arcCenterX, y: arcCenterY - 10 });
              }
            }}
            onMouseLeave={() => setHoveredIndex(null)}
          />
          {/* Label de porcentaje de fondo */}
          {percentage > 3 && (
            <text
              x={textX}
              y={textY}
              textAnchor="middle"
              className="text-[9px] font-black fill-slate-600 bg-white"
            >
              {xVal.length > 8 ? `${xVal.substring(0, 7)}.` : xVal} ({percentage.toFixed(1)}%)
            </text>
          )}
        </g>
      );
    });
  };

  // Dibujar líneas guía horizontales para el eje Y
  const renderGridLines = () => {
    const lines = 4;
    return Array.from({ length: lines + 1 }).map((_, i) => {
      const yVal = (maxY / lines) * i;
      const y = paddingTop + chartHeight - (yVal / maxY) * chartHeight;
      return (
        <g key={i}>
          {/* Línea de cuadrícula */}
          <line
            x1={paddingLeft}
            y1={y}
            x2={width - paddingRight}
            y2={y}
            stroke="#E2E8F0"
            strokeWidth="1"
            strokeDasharray="4 4"
          />
          {/* Texto de valor del eje Y */}
          <text
            x={paddingLeft - 8}
            y={y + 4}
            textAnchor="end"
            className="text-[10px] fill-slate-400 font-bold"
          >
            {yVal.toFixed(1)}
          </text>
        </g>
      );
    });
  };

  return (
    <div className="my-6 p-6 bg-white border border-slate-200/60 rounded-[2.5rem] shadow-xl shadow-slate-100 flex flex-col relative group max-w-full overflow-hidden select-none animate-in fade-in duration-500">
      {/* Cabecera del gráfico */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-50 pb-4 shrink-0">
        <div>
          <span className="text-[10px] uppercase font-black tracking-widest text-osi-blue">Visualización de Datos</span>
          <h4 className="text-base font-black text-slate-800 tracking-tight leading-tight">{titulo}</h4>
        </div>
        <button
          onClick={handleDownloadSVG}
          className="p-3 bg-slate-50 hover:bg-osi-blue hover:text-white text-slate-400 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
          title="Descargar SVG Vectorial"
        >
          <Download className="w-4 h-4" />
        </button>
      </div>

      {/* Contenedor del SVG */}
      <div className="relative flex justify-center w-full overflow-x-auto no-scrollbar">
        <svg
          id={chartId}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          className="overflow-visible"
        >
          <defs>
            {/* Gradientes Premium */}
            <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0F52BA" />
              <stop offset="100%" stopColor="#0039AA" />
            </linearGradient>
            <linearGradient id="barHoverGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3F88C5" />
              <stop offset="100%" stopColor="#0F52BA" />
            </linearGradient>
          </defs>

          {/* Renderizar grilla y ejes si no es un gráfico circular (pie) */}
          {tipo !== 'pastel' && (
            <>
              {renderGridLines()}
              {/* Eje X Línea Base */}
              <line
                x1={paddingLeft}
                y1={paddingTop + chartHeight}
                x2={width - paddingRight}
                y2={paddingTop + chartHeight}
                stroke="#94A3B8"
                strokeWidth="1.5"
              />
            </>
          )}

          {/* Renderizar contenido del gráfico según tipo */}
          {tipo === 'barras' && renderBars()}
          {tipo === 'lineas' && renderLines()}
          {tipo === 'dispersion' && renderScatter()}
          {tipo === 'pastel' && renderPie()}
        </svg>

        {/* Tooltip Dinámico y Flotante en HTML */}
        {hoveredIndex !== null && (
          <div
            className="absolute z-30 pointer-events-none p-3 bg-slate-900 text-white rounded-2xl text-xs font-bold shadow-2xl flex flex-col items-start gap-1 border border-slate-700/50 animate-in zoom-in-95 duration-100"
            style={{
              left: tooltipPos.x,
              top: tooltipPos.y,
              transform: 'translate(-50%, -100%)'
            }}
          >
            <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">{columna_x}: {xValues[hoveredIndex]}</span>
            <span className="text-[13px] font-black text-white">{columna_y}: {yValues[hoveredIndex].toLocaleString()} MW</span>
          </div>
        )}
      </div>
    </div>
  );
}
