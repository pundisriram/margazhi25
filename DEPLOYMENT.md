# Deployment Guide for Margazhi Season Planner

## Option 1: Streamlit Cloud (Recommended - Easiest)

Streamlit Cloud is the easiest way to deploy your app for free.

### Steps:

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Go to [Streamlit Cloud](https://streamlit.io/cloud)**
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Set up Secrets (API Keys):**
   - In Streamlit Cloud, go to your app settings
   - Click "Secrets" tab
   - Add your API keys:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
     ```
   - Save and the app will redeploy

4. **Your app will be live at:** `https://your-app-name.streamlit.app`

### Important Notes:
- Make sure `combined_schedules.csv` is in your repository
- The app will automatically install dependencies from `requirements.txt`
- API keys are stored securely in Streamlit Cloud secrets

---

## Option 2: Heroku

### Steps:

1. **Install Heroku CLI** (if not already installed)

2. **Create a Procfile:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

3. **Create setup.sh:**
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   port = $PORT\n\
   enableCORS = false\n\
   headless = true\n\
   " > ~/.streamlit/config.toml
   ```

4. **Deploy:**
   ```bash
   heroku create your-app-name
   heroku config:set GEMINI_API_KEY=your_key
   heroku config:set GOOGLE_MAPS_API_KEY=your_key
   git push heroku main
   ```

---

## Option 3: Docker + Cloud Platform

### Create Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Then deploy to:
- **Railway**: https://railway.app
- **Render**: https://render.com
- **Fly.io**: https://fly.io
- **AWS/GCP/Azure**: Use their container services

---

## Option 4: Local Network Sharing

For sharing on your local network:

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

Then others on your network can access: `http://your-ip-address:8501`

---

## Pre-Deployment Checklist

- [ ] `requirements.txt` is up to date
- [ ] `combined_schedules.csv` is in the repository
- [ ] `.env` is in `.gitignore` (API keys should NOT be committed)
- [ ] All necessary files are committed to git
- [ ] API keys are ready to add as environment variables/secrets

---

## Recommended: Streamlit Cloud

**Why Streamlit Cloud:**
- ✅ Free for public apps
- ✅ Automatic deployments from GitHub
- ✅ Easy secret management
- ✅ No server management
- ✅ HTTPS by default
- ✅ Easy to update (just push to GitHub)

