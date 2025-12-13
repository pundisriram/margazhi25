# Push to GitHub - Authentication Options

Your code is committed locally. Now you need to push to GitHub.

## Option 1: Personal Access Token (Easiest)

1. **Create a token:**
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Name: "Streamlit Deployment"
   - Expiration: Choose your preference
   - Select scope: ✅ **repo** (full control)
   - Click "Generate token"
   - **COPY THE TOKEN** (you won't see it again!)

2. **Push to GitHub:**
   ```bash
   git push -u origin main
   ```
   - Username: `pundisriram`
   - Password: **Paste your token** (not your GitHub password)

## Option 2: SSH Key (More Secure)

1. **Check if you have SSH key:**
   ```bash
   ls -la ~/.ssh/id_*.pub
   ```

2. **If no key, generate one:**
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Press Enter to accept defaults
   ```

3. **Add key to GitHub:**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # Copy the output
   ```
   - Go to: https://github.com/settings/keys
   - Click "New SSH key"
   - Paste the key and save

4. **Change remote to SSH:**
   ```bash
   git remote set-url origin git@github.com:pundisriram/margazhi25.git
   git push -u origin main
   ```

## Option 3: GitHub Desktop

If you have GitHub Desktop installed, you can:
1. Open the app
2. Add the repository
3. Push using the GUI

---

## After Pushing Successfully

Once your code is on GitHub, proceed to Streamlit Cloud:
1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Deploy your app!



