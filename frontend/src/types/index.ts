/**
 * BESS EPC Engineering Spatial Viewer Types
 * 
 * [작성 의도]:
 * 3D 뷰어 씬 데이터 및 BESS 배치 장비의 타입 안정성을 보장하고
 * 런타임 오류를 방지하기 위한 정본 타입 정의 파일입니다.
 */

export type ViewerMode = 'site' | 'thermal' | 'fire' | 'smoke' | 'structure';

export type AssetKind = 'enc' | 'pcs' | 'tr' | 'tank' | 'rack' | 'ehouse' | 'bund' | 'hydrant' | 'pump_house' | 'storage' | 'basin';

export interface BESSBox {
  id?: string;
  name?: string;
  kind: AssetKind;
  x: number;      // 동쪽 좌표 (East, meters)
  y: number;      // 북쪽 좌표 (North, meters)
  z?: number;     // 지면 기준 높이 (Up, meters)
  dx: number;     // 폭 (Width, meters)
  dy: number;     // 길이 (Length, meters)
  dz: number;     // 높이 (Height, meters)
  temperature?: number; // 열해석 시 온도 (°C)
  state?: number;       // 화재 시뮬레이션 상태 코드 (0: 대기, 1: 가열, 2: 열폭주, 3: 화재, 4: 억제, 5: 소진)
}

export interface LayerVisibility {
  equipment: boolean;
  civil: boolean;
  utilities: boolean;
  fence: boolean;
  shell: boolean;
  results: boolean;
  flow: boolean;
  labels: boolean;
  baseline: boolean;
}

export interface SceneData {
  language: 'KO' | 'EN';
  mode: ViewerMode;
  size: [number, number, number]; // [W, H, Z] (meters)
  boxes: BESSBox[];
  pads?: number[][];        // 기초 패드 좌표 [x, y, z, dx, dy, dz]
  trenches?: number[][][];  // 케이블 트렌치 선분 좌표 쌍 [[x1,y1,z1], [x2,y2,z2]]
  fence?: number[][][];     // 울타리 선분
  baseline?: number[][];    // 기준안 비교 박스
  times?: number[];         // 시뮬레이션 타임스텝
  states?: number[][];      // 시뮬레이션 상태 프레임
  fields?: number[][][];    // 온도장 / 압력장 프레임
  power_blocks?: PowerBlock[]; // 파워 블록(1 PCS : N Battery) 구획
  cooling_mode?: 'air' | 'liquid'; // 냉각 시스템 아키텍처 (공랭식 vs 액랭식/냉매)
}

export interface PowerBlock {
  block: number;
  x: number;
  y: number;
  dx: number;
  dy: number;
  n_enc: number;
  pcs_label: string;
}

export interface ViewerProps {
  sceneData: SceneData;
  onSelectAsset?: (asset: BESSBox | null) => void;
  selectedAssetId?: string | null;
  className?: string;
  width?: number | string;
  height?: number | string;
}
