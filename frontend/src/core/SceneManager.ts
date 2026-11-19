/**
 * SceneManager.ts
 * 
 * [작성 의도]:
 * Three.js 3D 씬의 수명주기(초기화, 리사이즈, 애니메이션 루프, 메모리 해제)와
 * BESS 오브젝트 생성을 캡슐화하여 React 컴포넌트가 직접적인 WebGL/Three.js
 * 명령형 코드에 종속되지 않도록 분리한 엔진 모듈입니다.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { SceneData, BESSBox, LayerVisibility } from '../types';

export class SceneManager {
  private container: HTMLElement;
  private sceneData: SceneData;
  private renderer!: THREE.WebGLRenderer;
  private scene!: THREE.Scene;
  private camPerspective!: THREE.PerspectiveCamera;
  private camOrthographic!: THREE.OrthographicCamera;
  private activeCamera!: THREE.Camera;
  private controls!: OrbitControls;
  private animationFrameId: number | null = null;
  private isDisposed: boolean = false;

  private groups: { [key: string]: THREE.Group } = {};
  private pickables: THREE.Object3D[] = [];
  private edges: THREE.LineSegments[] = [];
  private cubeGeometry = new THREE.BoxGeometry(1, 1, 1);
  private clippingPlane!: THREE.Plane;
  private onSelectAsset?: (asset: BESSBox | null) => void;

  constructor(
    container: HTMLElement,
    sceneData: SceneData,
    onSelectAsset?: (asset: BESSBox | null) => void
  ) {
    this.container = container;
    this.sceneData = sceneData;
    this.onSelectAsset = onSelectAsset;

    this.initRenderer();
    this.initScene();
    this.initCameras();
    this.initLighting();
    this.initLayers();
    this.buildEnvironment();
    this.buildAssets();
    this.initEventListeners();
    this.startLoop();
  }

  /**
   * WebGL 렌더러 초기화 및 하드웨어 가속/컨텍스트 손실 예외 처리
   */
  private initRenderer(): void {
    try {
      this.renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        preserveDrawingBuffer: true,
      });
    } catch (err) {
      console.error('[SceneManager] WebGL 초기화 실패:', err);
      throw new Error('이 브라우저/환경에서 WebGL을 초기화할 수 없습니다.');
    }

    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.7));
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    this.renderer.localClippingEnabled = true;

    this.container.appendChild(this.renderer.domElement);

    // GPU 컨텍스트 복구 핸들러
    this.renderer.domElement.addEventListener('webglcontextlost', (e) => {
      e.preventDefault();
      console.warn('[SceneManager] WebGL 컨텍스트 손실 발생');
    });
  }

  private initScene(): void {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color('#0d1117'); // Dark theme 배경
    const span = Math.max(...this.sceneData.size);
    this.scene.fog = new THREE.Fog('#0d1117', span * 3, span * 10);
    this.clippingPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), this.sceneData.size[2] + 1);
  }

  private initCameras(): void {
    const [W, H, Z] = this.sceneData.size;
    const span = Math.max(W, H, Z);
    const aspect = this.container.clientWidth / Math.max(this.container.clientHeight, 1);

    this.camPerspective = new THREE.PerspectiveCamera(42, aspect, 0.05, span * 30 + 100);
    this.camPerspective.position.set(W * 1.2, span * 1.5, H * 1.2);

    this.camOrthographic = new THREE.OrthographicCamera(
      -span * aspect, span * aspect, span, -span, 0.05, span * 30 + 100
    );

    this.activeCamera = this.camPerspective;
    this.controls = new OrbitControls(this.activeCamera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxPolarAngle = Math.PI * 0.49;
    this.controls.target.set(W / 2, 0, -H / 2);
    this.controls.update();
  }

  private initLighting(): void {
    const [W, H, Z] = this.sceneData.size;
    const span = Math.max(W, H, Z);

    const hemiLight = new THREE.HemisphereLight('#e6f6ff', '#21262d', 2.0);
    this.scene.add(hemiLight);

    const sun = new THREE.DirectionalLight('#fff2d5', 3.0);
    sun.position.set(-span * 0.35, span * 1.2, -span * 0.65);
    sun.target.position.set(W / 2, 0, -H / 2);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.near = 0.1;
    sun.shadow.camera.far = span * 5 + 20;
    sun.shadow.bias = -0.00015;

    this.scene.add(sun);
    this.scene.add(sun.target);
  }

  private initLayers(): void {
    const layerNames = ['equipment', 'civil', 'utilities', 'fence', 'shell', 'results', 'flow', 'labels', 'baseline'];
    layerNames.forEach((name) => {
      const group = new THREE.Group();
      this.groups[name] = group;
      this.scene.add(group);
    });
  }

  private buildEnvironment(): void {
    const [W, H] = this.sceneData.size;
    const groundGeo = new THREE.PlaneGeometry(W * 1.8, H * 1.8);
    const groundMat = new THREE.MeshStandardMaterial({
      color: '#161b22',
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(W / 2, -0.05, -H / 2);
    ground.receiveShadow = true;
    this.groups.civil.add(ground);

    const grid = new THREE.GridHelper(Math.max(W, H) * 1.5, 40, '#30363d', '#21262d');
    grid.position.set(W / 2, -0.02, -H / 2);
    this.groups.civil.add(grid);
  }

  private buildAssets(): void {
    const { boxes } = this.sceneData;

    boxes.forEach((boxData) => {
      const { x, y, dx, dy, dz, kind } = boxData;
      let color = '#f8fafc'; // 기본: 배터리 인클로저 (클린 화이트)
      let edgeColor = '#2ea44f';
      if (kind === 'pcs') {
        color = '#1565c0'; // PCS/MV 스키드: 딥 일렉트릭 블루
        edgeColor = '#0d47a1';
      }
      else if (kind === 'tr') color = '#e3b341';
      else if (kind === 'tank') color = '#79c0ff';
      else if (kind === 'rack') color = '#a371f7';
      else if (kind === 'ehouse') color = '#00b4d8';
      else if (kind === 'bund') color = '#6c757d';
      else if (kind === 'hydrant') color = '#e63946';
      else if (kind === 'pump_house') color = '#d90429';
      else if (kind === 'storage') color = '#4a5568';
      else if (kind === 'basin') color = '#2a9d8f';

      const mat = new THREE.MeshStandardMaterial({
        color,
        roughness: kind === 'pcs' ? 0.45 : 0.75,
        metalness: kind === 'pcs' ? 0.35 : 0.15,
        clippingPlanes: [this.clippingPlane],
      });

      const mesh = new THREE.Mesh(this.cubeGeometry, mat);
      // Python 좌표계(x East, y North, z Up) -> Three.js (x Right, y Up, z Forward/Back)
      mesh.position.set(x + dx / 2, dz / 2, -y - dy / 2);
      mesh.scale.set(dx, dz, dy);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData.bessAsset = boxData;

      this.groups.equipment.add(mesh);
      this.pickables.push(mesh);

      // 모서리 외곽선 생성
      const edgeGeo = new THREE.EdgesGeometry(this.cubeGeometry);
      const edgeMat = new THREE.LineBasicMaterial({ color: edgeColor, transparent: true, opacity: 0.65 });
      const edgeMesh = new THREE.LineSegments(edgeGeo, edgeMat);
      edgeMesh.position.copy(mesh.position);
      edgeMesh.scale.copy(mesh.scale);
      this.groups.equipment.add(edgeMesh);
      this.edges.push(edgeMesh);

      // PCS 상부 3상 고전압 연계 부싱
      if (kind === 'pcs') {
        for (let i = 0; i < 3; i++) {
          const bushGeo = new THREE.CylinderGeometry(dx * 0.022, dx * 0.035, dz * 0.22, 12);
          const bushMat = new THREE.MeshStandardMaterial({ color: '#8d6e63' });
          const bush = new THREE.Mesh(bushGeo, bushMat);
          bush.position.set(x + dx * (0.22 + i * 0.16), dz + dz * 0.11, -y - dy * 0.5);
          this.groups.equipment.add(bush);
        }
      }

      // 소화전 40m 방수 반경 원형 링 (NFPA 24)
      if (kind === 'hydrant') {
        const ringGeo = new THREE.RingGeometry(39.85, 40.0, 64);
        const ringMat = new THREE.MeshBasicMaterial({
          color: '#e63946',
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.6,
        });
        const ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.rotation.x = -Math.PI / 2;
        ringMesh.position.set(x + dx / 2, 0.025, -y - dy / 2);
        this.groups.utilities.add(ringMesh);
      }
    });

    // 파워 블록(Power Block: 1 PCS + N Battery) 바닥 구획선 렌더링
    if (this.sceneData.power_blocks && this.sceneData.power_blocks.length > 0) {
      this.sceneData.power_blocks.forEach((pb) => {
        const lineGeo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(pb.x, 0.02, -pb.y),
          new THREE.Vector3(pb.x + pb.dx, 0.02, -pb.y),
          new THREE.Vector3(pb.x + pb.dx, 0.02, -pb.y - pb.dy),
          new THREE.Vector3(pb.x, 0.02, -pb.y - pb.dy),
          new THREE.Vector3(pb.x, 0.02, -pb.y),
        ]);
        const lineMat = new THREE.LineBasicMaterial({ color: '#1f6feb', transparent: true, opacity: 0.6 });
        const line = new THREE.Line(lineGeo, lineMat);
        this.groups.civil.add(line);
      });
    }
  }

  private initEventListeners(): void {
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    this.renderer.domElement.addEventListener('click', (event) => {
      const rect = this.renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, this.activeCamera);
      const intersects = raycaster.intersectObjects(this.pickables, false);

      if (intersects.length > 0) {
        const hit = intersects[0].object;
        const asset = hit.userData.bessAsset as BESSBox;
        if (this.onSelectAsset) this.onSelectAsset(asset);
      } else {
        if (this.onSelectAsset) this.onSelectAsset(null);
      }
    });

    window.addEventListener('resize', this.onResize);
  }

  private onResize = (): void => {
    if (!this.container || this.isDisposed) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    const aspect = width / Math.max(height, 1);

    if (this.activeCamera === this.camPerspective) {
      this.camPerspective.aspect = aspect;
      this.camPerspective.updateProjectionMatrix();
    } else {
      const span = Math.max(...this.sceneData.size);
      this.camOrthographic.left = -span * aspect;
      this.camOrthographic.right = span * aspect;
      this.camOrthographic.updateProjectionMatrix();
    }

    this.renderer.setSize(width, height);
  };

  private startLoop(): void {
    const animate = () => {
      if (this.isDisposed) return;
      this.animationFrameId = requestAnimationFrame(animate);
      this.controls.update();
      this.renderer.render(this.scene, this.activeCamera);
    };
    animate();
  }

  // ── Public API ────────────────────────────────────────────────────────

  public setViewPreset(preset: 'top' | 'front' | 'fit'): void {
    const [W, H, Z] = this.sceneData.size;
    const span = Math.max(W, H, Z);
    const target = new THREE.Vector3(W / 2, 0, -H / 2);

    if (preset === 'top') {
      this.activeCamera = this.camOrthographic;
      this.activeCamera.position.set(W / 2, span * 2, -H / 2);
      this.controls.object = this.activeCamera;
      this.controls.target.copy(target);
    } else if (preset === 'front') {
      this.activeCamera = this.camPerspective;
      this.activeCamera.position.set(W / 2, Z * 2, H * 1.5);
      this.controls.object = this.activeCamera;
      this.controls.target.copy(target);
    } else if (preset === 'fit') {
      this.activeCamera = this.camPerspective;
      this.activeCamera.position.set(W * 1.2, span * 1.5, H * 1.2);
      this.controls.object = this.activeCamera;
      this.controls.target.copy(target);
    }
    this.controls.update();
  }

  public setEdgesVisible(visible: boolean): void {
    this.edges.forEach((edge) => (edge.visible = visible));
  }

  public setLayerVisibility(layers: Partial<LayerVisibility>): void {
    Object.entries(layers).forEach(([name, visible]) => {
      if (this.groups[name] && visible !== undefined) {
        this.groups[name].visible = visible;
      }
    });
  }

  public captureScreenshot(): string {
    return this.renderer.domElement.toDataURL('image/png');
  }

  /**
   * 컴포넌트 언마운트 시 Three.js 메모리 및 이벤트 누수 완전 해제
   */
  public dispose(): void {
    this.isDisposed = true;
    if (this.animationFrameId !== null) {
      cancelAnimationFrame(this.animationFrameId);
    }
    window.removeEventListener('resize', this.onResize);

    this.controls.dispose();
    this.cubeGeometry.dispose();
    this.scene.clear();
    this.renderer.dispose();

    if (this.renderer.domElement.parentElement) {
      this.renderer.domElement.parentElement.removeChild(this.renderer.domElement);
    }
  }
}
