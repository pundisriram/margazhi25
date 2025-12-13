# Step-by-Step Deployment to Streamlit Cloud

## ✅ Step 1: Git Repository (DONE)
Git repository has been initialized and files are staged.

## 📝 Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `margazhi25` (or any name you prefer)
3. Description: "AI-powered Margazhi season concert schedule planner"
4. Make it **Public** (required for free Streamlit Cloud)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## 🚀 Step 3: Push to GitHub

Run these commands (replace YOUR_USERNAME with your GitHub username):

```bash
git commit -m "Initial commit: Margazhi Season Planner app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/margazhi25.git
git push -u origin main
```

## ☁️ Step 4: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with your **GitHub account**
3. Click **"New app"** button
4. Fill in:
   - **Repository**: Select `YOUR_USERNAME/margazhi25`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**: (optional) choose a custom name
5. Click **"Deploy"**

## 🔑 Step 5: Add API Keys (IMPORTANT!)

1. Once deployed, click the **"⋮"** menu (three dots) in the top right
2. Select **"Settings"**
3. Click **"Secrets"** tab
4. Add your API keys in this format:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GOOGLE_MAPS_API_KEY=your_actual_google_maps_api_key_here
   ```
5. Click **"Save"** - the app will automatically redeploy

## 🎉 Step 6: Share Your App!

Your app will be live at: `https://your-app-name.streamlit.app`

You can share this link with anyone!

---

## Troubleshooting

**"App not found" error?**
- Make sure the repository is **public** on GitHub
- Check that `app.py` is in the root directory
- Verify `combined_schedules.csv` is committed

**API errors after deployment?**
- Double-check secrets are set correctly (no extra spaces)
- Verify API keys are valid
- Check the app logs in Streamlit Cloud dashboard

**Need to update the app?**
- Just make changes and push to GitHub:
  ```bash
  git add .
  git commit -m "Update description"
  git push
  ```
- Streamlit Cloud will automatically redeploy



