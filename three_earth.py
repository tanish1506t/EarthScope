"""
3D Interactive Earth Component
Renders an interactive 3D WebGL Earth globe with starry cosmos, atmosphere halo,
and a pulsing pin at the selected target coordinates (lat/lon).
"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background: #081226;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        #earth-container {
            width: 100%;
            height: __HEIGHT__px;
            position: relative;
            cursor: grab;
        }
        #earth-container:active {
            cursor: grabbing;
        }
        .overlay-badge {
            position: absolute;
            bottom: 12px;
            left: 14px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 6px 12px;
            color: #f8fafc;
            font-size: 11px;
            backdrop-filter: blur(8px);
            pointer-events: none;
            z-index: 10;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: #00f0ff;
            border-radius: 50%;
            box-shadow: 0 0 8px #00f0ff;
            animation: pulse 1.8s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.8; }
        }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
    <div id="earth-container">
        <div class="overlay-badge">
            <div class="pulse-dot"></div>
            <span><strong>Target:</strong> __LOC__ (__LAT__°, __LON__°)</span>
        </div>
    </div>

    <script>
        (function() {
            const container = document.getElementById('earth-container');
            const width = container.clientWidth || window.innerWidth;
            const height = __HEIGHT__;

            // Scene, Camera, Renderer
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
            camera.position.z = 2.6;

            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(renderer.domElement);

            // Earth Sphere Geometry
            const sphereGeometry = new THREE.SphereGeometry(1, 48, 48);

            // Canvas Texture generation for fast, offline/reliable Earth appearance
            const canvas = document.createElement('canvas');
            canvas.width = 2048;
            canvas.height = 1024;
            const ctx = canvas.getContext('2d');

            // Ocean background
            const oceanGradient = ctx.createLinearGradient(0, 0, 0, 1024);
            oceanGradient.addColorStop(0, '#0a192f');
            oceanGradient.addColorStop(0.5, '#0d254c');
            oceanGradient.addColorStop(1, '#0a192f');
            ctx.fillStyle = oceanGradient;
            ctx.fillRect(0, 0, 2048, 1024);

            // Simplified continental landmass contours
            ctx.fillStyle = '#1e3a5f';
            // Eurasia & Africa
            ctx.beginPath();
            ctx.ellipse(1250, 400, 380, 260, 0, 0, Math.PI * 2);
            ctx.fill();
            // Africa
            ctx.beginPath();
            ctx.ellipse(1150, 600, 200, 280, 0.2, 0, Math.PI * 2);
            ctx.fill();
            // Americas
            ctx.beginPath();
            ctx.ellipse(550, 360, 240, 220, -0.2, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(650, 700, 180, 240, 0.3, 0, Math.PI * 2);
            ctx.fill();
            // Australia
            ctx.beginPath();
            ctx.ellipse(1650, 750, 150, 120, 0, 0, Math.PI * 2);
            ctx.fill();
            // Antarctica
            ctx.beginPath();
            ctx.ellipse(1024, 980, 800, 90, 0, 0, Math.PI * 2);
            ctx.fill();

            // Lat/Lon gridlines
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.15)';
            ctx.lineWidth = 1.5;
            for (let latL = 100; latL < 1024; latL += 100) {
                ctx.beginPath();
                ctx.moveTo(0, latL);
                ctx.lineTo(2048, latL);
                ctx.stroke();
            }
            for (let lonL = 150; lonL < 2048; lonL += 150) {
                ctx.beginPath();
                ctx.moveTo(lonL, 0);
                ctx.lineTo(lonL, 1024);
                ctx.stroke();
            }

            const earthTexture = new THREE.CanvasTexture(canvas);
            const earthMaterial = new THREE.MeshPhongMaterial({
                map: earthTexture,
                shininess: 25,
                specular: new THREE.Color(0x224488)
            });
            const earthMesh = new THREE.Mesh(sphereGeometry, earthMaterial);
            scene.add(earthMesh);

            // Atmosphere Glow Halo with Shader
            const glowGeometry = new THREE.SphereGeometry(1.15, 32, 32);
            const glowMaterial = new THREE.ShaderMaterial({
                vertexShader: [
                    'varying vec3 vNormal;',
                    'void main() {',
                    '    vNormal = normalize(normalMatrix * normal);',
                    '    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
                    '}'
                ].join('\\n'),
                fragmentShader: [
                    'varying vec3 vNormal;',
                    'void main() {',
                    '    float intensity = pow(0.6 - dot(vNormal, vec3(0, 0, 1.0)), 2.0);',
                    '    gl_FragColor = vec4(0.0, 0.94, 1.0, 1.0) * intensity;',
                    '}'
                ].join('\\n'),
                blending: THREE.AdditiveBlending,
                side: THREE.BackSide,
                transparent: true
            });
            const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
            scene.add(glowMesh);

            // Marker Pin calculation for Lat/Lon
            const targetLat = __LAT__;
            const targetLon = __LON__;
            const phi = (90 - targetLat) * (Math.PI / 180);
            const theta = (targetLon + 180) * (Math.PI / 180);

            const pinRadius = 1.02;
            const pinX = -(pinRadius * Math.sin(phi) * Math.cos(theta));
            const pinZ = (pinRadius * Math.sin(phi) * Math.sin(theta));
            const pinY = (pinRadius * Math.cos(phi));

            const pinGeometry = new THREE.SphereGeometry(0.04, 16, 16);
            const pinMaterial = new THREE.MeshBasicMaterial({ color: 0xff3366 });
            const pinMesh = new THREE.Mesh(pinGeometry, pinMaterial);
            pinMesh.position.set(pinX, pinY, pinZ);
            earthMesh.add(pinMesh);

            // Pulsing outer ring on target
            const ringGeometry = new THREE.RingGeometry(0.05, 0.08, 32);
            const ringMaterial = new THREE.MeshBasicMaterial({
                color: 0x00f0ff,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.8
            });
            const ringMesh = new THREE.Mesh(ringGeometry, ringMaterial);
            ringMesh.position.set(pinX * 1.01, pinY * 1.01, pinZ * 1.01);
            ringMesh.lookAt(pinX * 2, pinY * 2, pinZ * 2);
            earthMesh.add(ringMesh);

            // Lighting
            const ambientLight = new THREE.AmbientLight(0x223355, 1.2);
            scene.add(ambientLight);

            const dirLight = new THREE.DirectionalLight(0xffffff, 1.8);
            dirLight.position.set(5, 3, 5);
            scene.add(dirLight);

            // Background Starfield
            const starsGeometry = new THREE.BufferGeometry();
            const starPositions = [];
            for (let i = 0; i < 600; i++) {
                const x = (Math.random() - 0.5) * 40;
                const y = (Math.random() - 0.5) * 40;
                const z = (Math.random() - 0.5) * 40;
                starPositions.push(x, y, z);
            }
            starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
            const starsMaterial = new THREE.PointsMaterial({ color: 0x88bbff, size: 0.08, transparent: true, opacity: 0.7 });
            const starField = new THREE.Points(starsGeometry, starsMaterial);
            scene.add(starField);

            // Interaction / Drag Controls
            let isDragging = false;
            let prevMouseX = 0;
            let prevMouseY = 0;

            container.addEventListener('mousedown', function(e) {
                isDragging = true;
                prevMouseX = e.clientX;
                prevMouseY = e.clientY;
            });

            window.addEventListener('mouseup', function() {
                isDragging = false;
            });

            window.addEventListener('mousemove', function(e) {
                if (isDragging) {
                    const deltaX = e.clientX - prevMouseX;
                    const deltaY = e.clientY - prevMouseY;
                    earthMesh.rotation.y += deltaX * 0.005;
                    earthMesh.rotation.x += deltaY * 0.005;
                    prevMouseX = e.clientX;
                    prevMouseY = e.clientY;
                }
            });

            // Animation Loop
            let ringScale = 1.0;
            let ringGrowing = true;

            function animate() {
                requestAnimationFrame(animate);

                if (!isDragging) {
                    earthMesh.rotation.y += 0.002;
                }
                starField.rotation.y -= 0.0003;

                // Pulsing ring animation
                if (ringGrowing) {
                    ringScale += 0.015;
                    if (ringScale > 1.6) ringGrowing = false;
                } else {
                    ringScale -= 0.015;
                    if (ringScale < 0.9) ringGrowing = true;
                }
                ringMesh.scale.set(ringScale, ringScale, 1.0);

                renderer.render(scene, camera);
            }
            animate();

            // Responsive resize
            window.addEventListener('resize', function() {
                const newW = container.clientWidth;
                camera.aspect = newW / height;
                camera.updateProjectionMatrix();
                renderer.setSize(newW, height);
            });
        })();
    </script>
</body>
</html>"""


def render_three_earth_html(lat: float, lon: float, location_name: str, height: int = 360) -> str:
    """
    Returns standalone HTML/JS with Three.js rendering an animated 3D Earth.
    """
    loc_clean = location_name.split(",")[0].replace('"', '')
    return (
        _HTML_TEMPLATE
        .replace("__HEIGHT__", str(int(height)))
        .replace("__LAT__", f"{lat:.4f}")
        .replace("__LON__", f"{lon:.4f}")
        .replace("__LOC__", loc_clean)
    )
