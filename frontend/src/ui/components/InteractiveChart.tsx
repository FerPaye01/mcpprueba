import { useState, useId, useRef, useEffect } from 'react';
import { Download, Maximize2, X, ZoomIn, ZoomOut } from 'lucide-react';

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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [zoomScale, setZoomScale] = useState(1.0);
  
  // Estados para el arrastre manual (Pan/Drag)
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeftStart, setScrollLeftStart] = useState(0);

  // Estado para medir y adaptar dinámicamente la altura del gráfico en el modal
  const [modalHeight, setModalHeight] = useState(500);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isModalOpen || !containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const newHeight = entry.contentRect.height;
        if (newHeight > 100) {
          setModalHeight(newHeight);
        }
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [isModalOpen]);

  if (!datos || datos.length === 0) {
    return (
      <div className="p-6 bg-white border border-slate-200 rounded-3xl text-center text-slate-400 font-semibold">
        No hay datos para graficar.
      </div>
    );
  }

  // Dimensiones del SVG
  const width = 680;
  const height = 360;
  const paddingLeft = 70;
  const paddingRight = 30;
  const paddingTop = 40;
  const paddingBottom = 95;

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
  const renderBars = (svgWidth: number = width, svgHeight: number = height) => {
    const currentChartWidth = svgWidth - paddingLeft - paddingRight;
    const currentChartHeight = svgHeight - paddingTop - paddingBottom;
    const barWidth = currentChartWidth / datos.length;
    const spacing = Math.max(2, barWidth * 0.15);
    const itemWidth = barWidth - spacing;

    return yValues.map((yVal, index) => {
      const xVal = xValues[index];
      const barHeight = (yVal / maxY) * currentChartHeight;
      const x = paddingLeft + index * barWidth + spacing / 2;
      const y = paddingTop + currentChartHeight - barHeight;

      return (
        <g key={index} className="transition-all duration-300">
          {/* Fondo de columna activo en hover */}
          {hoveredIndex === index && (
            <rect
              x={x - spacing / 2}
              y={paddingTop}
              width={barWidth}
              height={currentChartHeight}
              fill="rgba(15, 82, 186, 0.04)"
              rx={6}
              className="pointer-events-none"
            />
          )}
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
          {/* Label truncado alineado en diagonal */}
          <text
            x={x + itemWidth / 2}
            y={svgHeight - paddingBottom + 12}
            textAnchor="end"
            className="text-[9px] fill-slate-500 font-bold font-sans"
            transform={`rotate(-45, ${x + itemWidth / 2}, ${svgHeight - paddingBottom + 12})`}
          >
            {xVal.length > 18 ? `${xVal.substring(0, 15)}...` : xVal}
          </text>
        </g>
      );
    });
  };

  // --- 2. Gráfico de Líneas ---
  const renderLines = (svgWidth: number = width, svgHeight: number = height) => {
    const currentChartWidth = svgWidth - paddingLeft - paddingRight;
    const currentChartHeight = svgHeight - paddingTop - paddingBottom;
    const step = currentChartWidth / (datos.length - 1 || 1);
    let pathD = '';
    
    yValues.forEach((yVal, index) => {
      const x = paddingLeft + index * step;
      const y = paddingTop + currentChartHeight - (yVal / maxY) * currentChartHeight;
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
          const y = paddingTop + currentChartHeight - (yVal / maxY) * currentChartHeight;
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
              {/* Label del eje X alineado en diagonal */}
              <text
                x={x}
                y={svgHeight - paddingBottom + 12}
                textAnchor="end"
                className="text-[9px] fill-slate-500 font-bold font-sans"
                transform={`rotate(-45, ${x}, ${svgHeight - paddingBottom + 12})`}
              >
                {xVal.length > 18 ? `${xVal.substring(0, 15)}...` : xVal}
              </text>
            </g>
          );
        })}
      </g>
    );
  };

  // --- 3. Gráfico de Dispersión ---
  const renderScatter = (svgWidth: number = width, svgHeight: number = height) => {
    const currentChartWidth = svgWidth - paddingLeft - paddingRight;
    const currentChartHeight = svgHeight - paddingTop - paddingBottom;
    const step = currentChartWidth / (datos.length - 1 || 1);

    return yValues.map((yVal, index) => {
      const xVal = xValues[index];
      const x = paddingLeft + index * step;
      const y = paddingTop + currentChartHeight - (yVal / maxY) * currentChartHeight;

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
          {/* Label del eje X alineado en diagonal */}
          <text
            x={x}
            y={svgHeight - paddingBottom + 12}
            textAnchor="end"
            className="text-[9px] fill-slate-500 font-bold font-sans"
            transform={`rotate(-45, ${x}, ${svgHeight - paddingBottom + 12})`}
          >
            {xVal.length > 18 ? `${xVal.substring(0, 15)}...` : xVal}
          </text>
        </g>
      );
    });
  };

  // --- 4. Gráfico de Pastel (Pie) ---
  const renderPie = (svgWidth: number = width, svgHeight: number = height) => {
    const total = yValues.reduce((sum, current) => sum + current, 0) || 1;
    let accumulatedAngle = 0;
    const centerX = svgWidth / 2;
    const centerY = svgHeight / 2;
    const radius = Math.min(svgWidth, svgHeight) * 0.28;

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

  // Renderiza el eje Y de forma independiente para el panel lateral fijo del modal
  const renderModalYAxis = (svgHeight: number = height) => {
    const lines = 4;
    const currentChartHeight = svgHeight - paddingTop - paddingBottom;
    return Array.from({ length: lines + 1 }).map((_, i) => {
      const yVal = (maxY / lines) * i;
      const y = paddingTop + currentChartHeight - (yVal / maxY) * currentChartHeight;
      return (
        <g key={i}>
          <text
            x={paddingLeft - 8}
            y={y + 4}
            textAnchor="end"
            className="text-[10px] fill-slate-400 font-bold font-sans"
          >
            {yVal.toFixed(1)}
          </text>
        </g>
      );
    });
  };

  // Renderiza solo las líneas de grilla horizontales para el panel del modal
  const renderModalGridLinesOnly = (customWidth: number, svgHeight: number = height) => {
    const lines = 4;
    const scaledChartWidth = customWidth - paddingLeft - paddingRight;
    const currentChartHeight = svgHeight - paddingTop - paddingBottom;
    return Array.from({ length: lines + 1 }).map((_, i) => {
      const yVal = (maxY / lines) * i;
      const y = paddingTop + currentChartHeight - (yVal / maxY) * currentChartHeight;
      return (
        <line
          key={i}
          x1={paddingLeft}
          y1={y}
          x2={paddingLeft + scaledChartWidth}
          y2={y}
          stroke="#E2E8F0"
          strokeWidth="1"
          strokeDasharray="4 4"
        />
      );
    });
  };

  // Controladores de eventos de arrastre manual (Pan)
  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    const container = e.currentTarget;
    setIsDragging(true);
    setStartX(e.pageX - container.offsetLeft);
    setScrollLeftStart(container.scrollLeft);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging) return;
    e.preventDefault();
    const container = e.currentTarget;
    const x = e.pageX - container.offsetLeft;
    const walk = (x - startX) * 1.5;
    container.scrollLeft = scrollLeftStart - walk;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
  };

  return (
    <div className="my-6 p-6 bg-white border border-slate-200/60 rounded-[2.5rem] shadow-xl shadow-slate-100 flex flex-col relative group max-w-full overflow-hidden select-none animate-in fade-in duration-500">
      {/* Cabecera del gráfico */}
      <div className="flex items-center justify-between mb-4 border-b border-slate-50 pb-4 shrink-0">
        <div>
          <span className="text-[10px] uppercase font-black tracking-widest text-osi-blue">Visualización de Datos</span>
          <h4 className="text-base font-black text-slate-800 tracking-tight leading-tight">{titulo}</h4>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={(e) => { e.stopPropagation(); setZoomScale(1.25); setIsModalOpen(true); }}
            className="p-3 bg-slate-50 hover:bg-osi-blue hover:text-white text-slate-400 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
            title="Maximizar Gráfico (Pantalla Completa)"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); handleDownloadSVG(); }}
            className="p-3 bg-slate-50 hover:bg-osi-blue hover:text-white text-slate-400 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
            title="Descargar SVG Vectorial"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Contenedor del SVG */}
      <div 
        onClick={() => { setZoomScale(1.25); setIsModalOpen(true); }}
        className="relative flex justify-center w-full overflow-x-auto no-scrollbar cursor-zoom-in hover:scale-[1.01] transition-transform duration-300"
      >
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

      {/* Modal Lightbox de Pantalla Completa (Zoom) */}
      {isModalOpen && (
        <div 
          onClick={() => { setIsModalOpen(false); setZoomScale(1.0); }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-6 select-none animate-in fade-in duration-200"
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            className="bg-white w-[95vw] max-w-7xl rounded-[3rem] p-8 shadow-2xl flex flex-col relative border border-slate-100 h-[88vh] overflow-hidden animate-in zoom-in-95 duration-200"
          >
            {/* Cabecera del Modal */}
            <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4 shrink-0">
              <div>
                <span className="text-[10px] uppercase font-black tracking-widest text-osi-blue">Vista Ampliada de Datos</span>
                <h4 className="text-xl font-black text-slate-800 tracking-tight leading-tight">{titulo}</h4>
              </div>
              <div className="flex items-center gap-3">
                {/* Widget de Zoom Escalonado */}
                <div className="flex items-center gap-2 bg-slate-50 border border-slate-200/60 p-1.5 px-3 rounded-2xl">
                  <button
                    onClick={() => setZoomScale(z => Math.max(0.5, z - 0.25))}
                    className="p-1 hover:bg-white hover:shadow-sm text-slate-500 hover:text-osi-blue rounded-lg transition-all cursor-pointer"
                    title="Alejar"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="text-xs font-black text-slate-600 min-w-[2.5rem] text-center select-none">
                    {Math.round(zoomScale * 100)}%
                  </span>
                  <button
                    onClick={() => setZoomScale(z => Math.min(3.0, z + 0.25))}
                    className="p-1 hover:bg-white hover:shadow-sm text-slate-500 hover:text-osi-blue rounded-lg transition-all cursor-pointer"
                    title="Acercar"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  {zoomScale !== 1.0 && (
                    <button
                      onClick={() => setZoomScale(1.0)}
                      className="p-1 px-2 hover:bg-red-50 text-red-500 hover:scale-105 rounded-lg transition-all text-[9px] font-black uppercase cursor-pointer"
                      title="Restablecer Zoom"
                    >
                      Reset
                    </button>
                  )}
                </div>

                <button
                  onClick={(e) => { e.stopPropagation(); handleDownloadSVG(); }}
                  className="p-3 bg-slate-50 hover:bg-osi-blue hover:text-white text-slate-400 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
                  title="Descargar SVG Vectorial"
                >
                  <Download className="w-4 h-4" />
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setIsModalOpen(false); setZoomScale(1.0); }}
                  className="p-3 bg-slate-100 hover:bg-red-50 hover:text-red-500 text-slate-500 rounded-2xl cursor-pointer transition-all duration-300 hover:scale-105"
                  title="Cerrar Vista Ampliada"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            {/* Contenedor del Gráfico Ampliado con Eje Y Fijo y Scroll Drag */}
            <div 
              ref={containerRef}
              className="flex-1 bg-slate-50/50 rounded-[2rem] border border-slate-100 overflow-hidden relative flex flex-row h-full"
            >
              {tipo === 'pastel' ? (
                /* Caso Pastel: Centrado y Escala Tradicional */
                <div className="flex-1 overflow-auto p-8 relative flex justify-start items-start">
                  <div 
                    style={{ 
                      width: `${width * zoomScale}px`,
                      height: `${modalHeight * zoomScale}px`,
                    }}
                    className="relative transition-all duration-300 ease-out flex justify-center items-center min-w-full min-h-full"
                  >
                    <div
                      className="transition-transform duration-300 ease-out origin-center"
                      style={{ transform: `scale(${zoomScale})` }}
                    >
                      <svg
                        width={width}
                        height={modalHeight}
                        viewBox={`0 0 ${width} ${modalHeight}`}
                        className="overflow-visible"
                      >
                        <defs>
                          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#0F52BA" />
                            <stop offset="100%" stopColor="#0039AA" />
                          </linearGradient>
                          <linearGradient id="barHoverGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#3F88C5" />
                            <stop offset="100%" stopColor="#0F52BA" />
                          </linearGradient>
                        </defs>
                        {renderPie(width, modalHeight)}
                      </svg>
                    </div>
                  </div>
                </div>
              ) : (
                /* Caso Cartesiano: Eje Y Fijo Absoluto + Contenedor Desplazable */
                <div className="relative w-full h-full flex flex-col justify-center items-center overflow-hidden">
                  {/* Eje Y Fijo Absoluto */}
                  <div 
                    className="absolute left-0 top-0 bottom-0 w-[70px] bg-white/95 backdrop-blur-sm flex items-center justify-end pr-2 border-r border-slate-200/50 shadow-[4px_0_12px_rgba(0,0,0,0.03)] z-20"
                    style={{ height: `${modalHeight}px` }}
                  >
                    <svg 
                      width={paddingLeft} 
                      height={modalHeight} 
                      className="overflow-visible"
                    >
                      {renderModalYAxis(modalHeight)}
                    </svg>
                  </div>

                  {/* Contenedor Desplazable del Plot */}
                  <div 
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseLeave}
                    className={`w-full overflow-x-auto overflow-y-hidden select-none no-scrollbar relative flex justify-start items-center ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
                    style={{ height: `${modalHeight}px` }}
                  >
                    <div 
                      style={{ 
                        width: `${width * zoomScale}px`, 
                        height: `${modalHeight}px`,
                      }}
                      className="relative transition-all duration-300 ease-out flex items-center"
                    >
                      <svg
                        width={width * zoomScale}
                        height={modalHeight}
                        viewBox={`0 0 ${width * zoomScale} ${modalHeight}`}
                        className="overflow-visible transition-all duration-300 ease-out"
                      >
                        <defs>
                          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#0F52BA" />
                            <stop offset="100%" stopColor="#0039AA" />
                          </linearGradient>
                          <linearGradient id="barHoverGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#3F88C5" />
                            <stop offset="100%" stopColor="#0F52BA" />
                          </linearGradient>
                        </defs>

                        {/* Renderizar grilla de fondo */}
                        {renderModalGridLinesOnly(width * zoomScale, modalHeight)}

                        {/* Eje X Línea Base */}
                        <line
                          x1={paddingLeft}
                          y1={modalHeight - paddingBottom}
                          x2={(width * zoomScale) - paddingRight}
                          y2={modalHeight - paddingBottom}
                          stroke="#94A3B8"
                          strokeWidth="1.5"
                        />

                        {/* Renderizar contenido escalado horizontalmente y adaptado verticalmente */}
                        {tipo === 'barras' && renderBars(width * zoomScale, modalHeight)}
                        {tipo === 'lineas' && renderLines(width * zoomScale, modalHeight)}
                        {tipo === 'dispersion' && renderScatter(width * zoomScale, modalHeight)}
                      </svg>

                      {/* Tooltip modal */}
                      {hoveredIndex !== null && (
                        <div
                          className="absolute z-30 pointer-events-none p-3 bg-slate-900 text-white rounded-2xl text-xs font-bold shadow-2xl flex flex-col items-start gap-1 border border-slate-700/50"
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
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
