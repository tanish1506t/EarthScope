/**
 * EarthScope 3D Interactive WebGL Globe (Ultra 3D & Dynamic Edition)
 * Three.js Planetary Simulation with Geodetic Coordinates Grid, Dual Satellites,
 * Holographic Target Reticle, Atmospheric Shader, Clouds, City Lights & Mouse Parallax
 * NASA Space Apps Challenge 2026 | Team CodeRex
 */

class EarthScopeGlobe {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.options = Object.assign({
      radius: 100,
      autoRotate: true,
      autoRotateSpeed: 0.0018,
      interactive: true,
      onLocationSelect: null
    }, options);

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.earthGroup = null;
    this.earthMesh = null;
    this.cloudMesh = null;
    this.atmosphereMesh = null;
    this.pinsGroup = null;
    this.satelliteGroup = null;
    this.polarSatGroup = null;
    this.starfield = null;
    this.gridGroup = null;
    this.targetReticle = null;

    this.isDragging = false;
    this.previousMousePosition = { x: 0, y: 0 };
    this.targetRotation = { x: 0.3, y: 0 };
    this.currentRotation = { x: 0.3, y: 0 };
    this.targetZoom = 280;
    this.currentZoom = 280;
    this.minZoom = 145;
    this.maxZoom = 460;
    this.parallaxMouse = { x: 0, y: 0 };

    this.locations = [];
    this.activeLocationId = null;
    this.raycaster = null;
    this.mouse = null;
    this.animationFrameId = null;

    this.init();
  }

  hasWebGL() {
    try {
      const canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    } catch (e) {
      return false;
    }
  }

  init() {
    if (!this.hasWebGL() || typeof THREE === 'undefined') {
      this.renderFallback();
      return;
    }

    const width = this.container.clientWidth || 300;
    const height = this.container.clientHeight || 300;

    // 1. Scene & Camera
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 1, 3000);
    this.camera.position.z = this.currentZoom;

    // 2. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.container.appendChild(this.renderer.domElement);

    // 3. Central Earth Group
    this.earthGroup = new THREE.Group();
    this.scene.add(this.earthGroup);

    // 4. Earth Sphere with Procedural Planetary Surface Map & Night City Lights
    const earthGeo = new THREE.SphereGeometry(this.options.radius, 64, 64);
    const earthTexture = this.generateEarthTexture();
    const bumpTexture = this.generateBumpTexture();

    const earthMat = new THREE.MeshPhongMaterial({
      map: earthTexture,
      bumpMap: bumpTexture,
      bumpScale: 2.2,
      specular: new THREE.Color(0x1a4570),
      shininess: 28
    });
    this.earthMesh = new THREE.Mesh(earthGeo, earthMat);
    this.earthGroup.add(this.earthMesh);

    // 5. Geodetic Coordinate Wireframe Grid
    this.createGeodeticGrid();

    // 6. Cloud Layer with Differential Spin
    const cloudGeo = new THREE.SphereGeometry(this.options.radius * 1.018, 48, 48);
    const cloudTexture = this.generateCloudTexture();
    const cloudMat = new THREE.MeshLambertMaterial({
      map: cloudTexture,
      transparent: true,
      opacity: 0.42,
      blending: THREE.AdditiveBlending
    });
    this.cloudMesh = new THREE.Mesh(cloudGeo, cloudMat);
    this.earthGroup.add(this.cloudMesh);

    // 7. Atmospheric Fresnel Rim Glow Shader
    const atmosGeo = new THREE.SphereGeometry(this.options.radius * 1.048, 48, 48);
    const atmosMat = new THREE.ShaderMaterial({
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.72 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
          gl_FragColor = vec4(0.0, 0.92, 1.0, 1.0) * intensity * 0.95;
        }
      `,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      transparent: true
    });
    this.atmosphereMesh = new THREE.Mesh(atmosGeo, atmosMat);
    this.earthGroup.add(this.atmosphereMesh);

    // 8. Dynamic 3D Holographic Target Reticle
    this.createTargetReticle();

    // 9. Starfield Particle Matrix
    this.createStarfield();

    // 10. Dual Satellites (ISS Equatorial + Polar Sun-Synchronous Observer)
    this.createDualSatellites();

    // 11. Coordinate Pins Group
    this.pinsGroup = new THREE.Group();
    this.earthGroup.add(this.pinsGroup);

    // 12. Dynamic Lighting
    const ambientLight = new THREE.AmbientLight(0x384c6e, 0.9);
    this.scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.5);
    sunLight.position.set(450, 220, 320);
    this.scene.add(sunLight);

    const rimLight = new THREE.DirectionalLight(0x00f0ff, 0.55);
    rimLight.position.set(-450, -220, -320);
    this.scene.add(rimLight);

    // 13. Raycaster & Mouse
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    // 14. Event Listeners
    if (this.options.interactive) {
      this.setupInteractionListeners();
    }

    window.addEventListener('resize', () => this.onWindowResize());

    // 15. Start Render Animation Loop
    this.animate();
  }

  // Geodetic Coordinate Wireframe Grid (Latitude & Longitude Measurement Rings)
  createGeodeticGrid() {
    this.gridGroup = new THREE.Group();
    const r = this.options.radius * 1.008;

    // Equator Ring (Highlighted Neon Cyan)
    const eqCurve = new THREE.EllipseCurve(0, 0, r, r, 0, 2 * Math.PI, false, 0);
    const eqPoints = eqCurve.getPoints(90);
    const eqGeo = new THREE.BufferGeometry().setFromPoints(eqPoints.map(p => new THREE.Vector3(p.x, 0, p.y)));
    const eqMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.5 });
    const eqLine = new THREE.Line(eqGeo, eqMat);
    this.gridGroup.add(eqLine);

    // Latitudinal Parallel Rings
    [-45, -30, 30, 45].forEach(latDeg => {
      const phi = (90 - latDeg) * (Math.PI / 180);
      const ringR = r * Math.sin(phi);
      const ringY = r * Math.cos(phi);
      const ringCurve = new THREE.EllipseCurve(0, 0, ringR, ringR, 0, 2 * Math.PI, false, 0);
      const pts = ringCurve.getPoints(60);
      const geo = new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(p.x, ringY, p.y)));
      const mat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.18 });
      this.gridGroup.add(new THREE.Line(geo, mat));
    });

    // Meridians (Longitudinal Rings)
    for (let lon = 0; lon < 180; lon += 45) {
      const mCurve = new THREE.EllipseCurve(0, 0, r, r, 0, 2 * Math.PI, false, 0);
      const mPts = mCurve.getPoints(90);
      const mGeo = new THREE.BufferGeometry().setFromPoints(mPts.map(p => new THREE.Vector3(p.x, p.y, 0)));
      const mMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.15 });
      const mLine = new THREE.Line(mGeo, mMat);
      mLine.rotation.y = lon * (Math.PI / 180);
      this.gridGroup.add(mLine);
    }

    this.earthGroup.add(this.gridGroup);
  }

  // 3D Holographic Reticle that locks onto the active city
  createTargetReticle() {
    this.targetReticle = new THREE.Group();
    this.targetReticle.visible = false;

    // Spinning Outer Ring with Tick Marks
    const outerGeo = new THREE.RingGeometry(3.5, 4.2, 32);
    const outerMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, side: THREE.DoubleSide, transparent: true, opacity: 0.85 });
    this.reticleOuter = new THREE.Mesh(outerGeo, outerMat);
    this.targetReticle.add(this.reticleOuter);

    // Pulsing Inner Target Circle
    const innerGeo = new THREE.RingGeometry(1.6, 2.2, 24);
    const innerMat = new THREE.MeshBasicMaterial({ color: 0xff0055, side: THREE.DoubleSide, transparent: true, opacity: 0.9 });
    this.reticleInner = new THREE.Mesh(innerGeo, innerMat);
    this.targetReticle.add(this.reticleInner);

    // Crosshairs
    const chGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-5, 0, 0), new THREE.Vector3(5, 0, 0),
      new THREE.Vector3(0, -5, 0), new THREE.Vector3(0, 5, 0)
    ]);
    const chMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.6 });
    this.reticleCross = new THREE.LineSegments(chGeo, chMat);
    this.targetReticle.add(this.reticleCross);

    this.earthGroup.add(this.targetReticle);
  }

  // Converts Geographic Lat/Lon to 3D Cartesian coordinates on sphere
  latLonToVector3(lat, lon, radius = this.options.radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);

    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);

    return new THREE.Vector3(x, y, z);
  }

  setLocations(locationsList) {
    this.locations = locationsList;
    if (!this.pinsGroup) return;

    // Clear existing pins
    while (this.pinsGroup.children.length > 0) {
      this.pinsGroup.remove(this.pinsGroup.children[0]);
    }

    const r = this.options.radius;
    locationsList.forEach((loc) => {
      const pos = this.latLonToVector3(loc.lat, loc.lon, r * 1.005);
      
      const pinObj = new THREE.Group();
      pinObj.position.copy(pos);
      pinObj.userData = loc;

      // Orient pin outward along surface normal
      pinObj.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), pos.clone().normalize());

      // Glowing Base Ring
      const ringGeo = new THREE.RingGeometry(1.2, 2.8, 24);
      const ringMat = new THREE.MeshBasicMaterial({
        color: loc.featured ? 0xff0055 : 0x00f0ff,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.85
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = Math.PI / 2;
      pinObj.add(ringMesh);

      // Vertical Marker Beam (Light Tower)
      const beamGeo = new THREE.CylinderGeometry(0.5, 0.5, 9, 12);
      const beamMat = new THREE.MeshBasicMaterial({
        color: loc.featured ? 0xff0055 : 0x38bdf8,
        transparent: true,
        opacity: 0.92
      });
      const beamMesh = new THREE.Mesh(beamGeo, beamMat);
      beamMesh.position.y = 4.5;
      pinObj.add(beamMesh);

      // Top Pulsing Beacon Head
      const headGeo = new THREE.SphereGeometry(1.8, 16, 16);
      const headMat = new THREE.MeshBasicMaterial({
        color: loc.featured ? 0xffdd00 : 0x00f0ff
      });
      const headMesh = new THREE.Mesh(headGeo, headMat);
      headMesh.position.y = 9.0;
      pinObj.add(headMesh);

      this.pinsGroup.add(pinObj);
    });

    if (this.activeLocationId) {
      this.highlightLocation(this.activeLocationId);
    }
  }

  highlightLocation(locationId) {
    this.activeLocationId = locationId;
    const loc = this.locations.find(l => l.id.toLowerCase() === locationId.toLowerCase());
    if (!loc || !this.targetReticle) return;

    const pos = this.latLonToVector3(loc.lat, loc.lon, this.options.radius * 1.018);
    this.targetReticle.position.copy(pos);
    this.targetReticle.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), pos.clone().normalize());
    this.targetReticle.visible = true;
  }

  flyToLocation(lat, lon) {
    const targetY = -((lon + 90) * (Math.PI / 180));
    const targetX = (lat * (Math.PI / 180));
    this.targetRotation.y = targetY;
    this.targetRotation.x = targetX;
    this.targetZoom = 210;

    // Find and highlight reticle
    const loc = this.locations.find(l => Math.abs(l.lat - lat) < 0.1 && Math.abs(l.lon - lon) < 0.1);
    if (loc) {
      this.highlightLocation(loc.id);
    }
  }

  createStarfield() {
    const starsGeo = new THREE.BufferGeometry();
    const starCount = 1600;
    const positions = new Float32Array(starCount * 3);
    const colors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      const radius = 650 + Math.random() * 500;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);

      positions[i] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i + 2] = radius * Math.cos(phi);

      // Varied cyan, violet, and crisp white star hues
      const hueChoice = Math.random();
      if (hueChoice > 0.7) {
        colors[i] = 0.2; colors[i + 1] = 0.9; colors[i + 2] = 1.0; // Cyan
      } else if (hueChoice > 0.4) {
        colors[i] = 0.8; colors[i + 1] = 0.5; colors[i + 2] = 1.0; // Violet
      } else {
        colors[i] = 0.95; colors[i + 1] = 0.95; colors[i + 2] = 1.0; // White
      }
    }

    starsGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    starsGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const starMat = new THREE.PointsMaterial({
      size: 2.2,
      vertexColors: true,
      transparent: true,
      opacity: 0.85
    });

    this.starfield = new THREE.Points(starsGeo, starMat);
    this.scene.add(this.starfield);
  }

  createDualSatellites() {
    // 1. ISS Equatorial Satellite
    this.satelliteGroup = new THREE.Group();
    const rOrbit = this.options.radius * 1.35;

    const orbitCurve = new THREE.EllipseCurve(0, 0, rOrbit, rOrbit * 0.92, 0, 2 * Math.PI, false, 0);
    const points = orbitCurve.getPoints(100);
    const orbitGeo = new THREE.BufferGeometry().setFromPoints(points.map(p => new THREE.Vector3(p.x, 0, p.y)));
    const orbitMat = new THREE.LineBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.25 });
    const orbitLine = new THREE.Line(orbitGeo, orbitMat);
    orbitLine.rotation.x = Math.PI / 3.2;
    orbitLine.rotation.z = Math.PI / 5.5;
    this.satelliteGroup.add(orbitLine);

    const satGeo = new THREE.BoxGeometry(2.2, 1.2, 1.2);
    const satMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    this.satMesh = new THREE.Mesh(satGeo, satMat);

    const panelGeo = new THREE.BoxGeometry(6, 0.2, 1.6);
    const panelMat = new THREE.MeshBasicMaterial({ color: 0x00a8ff });
    this.satMesh.add(new THREE.Mesh(panelGeo, panelMat));

    this.satOrbitRadius = rOrbit;
    this.satOrbitAngle = 0;
    this.satelliteGroup.add(this.satMesh);
    this.earthGroup.add(this.satelliteGroup);

    // 2. Polar Sun-Synchronous Earth Observation Satellite (Landsat-9 / Terra)
    this.polarSatGroup = new THREE.Group();
    const rPolar = this.options.radius * 1.45;
    const polarCurve = new THREE.EllipseCurve(0, 0, rPolar, rPolar, 0, 2 * Math.PI, false, 0);
    const polarPts = polarCurve.getPoints(100);
    const polarGeo = new THREE.BufferGeometry().setFromPoints(polarPts.map(p => new THREE.Vector3(p.x, p.y, 0)));
    const polarLine = new THREE.Line(polarGeo, new THREE.LineBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.2 }));
    polarLine.rotation.y = Math.PI / 4;
    this.polarSatGroup.add(polarLine);

    this.polarSatMesh = new THREE.Mesh(
      new THREE.SphereGeometry(1.4, 12, 12),
      new THREE.MeshBasicMaterial({ color: 0x10b981 })
    );
    this.polarSatRadius = rPolar;
    this.polarSatAngle = Math.PI;
    this.polarSatGroup.add(this.polarSatMesh);
    this.earthGroup.add(this.polarSatGroup);
  }

  // Generates offline 2048x1024 planetary canvas map with continents, oceans, and golden city lights
  generateEarthTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    // Deep ocean base
    const oceanGrad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    oceanGrad.addColorStop(0, '#041733');
    oceanGrad.addColorStop(0.5, '#07244d');
    oceanGrad.addColorStop(1, '#041733');
    ctx.fillStyle = oceanGrad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw continent silhouettes
    ctx.fillStyle = '#1c4a3b';
    ctx.strokeStyle = '#296b55';
    ctx.lineWidth = 1.8;

    this.drawContinentBlob(ctx, 1150, 400, 380, 260); // Eurasia
    this.drawContinentBlob(ctx, 1100, 580, 220, 280); // Africa
    this.drawContinentBlob(ctx, 1480, 720, 160, 140); // Australia
    this.drawContinentBlob(ctx, 420, 360, 280, 240);  // North America
    this.drawContinentBlob(ctx, 560, 680, 190, 280);  // South America
    this.drawContinentBlob(ctx, 750, 180, 120, 90);   // Greenland
    this.drawContinentBlob(ctx, 1550, 340, 80, 140);  // Japan
    this.drawContinentBlob(ctx, 1380, 550, 140, 90);  // Southeast Asia / India

    // Mountain ranges / interior arid shading
    ctx.fillStyle = '#3a5933';
    this.drawContinentBlob(ctx, 1240, 370, 180, 100);
    this.drawContinentBlob(ctx, 430, 370, 60, 180);

    // Desert regions
    ctx.fillStyle = '#6e5a32';
    this.drawContinentBlob(ctx, 1080, 500, 160, 70); // Sahara
    this.drawContinentBlob(ctx, 1220, 480, 90, 60);  // Middle East
    this.drawContinentBlob(ctx, 1480, 720, 100, 70); // Australia

    // Polar Ice Caps
    ctx.fillStyle = '#d4ebf7';
    ctx.fillRect(0, 0, canvas.width, 48);
    ctx.fillRect(0, canvas.height - 70, canvas.width, 70);

    // Golden Night City Light Clusters (Glow points)
    ctx.fillStyle = 'rgba(255, 220, 100, 0.85)';
    const cityCoordinates = [
      [1130, 330], [1160, 340], [1180, 350], [1210, 360], // Europe
      [1370, 520], [1390, 530], [1400, 540], // India
      [1540, 380], [1520, 410], // East Asia & Tokyo
      [480, 380], [490, 390], [500, 400], [440, 390], // North America
      [580, 730], [590, 750] // South America
    ];
    cityCoordinates.forEach(([cx, cy]) => {
      for (let i = 0; i < 6; i++) {
        const ox = (Math.random() - 0.5) * 35;
        const oy = (Math.random() - 0.5) * 25;
        ctx.beginPath();
        ctx.arc(cx + ox, cy + oy, Math.random() * 1.6 + 0.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
  }

  generateBumpTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#666666';
    this.drawContinentBlob(ctx, 570, 200, 190, 130);
    this.drawContinentBlob(ctx, 550, 290, 110, 140);
    this.drawContinentBlob(ctx, 210, 180, 140, 120);
    this.drawContinentBlob(ctx, 280, 340, 95, 140);

    return new THREE.CanvasTexture(canvas);
  }

  generateCloudTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(0,0,0,0)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Swirling atmospheric cloud streaks
    ctx.fillStyle = 'rgba(255, 255, 255, 0.72)';
    for (let i = 0; i < 55; i++) {
      const cx = Math.random() * canvas.width;
      const cy = 60 + Math.random() * (canvas.height - 120);
      const rx = 40 + Math.random() * 140;
      const ry = 10 + Math.random() * 40;
      ctx.beginPath();
      ctx.ellipse(cx, cy, rx, ry, Math.random() * 0.4 - 0.2, 0, Math.PI * 2);
      ctx.fill();
    }

    return new THREE.CanvasTexture(canvas);
  }

  drawContinentBlob(ctx, x, y, w, h) {
    ctx.beginPath();
    ctx.ellipse(x, y, w / 2, h / 2, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  setupInteractionListeners() {
    const dom = this.renderer.domElement;

    dom.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    dom.addEventListener('mousemove', (e) => {
      const rect = dom.getBoundingClientRect();
      this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      // Parallax offset
      this.parallaxMouse.x = this.mouse.x * 12;
      this.parallaxMouse.y = this.mouse.y * 12;

      if (this.isDragging) {
        const deltaX = e.clientX - this.previousMousePosition.x;
        const deltaY = e.clientY - this.previousMousePosition.y;

        this.targetRotation.y += deltaX * 0.005;
        this.targetRotation.x += deltaY * 0.005;
        this.targetRotation.x = Math.max(-1.4, Math.min(1.4, this.targetRotation.x));

        this.previousMousePosition = { x: e.clientX, y: e.clientY };
      } else {
        this.checkPinHover();
      }
    });

    dom.addEventListener('click', () => {
      this.checkPinClick();
    });

    // Touch support for mobile devices
    let initialTouchDist = 0;
    dom.addEventListener('touchstart', (e) => {
      if (e.touches.length === 1) {
        this.isDragging = true;
        this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      } else if (e.touches.length === 2) {
        initialTouchDist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
      }
    }, { passive: true });

    dom.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1 && this.isDragging) {
        const deltaX = e.touches[0].clientX - this.previousMousePosition.x;
        const deltaY = e.touches[0].clientY - this.previousMousePosition.y;

        this.targetRotation.y += deltaX * 0.006;
        this.targetRotation.x += deltaY * 0.006;
        this.targetRotation.x = Math.max(-1.4, Math.min(1.4, this.targetRotation.x));

        this.previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      } else if (e.touches.length === 2) {
        const dist = Math.hypot(
          e.touches[0].clientX - e.touches[1].clientX,
          e.touches[0].clientY - e.touches[1].clientY
        );
        const factor = (initialTouchDist - dist) * 0.4;
        this.targetZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.targetZoom + factor));
        initialTouchDist = dist;
      }
    }, { passive: true });

    dom.addEventListener('touchend', () => {
      this.isDragging = false;
    });

    dom.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.targetZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.targetZoom + e.deltaY * 0.25));
    }, { passive: false });
  }

  checkPinHover() {
    if (!this.pinsGroup || !this.camera) return;
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.pinsGroup.children, true);
    
    if (intersects.length > 0) {
      this.renderer.domElement.style.cursor = 'pointer';
    } else {
      this.renderer.domElement.style.cursor = 'default';
    }
  }

  checkPinClick() {
    if (!this.pinsGroup || !this.camera) return;
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.pinsGroup.children, true);

    if (intersects.length > 0) {
      let topObj = intersects[0].object;
      while (topObj.parent && topObj.parent !== this.pinsGroup) {
        topObj = topObj.parent;
      }
      if (topObj.userData && topObj.userData.id) {
        if (typeof this.options.onLocationSelect === 'function') {
          this.options.onLocationSelect(topObj.userData);
        }
        this.flyToLocation(topObj.userData.lat, topObj.userData.lon);
      }
    }
  }

  onWindowResize() {
    if (!this.camera || !this.renderer || !this.container) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    this.animationFrameId = requestAnimationFrame(() => this.animate());

    const time = Date.now() * 0.003;

    // 1. Auto-rotation when not dragging
    if (this.options.autoRotate && !this.isDragging) {
      this.targetRotation.y += this.options.autoRotateSpeed;
    }

    // 2. Smooth Damped Rotations & Zoom
    this.currentRotation.x += (this.targetRotation.x - this.currentRotation.x) * 0.08;
    this.currentRotation.y += (this.targetRotation.y - this.currentRotation.y) * 0.08;
    this.currentZoom += (this.targetZoom - this.currentZoom) * 0.08;

    if (this.earthGroup) {
      this.earthGroup.rotation.x = this.currentRotation.x;
      this.earthGroup.rotation.y = this.currentRotation.y;
    }

    if (this.cloudMesh) {
      this.cloudMesh.rotation.y += 0.0006;
    }

    // 3. Camera with Parallax Shift
    if (this.camera) {
      this.camera.position.x += (this.parallaxMouse.x - this.camera.position.x) * 0.05;
      this.camera.position.y += (-this.parallaxMouse.y - this.camera.position.y) * 0.05;
      this.camera.position.z = this.currentZoom;
      this.camera.lookAt(0, 0, 0);
    }

    // 4. Dual Satellite Orbits
    if (this.satMesh) {
      this.satOrbitAngle += 0.015;
      const r = this.satOrbitRadius;
      const x = r * Math.cos(this.satOrbitAngle);
      const z = r * Math.sin(this.satOrbitAngle);
      this.satMesh.position.set(x, 0, z);
      this.satMesh.rotation.y = -this.satOrbitAngle;
    }

    if (this.polarSatMesh) {
      this.polarSatAngle += 0.012;
      const rP = this.polarSatRadius;
      const xP = rP * Math.cos(this.polarSatAngle);
      const yP = rP * Math.sin(this.polarSatAngle);
      this.polarSatMesh.position.set(xP, yP, 0);
    }

    // 5. Dynamic Reticle Animation (Spinning crosshairs & pulsing inner ring)
    if (this.targetReticle && this.targetReticle.visible) {
      this.reticleOuter.rotation.z += 0.02;
      this.reticleCross.rotation.z -= 0.015;
      const pulseReticle = 1.0 + 0.2 * Math.sin(time * 4);
      this.reticleInner.scale.setScalar(pulseReticle);
    }

    // 6. Dynamic Pulsing Pins & Beacons
    if (this.pinsGroup && this.pinsGroup.children.length > 0) {
      this.pinsGroup.children.forEach((pin, idx) => {
        const pulse = 1.0 + 0.25 * Math.sin(time * 3 + idx);
        // Head pulse
        if (pin.children[2]) {
          pin.children[2].scale.setScalar(pulse);
        }
        // Base ring expansion
        if (pin.children[0]) {
          const ringPulse = 1.0 + 0.35 * Math.sin(time * 2.5 + idx);
          pin.children[0].scale.setScalar(ringPulse);
        }
      });
    }

    // 7. Subtle starfield celestial drift
    if (this.starfield) {
      this.starfield.rotation.y -= 0.0002;
    }

    this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
    if (this.renderer && this.renderer.domElement && this.renderer.domElement.parentNode) {
      this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
    }
  }

  toggleClouds(visible) {
    if (this.cloudMesh) {
      this.cloudMesh.visible = visible !== undefined ? visible : !this.cloudMesh.visible;
      return this.cloudMesh.visible;
    }
    return false;
  }

  toggleAtmosphere(visible) {
    if (this.atmosMesh) {
      this.atmosMesh.visible = visible !== undefined ? visible : !this.atmosMesh.visible;
      return this.atmosMesh.visible;
    }
    return false;
  }

  toggleSatellites(visible) {
    const show = visible !== undefined ? visible : !(this.satelliteGroup && this.satelliteGroup.visible);
    if (this.satelliteGroup) this.satelliteGroup.visible = show;
    if (this.polarSatGroup) this.polarSatGroup.visible = show;
    return show;
  }

  toggleGrid(visible) {
    if (this.gridGroup) {
      this.gridGroup.visible = visible !== undefined ? visible : !this.gridGroup.visible;
      return this.gridGroup.visible;
    }
    return false;
  }

  resetView() {
    this.targetRotation.x = 0.2;
    this.targetRotation.y = 0;
    this.targetZoom = 260;
  }

  setRotationSpeed(speedMultiplier) {
    this.options.autoRotateSpeed = 0.0018 * speedMultiplier;
  }

  renderFallback() {
    this.container.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;padding:20px;color:#94a3b8;">
        <div style="font-size:48px;margin-bottom:12px;">🌍</div>
        <h4 style="color:#ffffff;margin-bottom:6px;">Earth Observation Globe</h4>
        <p style="font-size:12px;max-width:260px;">WebGL 3D Earth accelerated view. Select any benchmark coordinate from the location catalog.</p>
      </div>
    `;
  }
}

window.EarthScopeGlobe = EarthScopeGlobe;
