/**
 * BessSpatialViewer.tsx
 * 
 * [작성 의도]:
 * BESS 3D 엔지니어링 공간 배치를 렌더링하고, 상단 툴바 및 인스펙터 오버레이를 통해
 * 인터랙티브한 장비 검토를 지원하는 React 함수형 컴포넌트입니다.
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { SceneManager } from '../core/SceneManager';
import { SceneData, BESSBox, ViewerProps } from '../types';

export const BessSpatialViewer: React.FC<ViewerProps> = ({
  sceneData,
  onSelectAsset,
  className = '',
  width = '100%',
  height = '620px',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneManagerRef = useRef<SceneManager | null>(null);

  const [selectedAsset, setSelectedAsset] = useState<BESSBox | null>(null);
  const [showEdges, setShowEdges] = useState(false);
  const [showLayers, setShowLayers] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // ── Three.js 씬 인스턴스 초기화 및 해제 ──────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      const manager = new SceneManager(
        containerRef.current,
        sceneData,
        (asset) => {
          setSelectedAsset(asset);
          if (onSelectAsset) onSelectAsset(asset);
        }
      );
      sceneManagerRef.current = manager;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : '3D 뷰어 로드 실패';
      setErrorMessage(msg);
    }

    return () => {
      if (sceneManagerRef.current) {
        sceneManagerRef.current.dispose();
        sceneManagerRef.current = null;
      }
    };
  }, [sceneData, onSelectAsset]);

  // ── 뷰 프리셋 변경 핸들러 ─────────────────────────────────────────
  const handleViewPreset = useCallback((preset: 'top' | 'front' | 'fit') => {
    sceneManagerRef.current?.setViewPreset(preset);
  }, []);

  // ── 모서리선 토글 핸들러 ──────────────────────────────────────────
  const toggleEdges = useCallback(() => {
    setShowEdges((prev) => {
      const next = !prev;
      sceneManagerRef.current?.setEdgesVisible(next);
      return next;
    });
  }, []);

  // ── 스크린샷 다운로드 ─────────────────────────────────────────────
  const handleScreenshot = useCallback(() => {
    if (!sceneManagerRef.current) return;
    const dataUrl = sceneManagerRef.current.captureScreenshot();
    const link = document.createElement('a');
    link.download = `BESS_Layout_${Date.now()}.png`;
    link.href = dataUrl;
    link.click();
  }, []);

  const isKo = sceneData.language === 'KO';

  return (
    <div
      className={`relative rounded-xl overflow-hidden border border-[#30363d] bg-[#0d1117] text-[#e6edf3] font-sans ${className}`}
      style={{ width, height }}
    >
      {/* ── 1. 상단 툴바 ─────────────────────────────────────────── */}
      <div className="absolute top-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        <div className="flex items-center gap-1.5 bg-[#161b22]/90 backdrop-blur-md px-2.5 py-1.5 rounded-lg border border-[#30363d] pointer-events-auto">
          <span className="text-xs font-bold text-[#58a6ff] mr-2 flex items-center gap-1">
            ⚡ {isKo ? 'BESS 3D 배치' : 'BESS 3D Layout'}
          </span>
          <button
            onClick={() => handleViewPreset('top')}
            className="px-2 py-1 text-xs rounded hover:bg-[#21262d] transition-colors"
          >
            {isKo ? '평면도' : 'Top'}
          </button>
          <button
            onClick={() => handleViewPreset('front')}
            className="px-2 py-1 text-xs rounded hover:bg-[#21262d] transition-colors"
          >
            {isKo ? '정면도' : 'Front'}
          </button>
          <button
            onClick={() => handleViewPreset('fit')}
            className="px-2 py-1 text-xs rounded hover:bg-[#21262d] transition-colors"
          >
            {isKo ? '전체맞춤' : 'Fit'}
          </button>
          <div className="w-[1px] h-3 bg-[#30363d] mx-1" />
          <button
            onClick={toggleEdges}
            className={`px-2 py-1 text-xs rounded transition-colors ${
              showEdges ? 'bg-[#58a6ff] text-[#0d1117] font-semibold' : 'hover:bg-[#21262d]'
            }`}
          >
            {isKo ? '모서리' : 'Edges'}
          </button>
        </div>

        <div className="flex items-center gap-1.5 bg-[#161b22]/90 backdrop-blur-md px-2 py-1.5 rounded-lg border border-[#30363d] pointer-events-auto">
          <button
            onClick={handleScreenshot}
            className="px-2 py-1 text-xs rounded hover:bg-[#21262d] transition-colors flex items-center gap-1"
          >
            📸 {isKo ? '캡처' : 'PNG'}
          </button>
          <button
            onClick={() => setShowLayers((prev) => !prev)}
            className="px-2 py-1 text-xs rounded hover:bg-[#21262d] transition-colors"
          >
            ⚙️ {isKo ? '패널' : 'Panels'}
          </button>
        </div>
      </div>

      {/* ── 2. WebGL 캔버스 컨테이너 ─────────────────────────────── */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* ── 3. 에러 발생 시 알림 배너 ────────────────────────────── */}
      {errorMessage && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0d1117]/80 backdrop-blur-sm z-20">
          <div className="bg-[#161b22] border border-[#f85149] p-4 rounded-lg max-w-md text-center">
            <div className="text-[#f85149] font-bold mb-1">⚠️ 3D 뷰어 경고</div>
            <p className="text-xs text-[#8b949e]">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* ── 4. 선택 장비 인스펙터 패널 (오른쪽 오버레이) ──────────── */}
      {selectedAsset && (
        <div className="absolute bottom-3 right-3 z-10 w-64 bg-[#161b22]/95 backdrop-blur-md p-3.5 rounded-xl border border-[#30363d] shadow-xl text-xs">
          <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-[#30363d]">
            <span className="font-bold text-[#58a6ff]">
              {selectedAsset.name || (isKo ? '선택 장비 정보' : 'Asset Properties')}
            </span>
            <button
              onClick={() => setSelectedAsset(null)}
              className="text-[#8b949e] hover:text-[#e6edf3]"
            >
              ✕
            </button>
          </div>
          <div className="space-y-1.5 text-[#8b949e]">
            <div className="flex justify-between">
              <span>{isKo ? '구분' : 'Kind'}:</span>
              <span className="text-[#e6edf3] font-mono font-medium">{selectedAsset.kind.toUpperCase()}</span>
            </div>
            <div className="flex justify-between">
              <span>{isKo ? '좌표 (X, Y)' : 'Pos (X, Y)'}:</span>
              <span className="text-[#e6edf3] font-mono">{selectedAsset.x.toFixed(1)}m, {selectedAsset.y.toFixed(1)}m</span>
            </div>
            <div className="flex justify-between">
              <span>{isKo ? '치수 (L×W×H)' : 'Size'}:</span>
              <span className="text-[#e6edf3] font-mono">{selectedAsset.dx}×{selectedAsset.dy}×{selectedAsset.dz}m</span>
            </div>
            {selectedAsset.temperature !== undefined && (
              <div className="flex justify-between">
                <span>{isKo ? '온도' : 'Temp'}:</span>
                <span className="text-[#f78166] font-mono font-bold">{selectedAsset.temperature.toFixed(1)}°C</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── 5. 하단 도움말 안내문 ─────────────────────────────────── */}
      <div className="absolute bottom-2 left-3 text-[10px] text-[#8b949e] pointer-events-none bg-[#0d1117]/60 px-2 py-0.5 rounded">
        {isKo ? '마우스 좌클릭 드래그: 회전 · 우클릭: 이동 · 휠: 확대/축소' : 'Left Drag: Orbit · Right Drag: Pan · Wheel: Zoom'}
      </div>
    </div>
  );
};
