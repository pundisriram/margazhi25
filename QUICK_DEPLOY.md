# Quick Deployment Guide

## Fastest Way: Streamlit Cloud (5 minutes)

### Step 1: Push to GitHub
```bash
# If you haven't initialized git yet
git init
git add .
git commit -m "Margazhi Season Planner app"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/margazhi25.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select your repository: `margazhi25`
5. Main file path: `app.py`
6. Click "Deploy"

### Step 3: Add API Keys
1. In your deployed app, click the "⋮" menu (top right)
2. Select "Settings" → "Secrets"
3. Add:
   ```
   GEMINI_API_KEY=your_actual_gemini_key
   GOOGLE_MAPS_API_KEY=your_actual_maps_key
   ```
4. Click "Save" - app will auto-redeploy

### Done! 
Your app is live at: `https://your-app-name.streamlit.app`

---

## What Gets Deployed

✅ All Python files (app.py, data_loader.py, etc.)
✅ combined_schedules.csv (your data)
✅ requirements.txt (dependencies)
✅ .streamlit/config.toml (app configuration)

❌ .env file (use Streamlit Secrets instead)
❌ Cache files
❌ Backup files

---

## Troubleshooting

**App won't start?**
- Check that `combined_schedules.csv` is in the repo
- Verify `requirements.txt` has all dependencies
- Check the logs in Streamlit Cloud dashboard

**API errors?**
- Verify secrets are set correctly in Streamlit Cloud
- Check API keys are valid and have proper permissions

**Need to update?**
- Just push changes to GitHub
- Streamlit Cloud auto-deploys on push

