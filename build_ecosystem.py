import re
import os

html_files = [
    'dandelion-overlay.html',
    'dragonflies-overlay.html',
    'fireflies-overlay.html'
]

combined_js = ""
for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'<script>\s*\(\(\) => \{\s*\'use strict\';(.*?)\}\)\(\);\s*</script>', content, re.DOTALL)
    if match:
        js = match.group(1)
        # Remove canvas/ctx init
        js = re.sub(r'const canvas = .*?;', '', js)
        js = re.sub(r'const ctx = .*?;', '', js)
        js = re.sub(r'const context = .*?;', '', js)
        
        # We will wrap it in a function
        name = file.split('-')[0]
        wrapped = f"function init_{name}(shared) {{\n" + js + f"\n  return {{ resize, update, draw }};\n}}\n"
        
        # Fix missing interact or draw if they don't exist
        wrapped = wrapped.replace('return { resize, update, draw };', 
                                  'return { resize: (typeof resize !== "undefined" ? resize : ()=>{}), update: (typeof update !== "undefined" ? update : (dt)=>{}), draw: (typeof draw !== "undefined" ? draw : (ctx)=>{}) };')
        
        # Inject shared array references
        if name == "dragonflies":
            wrapped = wrapped.replace('return {', 'shared.dragonflies = dragonflies; return {')
        elif name == "fireflies":
            wrapped = wrapped.replace('return {', 'shared.fireflies = fireflies; return {')
        elif name == "dandelion":
            wrapped = wrapped.replace('return {', 'shared.dandelions = seeds; shared.addDandelionGust = (g) => { globalGust += g; }; return {')
            
        combined_js += wrapped + "\n"

# Create the final HTML
html_template = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Ecosystem</title>
  <style>
    html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: transparent; }
    canvas { display: block; width: 100%; height: 100%; cursor: none; }
  </style>
</head>
<body>
  <canvas id="ecosystem"></canvas>
  <script>
    'use strict';
    const canvas = document.getElementById('ecosystem');
    const ctx = canvas.getContext('2d', { alpha: true });
    const context = ctx;
    
    let shared = {
      width: 1, height: 1, dpr: 1, elapsed: 0,
      pointer: { x: -1000, y: -1000, active: false, down: false, velocityX: 0, velocityY: 0 },
      // physics sharing
      dragonflies: [],
      fireflies: [],
      dandelions: []
    };
    
    // utility functions
    function clamp(value, min, max) { return Math.max(min, Math.min(max, value)); }
    function lerp(a, b, amount) { return a + (b - a) * amount; }
    function seeded(seed, offset) {
      let x = Math.sin(seed * 29.3 + offset * 17.1) * 10000;
      return x - Math.floor(x);
    }
    function angleDifference(a, b) {
      const TAU = Math.PI * 2;
      let diff = (b - a) % TAU;
      if (diff < -Math.PI) diff += TAU;
      if (diff > Math.PI) diff -= TAU;
      return diff;
    }

    // Insert combined JS here
    COMBINED_JS
    
    // Engine loop
    const modules = [];
    modules.push(init_dandelion(shared));
    modules.push(init_dragonflies(shared));
    modules.push(init_fireflies(shared));
    
    function resize() {
      shared.width = window.innerWidth;
      shared.height = window.innerHeight;
      shared.dpr = window.devicePixelRatio || 1;
      canvas.width = shared.width * shared.dpr;
      canvas.height = shared.height * shared.dpr;
      ctx.scale(shared.dpr, shared.dpr);
      for (const m of modules) m.resize();
    }
    
    let lastTime = performance.now();
    function animate(time) {
      const dt = Math.min(0.05, (time - lastTime) / 1000);
      lastTime = time;
      shared.elapsed += dt;
      
      ctx.clearRect(0, 0, shared.width, shared.height);
      
      for (const m of modules) m.update(dt);
      
      // PHYSICS INTERACTIONS
      if (shared.dragonflies && shared.dragonflies.length > 0) {
        for (const d of shared.dragonflies) {
           let speed = Math.sqrt(d.vx*d.vx + d.vy*d.vy);
           if (speed > 5) {
               const dartIntensity = speed / 10;
               // Push dandelions
               if (shared.dandelions) {
                   for (const seed of shared.dandelions) {
                       const dx = seed.x - d.x;
                       const dy = seed.y - d.y;
                       const dist = Math.sqrt(dx*dx + dy*dy);
                       if (dist < 300) {
                           const force = (1 - dist/300) * dartIntensity * 20;
                           seed.vx += (dx/dist) * force * dt;
                           seed.vy += (dy/dist) * force * dt;
                       }
                   }
               }
               // Add global gust to dandelions
               if (shared.addDandelionGust) {
                   shared.addDandelionGust((d.vx / speed) * dartIntensity * 0.05 * dt);
               }
               // Fireflies scatter
               if (shared.fireflies) {
                   for (const f of shared.fireflies) {
                       const dx = f.x - d.x;
                       const dy = f.y - d.y;
                       const dist = Math.sqrt(dx*dx + dy*dy);
                       if (dist < 150) {
                           f.vx += (dx/dist) * 200 * dt;
                           f.vy += (dy/dist) * 200 * dt;
                           f.glow = Math.max(0, f.glow - 5*dt); // Dim them
                       }
                   }
               }
           }
        }
      }
      
      for (const m of modules) m.draw(ctx);
      
      requestAnimationFrame(animate);
    }
    
    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(animate);
  </script>
</body>
</html>
"""

with open("ecosystem-overlay.html", "w", encoding="utf-8") as f:
    f.write(html_template.replace("COMBINED_JS", combined_js))

print("Created ecosystem-overlay.html")
