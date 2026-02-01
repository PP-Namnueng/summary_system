/* 
   interactions.js - Motion Engine & Particle System
   Features: Neural Web Background, 3D Tilt
*/

(function () {
    // --- 1. Neural Particle Background ---
    function initParticles() {
        const canvas = document.getElementById('bgCanvas');
        if (!canvas) return; // Might not be injected yet

        const ctx = canvas.getContext('2d');
        let width, height;
        let particles = [];

        // Track Mouse
        window.mouseX = 0;
        window.mouseY = 0;
        window.addEventListener('mousemove', (e) => {
            window.mouseX = e.clientX;
            window.mouseY = e.clientY;
        });

        // Configuration: Twilight Crystals (V5)
        const particleCount = 70;
        const connectionDistance = 160;
        const moveSpeed = 0.4;
        const particleColor = 'rgba(255, 255, 255, 0.4)'; // Frost White
        const lineColor = 'rgba(45, 212, 191, 0.15)'; // Teal tint lines

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }

        class Particle {
            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.vx = (Math.random() - 0.5) * moveSpeed;
                this.vy = (Math.random() - 0.5) * moveSpeed;
                this.size = Math.random() * 2 + 1;
            }

            update() {
                // Interactive: Mouse Interaction
                const dx = window.mouseX - this.x;
                const dy = window.mouseY - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 200) {
                    this.vx += (dx / dist) * 0.05; // Gently attract
                    this.vy += (dy / dist) * 0.05;
                }

                this.x += this.vx;
                this.y += this.vy;

                // Friction
                this.vx *= 0.99;
                this.vy *= 0.99;

                // Bounce off edges
                if (this.x < 0 || this.x > width) this.vx *= -1;
                if (this.y < 0 || this.y > height) this.vy *= -1;
            }

            draw() {
                ctx.fillStyle = particleColor;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        function init() {
            resize();
            particles = [];
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle());
            }
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);

            // Update and draw particles
            particles.forEach(p => {
                p.update();
                p.draw();
            });

            // Draw connections
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < connectionDistance) {
                        ctx.strokeStyle = lineColor;
                        ctx.lineWidth = 1 - distance / connectionDistance;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }

            requestAnimationFrame(animate);
        }

        window.addEventListener('resize', resize);
        init();
        animate();
        console.log("Neural Particles Initialized");
    }

    // --- 2. 3D Tilt Effect ---
    function initTilt() {
        const cards = document.querySelectorAll('.glass-card');
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                // Calculate rotation (max 10 degrees)
                const xPct = x / rect.width;
                const yPct = y / rect.height;

                const rotateX = (0.5 - yPct) * 10;
                const rotateY = (xPct - 0.5) * 10;

                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
            });
        });
    }

    // --- 3. Component Mapping (Auto-Magical) ---
    function mapComponents() {
        const containers = document.querySelectorAll('div[data-testid="stVerticalBlockBorderWrapper"], .stExpander');
        containers.forEach(el => {
            if (!el.classList.contains('glass-card')) el.classList.add('glass-card');
        });

        const buttons = document.querySelectorAll('.stButton button');
        buttons.forEach(btn => {
            if (!btn.classList.contains('btn-glass')) btn.classList.add('btn-glass');
        });

        const navLabels = document.querySelectorAll('section[data-testid="stSidebar"] label[data-baseweb="radio"]');
        navLabels.forEach(lbl => {
            const div = lbl.querySelector('div');
            if (div && !div.classList.contains('nav-item')) div.classList.add('nav-item');
        });
    }

    // --- Initialization Logic ---
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initParticles();
            initTilt();
            mapComponents();
        });
    } else {
        initParticles();
        initTilt();
        mapComponents();
    }

    const observer = new MutationObserver((mutations) => {
        mapComponents();
        initTilt();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    setInterval(mapComponents, 2000);
    setTimeout(initParticles, 1000);

})();
