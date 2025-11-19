# DigitalOcean Deployment Guide - RedaxAI Web Demo
**Goal**: Get live demo URL for hackathon submission
**Platform**: DigitalOcean App Platform
**Estimated Time**: 20-30 minutes
**Cost**: $5-12/month (can cancel after hackathon)

---

## Prerequisites

- [ ] DigitalOcean account (sign up at digitalocean.com - $200 free credit for new users)
- [ ] GitHub repository (must be public or connected to DigitalOcean)
- [ ] Gemini API key ready
- [ ] Web demo code ready (Gradio or Streamlit)

---

## Step 1: Prepare Your Web Demo

### Option A: If you already have `web/` folder with app
Check what you have:
```bash
ls web/
# Should see: app.py, requirements.txt, README.md
```

### Option B: Create minimal web demo (if missing)

Create `web/app.py`:
```python
import gradio as gr
import os
import sys

# Add parent directory to path to import from desktop/src/python
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'desktop', 'src', 'python'))

from gemini_client import GeminiClient
from pii_detector import PIIDetector

# Initialize
gemini_api_key = os.getenv('GEMINI_API_KEY')
gemini_client = GeminiClient(api_key=gemini_api_key) if gemini_api_key else None
detector = PIIDetector()

def chat_with_gemini(message, history):
    """Chat interface for conversational configuration"""
    if not gemini_client:
        return "⚠️ Gemini API key not configured. Please set GEMINI_API_KEY environment variable."

    try:
        # Simple chat with Gemini
        response = gemini_client.chat(message)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

def detect_pii(file, requirements):
    """Process uploaded PDF with requirements"""
    if file is None:
        return "Please upload a PDF file"

    try:
        # Use Gemini to understand requirements
        if gemini_client and requirements:
            context = gemini_client.extract_requirements(requirements)
        else:
            context = {}

        # Detect PII
        results = detector.detect(file.name, context)

        # Format results
        summary = f"Found {len(results)} potential PII items:\n\n"
        for r in results:
            summary += f"- {r['text']}: {r['type']} (confidence: {r['score']:.2f})\n"

        return summary
    except Exception as e:
        return f"Error processing document: {str(e)}"

# Create Gradio interface
with gr.Blocks(title="RedaxAI Demo", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🔒 RedaxAI - Chat to AI, Redact Locally

    **Conversational document redaction with Gemini enhanced accuracy**

    Demo features:
    - 💬 Chat with Gemini to describe redaction requirements
    - 📄 Upload PDF for PII detection
    - 🎯 Context-aware classification
    - 👁️ Review and refine proposals
    """)

    with gr.Tab("Chat with Gemini"):
        gr.Markdown("### Describe your redaction requirements")
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(
            placeholder="Example: This is a medical form. Redact patient name and SSN, but keep doctor name.",
            label="Your message"
        )
        msg.submit(chat_with_gemini, [msg, chatbot], [chatbot])

    with gr.Tab("Process Document"):
        gr.Markdown("### Upload and analyze document")
        with gr.Row():
            with gr.Column():
                file_input = gr.File(label="Upload PDF", file_types=[".pdf"])
                requirements_input = gr.Textbox(
                    label="Requirements (optional)",
                    placeholder="Redact patient info, keep provider names",
                    lines=3
                )
                process_btn = gr.Button("Analyze Document", variant="primary")
            with gr.Column():
                output = gr.Textbox(label="Results", lines=15)

        process_btn.click(detect_pii, [file_input, requirements_input], output)

    gr.Markdown("""
    ---
    **Note**: This is a demo version. For full features including batch processing and template management,
    download the desktop app from [GitHub](https://github.com/[your-username]/redaxai).

    Built with ❤️ and Google Gemini
    """)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=8080,
        share=False
    )
```

Create `web/requirements.txt`:
```txt
gradio==4.44.0
google-generativeai==0.8.0
presidio-analyzer==2.2.354
spacy==3.7.2
PyMuPDF==1.24.0
python-dotenv==1.0.0
```

Create `web/README.md`:
```markdown
# RedaxAI Web Demo

Minimal web demo for hackathon submission.

## Local Testing

```bash
cd web
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
python app.py
```

Visit http://localhost:8080
```

---

## Step 2: Push to GitHub

Make sure your web demo is in the repo:

```bash
# From project root
git add web/
git commit -m "Add web demo for DigitalOcean deployment"
git push origin main
```

Verify files are public:
```
https://github.com/[your-username]/redaxai/tree/main/web
```

---

## Step 3: Create DigitalOcean App

### 3.1 Sign Up / Login
1. Go to https://www.digitalocean.com/
2. Sign up (get $200 free credit) or login
3. Navigate to **Apps** section (left sidebar)

### 3.2 Create New App
1. Click **"Create App"** button
2. Choose **"GitHub"** as source
3. Click **"Manage Access"** → Authorize DigitalOcean to access your GitHub
4. Select your repository: `redaxai`
5. Select branch: `main`
6. **Source Directory**: `/web` (important!)
7. Click **"Next"**

### 3.3 Configure App Settings

**Step 1: Resources**
- Type: **Web Service**
- Name: `redaxai-web-demo`
- Environment: **Python**
- Build Command: (leave auto-detected or use):
  ```
  pip install -r requirements.txt && python -m spacy download en_core_web_sm
  ```
- Run Command:
  ```
  python app.py
  ```
- HTTP Port: `8080`
- HTTP Request Routes: `/`

**Step 2: Environment Variables**
Click **"Edit"** next to Environment Variables, then **"Add Variable"**:

| Key | Value | Encrypt |
|-----|-------|---------|
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | ✅ Yes |
| `PORT` | `8080` | No |

**Step 3: Resources (Instance Size)**
- Instance Size: **Basic ($5/month)** or **Pro ($12/month)** for better performance
- Instance Count: 1

**Step 4: Info**
- App Name: `redaxai-demo`
- Region: Choose closest to you (e.g., New York, San Francisco, London)

Click **"Next"** → Review → **"Create Resources"**

---

## Step 4: Wait for Deployment

DigitalOcean will now:
1. ✅ Clone your GitHub repo
2. ✅ Install dependencies (`requirements.txt`)
3. ✅ Download spaCy model
4. ✅ Build the app
5. ✅ Deploy to live URL

**Estimated time**: 5-10 minutes

You'll see build logs in real-time. Watch for:
- ✅ "Installing dependencies..."
- ✅ "Building..."
- ✅ "Deploying..."
- ✅ "Live" (green status)

---

## Step 5: Get Your Demo URL

Once deployment succeeds:

1. Go to **Apps** → Click your app name
2. Copy the URL shown at the top:
   ```
   https://redaxai-demo-xxxxx.ondigitalocean.app
   ```

3. **Test it immediately**:
   - Open URL in browser
   - Should see Gradio interface
   - Try chatting with Gemini
   - Upload a test PDF

---

## Step 6: Custom Domain (Optional but Recommended)

Make URL more professional:

### Option A: Use DigitalOcean Subdomain (Free)
1. In App settings → **Domains**
2. Click **"Edit"** → Change subdomain:
   ```
   redaxai-demo.ondigitalocean.app
   ```

### Option B: Use Custom Domain (if you own redax.ai)
1. In App settings → **Domains** → **"Add Domain"**
2. Enter: `demo.redax.ai`
3. DigitalOcean shows DNS records to add:
   ```
   Type: CNAME
   Name: demo
   Value: redaxai-demo-xxxxx.ondigitalocean.app
   ```
4. Add these records in your domain registrar (e.g., Namecheap, GoDaddy)
5. Wait 5-10 minutes for DNS propagation
6. Your demo will be at: `https://demo.redax.ai`

---

## Step 7: Enable HTTPS (Automatic)

DigitalOcean automatically provisions SSL certificate:
- ✅ All URLs use HTTPS
- ✅ Certificate auto-renews
- ✅ No configuration needed

---

## Step 8: Monitor & Troubleshoot

### Check Logs
1. Go to **Apps** → Your app → **Runtime Logs**
2. See real-time application logs
3. Look for errors if something doesn't work

### Common Issues:

**Issue 1: Build fails - "Module not found"**
```
Solution: Check requirements.txt has all dependencies
Add missing packages and push to GitHub
DigitalOcean auto-redeploys on git push
```

**Issue 2: App crashes - "GEMINI_API_KEY not found"**
```
Solution:
1. Go to Settings → Environment Variables
2. Add GEMINI_API_KEY
3. Restart app (Settings → click "..." → Force Rebuild)
```

**Issue 3: Port error**
```
Solution: Make sure app.py uses:
demo.launch(server_name="0.0.0.0", server_port=8080)
```

**Issue 4: Timeout / Slow**
```
Solution: Upgrade instance size
Settings → Edit Plan → Choose $12/month Pro tier
```

---

## Step 9: Update Submission Requirements

Now update your hackathon submission doc with the URL:

```markdown
**Application URL**: https://redaxai-demo-xxxxx.ondigitalocean.app

or (if custom domain):

**Application URL**: https://demo.redax.ai
```

---

## Step 10: Test Thoroughly

Before submitting, test ALL features:

- [ ] URL loads in browser (Chrome, Firefox, Safari)
- [ ] Gemini chat works (try: "Redact patient, keep doctor")
- [ ] PDF upload works
- [ ] Detection shows results
- [ ] No errors in browser console (F12 → Console)
- [ ] Mobile responsive (test on phone)
- [ ] HTTPS working (green lock icon)

---

## Ongoing Management

### Auto-Deploy on Push
Every `git push` to `main` branch triggers automatic redeployment:
```bash
git add .
git commit -m "Fix: improve error handling"
git push origin main
# DigitalOcean auto-deploys in 3-5 minutes
```

### Pause App (Save Money)
After hackathon, you can pause to stop billing:
1. Apps → Your app → Settings
2. Click **"Destroy"** (can recreate anytime from GitHub)

Or keep it running for portfolio ($5-12/month)

---

## Cost Breakdown

| Plan | CPU | RAM | Monthly Cost | Best For |
|------|-----|-----|--------------|----------|
| Basic | 1 vCPU | 512 MB | $5 | Simple demo |
| Pro | 1 vCPU | 1 GB | $12 | Better performance |
| Pro+ | 2 vCPU | 2 GB | $24 | Production |

**Recommendation**: Start with Basic ($5), upgrade to Pro ($12) if slow.

**Free Credit**: New users get $200 credit (good for 16 months of Basic plan!)

---

## Alternative: Deploy to Other Platforms

If DigitalOcean doesn't work:

### Hugging Face Spaces (Backup Option)
```bash
# Create account at huggingface.co
# Create new Space
# Upload app.py and requirements.txt
# Set GEMINI_API_KEY in Settings → Secrets
# Get URL: https://huggingface.co/spaces/username/redaxai
```

### Vercel (Another Backup)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd web
vercel --prod
# Follow prompts, get URL
```

---

## Quick Reference Commands

```bash
# Test locally before deploying
cd web
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY=your_key  # Windows: set GEMINI_API_KEY=your_key
python app.py
# Visit http://localhost:8080

# Push to trigger DigitalOcean deployment
git add web/
git commit -m "Update web demo"
git push origin main

# Check deployment status
# Visit: https://cloud.digitalocean.com/apps
```

---

## Troubleshooting Checklist

Before contacting support:

- [ ] Checked Runtime Logs for errors
- [ ] Verified GEMINI_API_KEY is set correctly
- [ ] Tested locally (works on localhost?)
- [ ] Checked requirements.txt is complete
- [ ] Verified GitHub repo is public
- [ ] Tried Force Rebuild (Settings → ... → Force Rebuild)

---

## Summary

**To get your demo URL:**

1. ✅ Prepare `web/app.py` and `requirements.txt`
2. ✅ Push to GitHub
3. ✅ Create DigitalOcean account ($200 free credit)
4. ✅ Create App → Connect GitHub repo
5. ✅ Set source directory to `/web`
6. ✅ Add `GEMINI_API_KEY` environment variable
7. ✅ Deploy (wait 5-10 min)
8. ✅ Get URL: `https://redaxai-demo-xxxxx.ondigitalocean.app`
9. ✅ Test thoroughly
10. ✅ Add URL to hackathon submission

**Time**: 20-30 minutes total
**Cost**: $5-12/month (or free with $200 credit)
**Difficulty**: Easy (mostly clicking through UI)

---

**Need help?** Check DigitalOcean docs: https://docs.digitalocean.com/products/app-platform/

Good luck with your deployment! 🚀
