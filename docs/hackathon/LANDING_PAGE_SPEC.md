# Landing Page Specification - OscuraTesti AI
**Purpose**: Hackathon submission URL (judges can access without installing)
**Tech Stack**: Static HTML/CSS/JS (deploy to Netlify/Vercel)
**Build Time**: 4-6 hours

---

## Page Structure

### Section 1: Hero (Above the Fold)

```html
┌─────────────────────────────────────────────────────────────┐
│                    [OscuraTesti AI Logo]                     │
│                                                               │
│        Gemini AI Teaches Local ML in Real-Time              │
│      Hybrid PII Detection for Italian Legal Documents        │
│                                                               │
│  [▶ Watch 5-Min Demo]  [⬇ Download App]  [📘 GitHub]       │
│                                                               │
│         Built for LabLab AI Hackathon - Gemini Track         │
└─────────────────────────────────────────────────────────────┘
```

**HTML**:
```html
<section class="hero gradient-bg">
  <div class="container">
    <img src="logo.svg" alt="OscuraTesti AI" class="logo">
    <h1 class="title">Gemini AI Teaches Local ML in Real-Time</h1>
    <p class="subtitle">
      Hybrid PII Detection for Italian Legal Documents
    </p>

    <div class="cta-buttons">
      <a href="#demo-video" class="btn btn-primary">
        ▶ Watch 5-Min Demo
      </a>
      <a href="#download" class="btn btn-secondary">
        ⬇ Download App
      </a>
      <a href="https://github.com/yourorg/oscuratesti-ai"
         class="btn btn-outline" target="_blank">
        📘 GitHub
      </a>
    </div>

    <div class="badge">
      <img src="gemini-logo.svg" alt="Google Gemini">
      <span>Powered by Google Gemini 1.5 Pro</span>
    </div>
  </div>
</section>
```

---

### Section 2: Demo Video (Primary Content for Judges)

```html
┌─────────────────────────────────────────────────────────────┐
│                    🎥 See It In Action                       │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │        [Embedded YouTube/Vimeo Video]                  │  │
│  │        5-minute walkthrough showing:                   │  │
│  │        1. Standard Scan (7/10 entities)                │  │
│  │        2. Gemini Scan (10/10 entities)                 │  │
│  │        3. Learning Loop (the magic)                    │  │
│  │                                                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│     ⭐ Judges: This 5-minute video demonstrates the full     │
│        functionality without requiring installation.          │
└─────────────────────────────────────────────────────────────┘
```

**HTML**:
```html
<section id="demo-video" class="demo-section">
  <div class="container">
    <h2>🎥 See It In Action</h2>
    <p class="section-subtitle">
      5-minute walkthrough of the Gemini Two-Scan architecture
    </p>

    <div class="video-wrapper">
      <iframe
        width="100%"
        height="600"
        src="https://www.youtube.com/embed/YOUR_VIDEO_ID"
        frameborder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowfullscreen>
      </iframe>
    </div>

    <div class="video-chapters">
      <h3>Video Chapters:</h3>
      <ul>
        <li><a href="https://youtu.be/VIDEO_ID?t=0">0:00 - Problem Setup</a></li>
        <li><a href="https://youtu.be/VIDEO_ID?t=30">0:30 - Standard Scan (The Pain)</a></li>
        <li><a href="https://youtu.be/VIDEO_ID?t=90">1:30 - Gemini Scan (The Relief)</a></li>
        <li><a href="https://youtu.be/VIDEO_ID?t=180">3:00 - Learning Loop (The Magic)</a></li>
        <li><a href="https://youtu.be/VIDEO_ID?t=240">4:00 - The Payoff</a></li>
      </ul>
    </div>

    <div class="judge-note">
      <p>
        ⭐ <strong>For Judges:</strong> This video demonstrates the complete
        functionality. For hands-on testing, download the desktop app below.
      </p>
    </div>
  </div>
</section>
```

---

### Section 3: Interactive UI Preview (Read-Only Mockup)

```html
┌─────────────────────────────────────────────────────────────┐
│                    Try the UI (Interactive Demo)             │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  [Scan Mode: ○ Standard  ● Gemini]                    │  │
│  │                                                         │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Gemini Chat Panel                               │  │  │
│  │  │ "Trova tutte le PII in documenti legali..."     │  │  │
│  │  │                                                  │  │  │
│  │  │ [Analyze with Gemini AI] ← (Disabled in demo)  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                         │  │
│  │  ⚠️ This is a UI preview. Download the desktop app     │  │
│  │     for full functionality.                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**:
```html
<section id="interactive-demo" class="interactive-section">
  <div class="container">
    <h2>Try the UI (Interactive Preview)</h2>
    <p class="section-subtitle">
      Explore the interface (read-only demo)
    </p>

    <div class="demo-container">
      <!-- Embedded React component (read-only) -->
      <div id="ui-preview-root"></div>

      <!-- Or simple HTML mockup -->
      <div class="ui-mockup">
        <div class="scan-mode-selector">
          <button class="mode-btn">Standard Scan</button>
          <button class="mode-btn active">Gemini Scan</button>
        </div>

        <div class="gemini-panel">
          <h3>🌟 Gemini AI Assistant</h3>
          <textarea readonly class="prompt-preview">
Sei un esperto nell'analisi di documenti legali italiani...
Trova TUTTE le istanze di PII nel documento fornito...
          </textarea>
          <button class="demo-btn" disabled>
            Analyze with Gemini AI (Download app to try)
          </button>
        </div>

        <div class="demo-notice">
          ⚠️ This is a UI preview. Download the desktop app for full functionality.
        </div>
      </div>
    </div>

    <div class="cta-download">
      <a href="#download" class="btn btn-primary">
        ⬇ Download Full App to Test
      </a>
    </div>
  </div>
</section>
```

**Optional**: Build this with your actual React components (read-only mode):
```typescript
// ui-preview.tsx (for landing page)
import { ScanModeSelector } from './components/ScanModeSelector';
import { GeminiChatPanel } from './components/GeminiChatPanel';

export const UIPreview = () => {
  return (
    <div className="demo-mode">
      <ScanModeSelector
        selectedMode="gemini"
        onModeChange={() => alert('Download the app to try!')}
        learnedCount={0}
      />

      <GeminiChatPanel
        filePath="demo_document.pdf"
        onScan={() => alert('Download the app to use Gemini scan!')}
        isLoading={false}
      />
    </div>
  );
};
```

---

### Section 4: Key Features (Visual Showcase)

```html
┌─────────────────────────────────────────────────────────────┐
│                     Why OscuraTesti AI?                      │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 🎯 Dual Mode│  │ 🧠 Learning │  │ 🔒 Privacy  │         │
│  │             │  │     Loop    │  │    First    │         │
│  │ Standard OR │  │ Gemini      │  │ Local ML +  │         │
│  │ Gemini Scan │  │ teaches     │  │ Optional    │         │
│  │             │  │ Standard    │  │ Cloud AI    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 📊 95%+     │  │ ⚡ Fast     │  │ 🇮🇹 Italian │         │
│  │  Accuracy   │  │ Detection   │  │   Legal     │         │
│  │ w/ Gemini   │  │ ~1s/page    │  │  Optimized  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 5: How It Works (Architecture Diagram)

```html
┌─────────────────────────────────────────────────────────────┐
│                  🏗️ Architecture Overview                    │
│                                                               │
│  [Interactive SVG Diagram or Animated GIF]                  │
│                                                               │
│  User uploads PDF                                            │
│       │                                                       │
│       ├──> Standard Scan (Local ML)                         │
│       │    ├─ Query learned DB (instant)                    │
│       │    └─ GLiNER + Presidio (1s)                        │
│       │                                                       │
│       └──> Gemini Scan (Cloud AI)                           │
│            ├─ Vision + Language (3-5s)                      │
│            └─ 95%+ accuracy                                  │
│                                                               │
│  User confirms Gemini results                                │
│       │                                                       │
│       └──> Learning Loop                                     │
│            └─ Store in local DB                             │
│                                                               │
│  Next document:                                              │
│       └──> Standard Scan now 10x smarter!                   │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 6: Download (Primary CTA for Judges)

```html
┌─────────────────────────────────────────────────────────────┐
│                   ⬇ Download Desktop App                     │
│                                                               │
│  For hands-on testing, download the full Electron app:       │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Windows    │  │    macOS    │  │    Linux    │         │
│  │   🪟        │  │     🍎      │  │     🐧      │         │
│  │  v1.0.0     │  │   v1.0.0    │  │   v1.0.0    │         │
│  │  45 MB      │  │    52 MB    │  │    48 MB    │         │
│  │ [Download]  │  │ [Download]  │  │ [Download]  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                               │
│  📋 Setup Instructions (5 minutes):                          │
│  1. Download installer for your OS                           │
│  2. Run installer (double-click)                             │
│  3. Get free Gemini API key: aistudio.google.com/apikey     │
│  4. Launch OscuraTesti AI                                    │
│  5. Enter API key in settings                                │
│  6. Upload a test PDF and try both scan modes!              │
│                                                               │
│  ⚠️ Note: Requires Python 3.10+ (included in installer)     │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 7: Technical Details (For Deep Evaluation)

```html
┌─────────────────────────────────────────────────────────────┐
│                  🔧 Technical Implementation                  │
│                                                               │
│  Tech Stack:                                                 │
│  • Frontend: React 18 + TypeScript + Tailwind CSS           │
│  • Backend: Python 3.10 + FastAPI                           │
│  • Desktop: Electron 28                                      │
│  • AI Models:                                                │
│    - Google Gemini 1.5 Pro (vision + language)              │
│    - GLiNER Italian NER (DeepMount00/universal_ner_ita)     │
│    - Microsoft Presidio (pattern recognizers)               │
│  • Storage: Simple JSON (learned entities DB)               │
│                                                               │
│  Key Innovations:                                            │
│  ✅ Hybrid AI: Cloud teaches Local ML                       │
│  ✅ Structured JSON output via Gemini schema enforcement    │
│  ✅ Context-aware PII detection for Italian legal docs      │
│  ✅ Privacy-first: Optional cloud, local-first processing   │
│  ✅ Learning loop: Permanent improvement without retraining │
│                                                               │
│  [View Architecture Docs] [View API Reference] [GitHub]     │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 8: Team & Links

```html
┌─────────────────────────────────────────────────────────────┐
│                      📚 Resources                            │
│                                                               │
│  GitHub Repository:                                          │
│  github.com/yourorg/oscuratesti-ai                          │
│                                                               │
│  Documentation:                                              │
│  docs.oscuratesti.ai                                        │
│                                                               │
│  Demo Video:                                                 │
│  youtube.com/watch?v=YOUR_VIDEO_ID                          │
│                                                               │
│  Hackathon Submission:                                       │
│  LabLab AI - Gemini Track                                   │
│  Submitted: January 2025                                     │
│                                                               │
│  Team: CodiceCivile.ai                                      │
│  Contact: hello@oscuratesti.ai                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Instructions

### Option 1: Netlify (Recommended - Free)

```bash
# 1. Create static site
cd landing-page/
npm run build  # If using React
# OR just have index.html + assets/

# 2. Deploy to Netlify
# a) Via Netlify CLI:
npm install -g netlify-cli
netlify deploy --prod

# b) Via drag-and-drop:
# Go to https://app.netlify.com/drop
# Drag the dist/ folder

# 3. Custom domain (optional)
# In Netlify dashboard: Domain settings → Add custom domain
# → oscuratesti.netlify.app OR your-domain.com
```

---

### Option 2: Vercel (Also Free)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
cd landing-page/
vercel --prod

# 3. Will give you URL: https://oscuratesti.vercel.app
```

---

### Option 3: GitHub Pages (Free)

```bash
# 1. Create gh-pages branch
git checkout -b gh-pages

# 2. Add landing page
cp -r landing-page/* .
git add .
git commit -m "Add landing page"
git push origin gh-pages

# 3. Enable in GitHub repo settings
# Settings → Pages → Source: gh-pages branch

# 4. Will be live at:
# https://yourorg.github.io/oscuratesti-ai
```

---

## Build Checklist

- [ ] Create `index.html` with all sections
- [ ] Add CSS for responsive design
- [ ] Embed demo video (YouTube/Vimeo)
- [ ] Add download links for installers
- [ ] Create architecture diagram (PNG/SVG)
- [ ] Add screenshots/GIFs of UI
- [ ] Test on mobile devices
- [ ] Deploy to Netlify/Vercel
- [ ] Get custom URL (if desired)
- [ ] Test all links work
- [ ] Submit URL to hackathon

---

## Quick Start Template

**File**: `landing-page/index.html` (Simple, no build step)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OscuraTesti AI - Gemini Two-Scan Demo</title>
  <meta name="description" content="Hybrid PII detection: Gemini AI teaches local ML in real-time">

  <!-- Tailwind CSS (CDN for quick start) -->
  <script src="https://cdn.tailwindcss.com"></script>

  <style>
    .gradient-bg {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .video-wrapper {
      position: relative;
      padding-bottom: 56.25%; /* 16:9 */
      height: 0;
      overflow: hidden;
    }
    .video-wrapper iframe {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
    }
  </style>
</head>
<body class="bg-gray-50">

  <!-- Hero Section -->
  <section class="gradient-bg text-white py-20">
    <div class="container mx-auto px-6 text-center">
      <h1 class="text-5xl font-bold mb-4">
        OscuraTesti AI
      </h1>
      <p class="text-2xl mb-8">
        Gemini AI Teaches Local ML in Real-Time
      </p>
      <p class="text-xl mb-12 opacity-90">
        Hybrid PII Detection for Italian Legal Documents
      </p>

      <div class="flex gap-4 justify-center">
        <a href="#demo-video" class="bg-white text-purple-700 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition">
          ▶ Watch 5-Min Demo
        </a>
        <a href="#download" class="bg-purple-800 text-white px-8 py-4 rounded-lg font-semibold hover:bg-purple-900 transition">
          ⬇ Download App
        </a>
        <a href="https://github.com/yourorg/oscuratesti-ai" target="_blank" class="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white hover:text-purple-700 transition">
          📘 GitHub
        </a>
      </div>

      <div class="mt-12 flex items-center justify-center gap-3 text-sm">
        <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" alt="Gemini" class="w-6 h-6">
        <span>Powered by Google Gemini 1.5 Pro</span>
      </div>
    </div>
  </section>

  <!-- Demo Video Section -->
  <section id="demo-video" class="py-20 bg-white">
    <div class="container mx-auto px-6">
      <h2 class="text-4xl font-bold text-center mb-4">
        🎥 See It In Action
      </h2>
      <p class="text-xl text-gray-600 text-center mb-12">
        5-minute walkthrough of the Gemini Two-Scan architecture
      </p>

      <div class="max-w-4xl mx-auto">
        <div class="video-wrapper rounded-lg shadow-2xl overflow-hidden">
          <iframe
            src="https://www.youtube.com/embed/YOUR_VIDEO_ID"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen>
          </iframe>
        </div>

        <div class="mt-8 p-6 bg-purple-50 border-2 border-purple-200 rounded-lg">
          <p class="text-purple-900">
            ⭐ <strong>For Judges:</strong> This video demonstrates the complete
            functionality. For hands-on testing, download the desktop app below.
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- Download Section -->
  <section id="download" class="py-20 bg-gray-100">
    <div class="container mx-auto px-6">
      <h2 class="text-4xl font-bold text-center mb-12">
        ⬇ Download Desktop App
      </h2>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
        <!-- Windows -->
        <div class="bg-white p-8 rounded-lg shadow-lg text-center">
          <div class="text-6xl mb-4">🪟</div>
          <h3 class="text-2xl font-bold mb-2">Windows</h3>
          <p class="text-gray-600 mb-4">v1.0.0 • 45 MB</p>
          <a href="releases/OscuraTesti-Setup-1.0.0.exe" class="block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
            Download .exe
          </a>
        </div>

        <!-- macOS -->
        <div class="bg-white p-8 rounded-lg shadow-lg text-center">
          <div class="text-6xl mb-4">🍎</div>
          <h3 class="text-2xl font-bold mb-2">macOS</h3>
          <p class="text-gray-600 mb-4">v1.0.0 • 52 MB</p>
          <a href="releases/OscuraTesti-1.0.0.dmg" class="block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
            Download .dmg
          </a>
        </div>

        <!-- Linux -->
        <div class="bg-white p-8 rounded-lg shadow-lg text-center">
          <div class="text-6xl mb-4">🐧</div>
          <h3 class="text-2xl font-bold mb-2">Linux</h3>
          <p class="text-gray-600 mb-4">v1.0.0 • 48 MB</p>
          <a href="releases/OscuraTesti-1.0.0.AppImage" class="block bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
            Download AppImage
          </a>
        </div>
      </div>

      <!-- Setup Instructions -->
      <div class="mt-12 max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-lg">
        <h3 class="text-2xl font-bold mb-4">📋 Setup Instructions (5 minutes)</h3>
        <ol class="space-y-3 text-lg">
          <li>1. Download installer for your OS</li>
          <li>2. Run installer (double-click)</li>
          <li>3. Get free Gemini API key: <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-blue-600 underline">aistudio.google.com/apikey</a></li>
          <li>4. Launch OscuraTesti AI</li>
          <li>5. Enter API key in settings</li>
          <li>6. Upload a test PDF and try both scan modes!</li>
        </ol>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="bg-gray-900 text-white py-12">
    <div class="container mx-auto px-6 text-center">
      <p class="text-xl mb-4">
        Built for LabLab AI Hackathon - Gemini Track
      </p>
      <p class="text-gray-400 mb-6">
        Team: CodiceCivile.ai • January 2025
      </p>
      <div class="flex gap-6 justify-center">
        <a href="https://github.com/yourorg/oscuratesti-ai" target="_blank" class="text-gray-400 hover:text-white transition">GitHub</a>
        <a href="https://docs.oscuratesti.ai" target="_blank" class="text-gray-400 hover:text-white transition">Docs</a>
        <a href="mailto:hello@oscuratesti.ai" class="text-gray-400 hover:text-white transition">Contact</a>
      </div>
    </div>
  </footer>

</body>
</html>
```

**Build Time**: 4-6 hours
**Deploy Time**: 10 minutes

This gives you a URL judges can access immediately!
