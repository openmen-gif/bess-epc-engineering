/**
 * BESS EPC Engineering Backend-for-Frontend (BFF) Node.js Server
 * 
 * [작성 의도]:
 * React 프론트엔드와 BESS 엔지니어링 계산 엔진 간의 통신을 중계하고
 * 프로젝트 배치 데이터, 전압강하, 배터리 증설 시뮬레이션을 REST API로 제공하는
 * Node.js (TypeScript) 기반 경량 서비스입니다.
 */

import * as http from 'http';
import { SceneData, BESSBox } from '../src/types/index.js';

export interface SizingRequest {
  powerMw: number;
  durationHours: number;
  market: string;
  voltageKv: number;
  cableLengthM: number;
}

export interface SizingResponse {
  energyMwh: number;
  numContainers: number;
  numPcs: number;
  recommendedCableMm2: number;
  vdropPct: number;
  ventAreaM2: number;
}

/**
 * 3D 뷰어용 기본 배치 씬 데이터 생성 (샘플 100MW / 400MWh BESS 프로젝트)
 */
export function generateSampleSceneData(numContainers = 20, numPcs = 5): SceneData {
  const boxes: BESSBox[] = [];
  const encDx = 6.05;
  const encDy = 2.44;
  const encDz = 2.9;

  // 1. 배터리 인클로저 배치 (2열 그리드)
  const cols = Math.ceil(numContainers / 2);
  let count = 0;
  for (let r = 0; r < 2; r++) {
    for (let c = 0; c < cols; c++) {
      if (count >= numContainers) break;
      boxes.push({
        id: `enc-${count + 1}`,
        name: `Battery Enclosure #${count + 1}`,
        kind: 'enc',
        x: c * (encDx + 3.0),
        y: r * (encDy + 5.0),
        dx: encDx,
        dy: encDy,
        dz: encDz,
        temperature: 24.5 + Math.random() * 2.0,
      });
      count++;
    }
  }

  // 2. PCS 스키드 배치
  for (let p = 0; p < numPcs; p++) {
    boxes.push({
      id: `pcs-${p + 1}`,
      name: `PCS / MV Skid #${p + 1}`,
      kind: 'pcs',
      x: p * (encDx + 3.0) * (cols / numPcs),
      y: 18.0,
      dx: 6.05,
      dy: 2.44,
      dz: 2.8,
    });
  }

  // 3. 변압기 및 소방 수조, E-House (MV 수배전반 / EMS 제어실)
  boxes.push({
    id: 'tr-main',
    name: 'Main POI Transformer (120 MVA)',
    kind: 'tr',
    x: cols * (encDx + 3.0) + 5.0,
    y: 9.0,
    dx: 8.0,
    dy: 6.0,
    dz: 4.5,
  });

  boxes.push({
    id: 'ehouse-main',
    name: 'E-House (MV Switchgear & EMS/SCADA, 40ft HC)',
    kind: 'ehouse',
    x: cols * (encDx + 3.0) + 5.0,
    y: 18.0,
    dx: 12.19,
    dy: 2.44,
    dz: 2.9,
  });

  boxes.push({
    id: 'tank-fire',
    name: 'NFPA 750 Fire Water Tank (540 m³)',
    kind: 'tank',
    x: -8.0,
    y: 5.0,
    dx: 5.0,
    dy: 5.0,
    dz: 4.0,
  });

  const width = cols * (encDx + 3.0) + 18.0;
  const height = 28.0;

  return {
    language: 'KO',
    mode: 'site',
    size: [Math.ceil(width), Math.ceil(height), 8.0],
    boxes,
  };
}

/**
 * Node.js HTTP REST API 서버 핸들러
 */
export function createBffServer(port = 4000): http.Server {
  const server = http.createServer((req: http.IncomingMessage, res: http.ServerResponse) => {
    // CORS 헤더 설정
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);

    // GET /api/health
    if (req.method === 'GET' && url.pathname === '/api/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'ok', service: 'bess-epc-bff', timestamp: new Date().toISOString() }));
      return;
    }

    // GET /api/project/layout
    if (req.method === 'GET' && url.pathname === '/api/project/layout') {
      const numEnc = parseInt(url.searchParams.get('enc') || '20', 10);
      const numPcs = parseInt(url.searchParams.get('pcs') || '5', 10);
      const sceneData = generateSampleSceneData(numEnc, numPcs);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(sceneData));
      return;
    }

    // 404 Not Found
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Endpoint Not Found' }));
  });

  return server;
}

// 직접 실행 시 로컬 포트 바인딩 (CLI 실행)
const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 4000;
if (process.env.NODE_ENV !== 'test' && !process.env.BESS_NO_LISTEN) {
  const server = createBffServer(PORT);
  server.listen(PORT, () => {
    console.log(`[BESS BFF Server] Listening on http://localhost:${PORT}`);
  });
}
