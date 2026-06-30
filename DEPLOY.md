# Deploy AI Research Office

## Important

- Do not commit `.env`.
- Do not commit `.streamlit/secrets.toml`.
- If you want users to bring their own API keys, leave provider keys empty on the server.
- Set `APP_PASSWORD` on the server if you want a password before users can open the app.
- Project files created inside `generated_projects/` are local runtime files. On many cloud hosts they are not guaranteed to persist forever.

## Option 1: Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Go to Streamlit Community Cloud and deploy `app.py`.
3. Make sure the repository contains `requirements.txt`.
4. Open **Advanced settings** before deploying and select **Python 3.11** or **Python 3.12**.
   CrewAI/ChromaDB can fail on Python 3.14.
5. In app settings/secrets, add:

```toml
APP_PASSWORD = "your-login-password"
```

If you want users to use their own provider keys, do not add `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` as server secrets.

If your existing app already deployed with Python 3.14, delete/redeploy it and choose Python 3.11 or 3.12 in Advanced settings. Streamlit Community Cloud does not reliably use `runtime.txt` for Python version selection.

## Option 2: Render

1. Push this folder to a GitHub repository.
2. Create a Render Web Service from the repo.
3. Render can use `render.yaml`, or set manually:

```text
Build Command: pip install -r requirements.txt
Start Command: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

4. Add environment variable:

```text
APP_PASSWORD=your-login-password
```

Leave provider keys empty if each user should enter their own key in the app.

## Sharing

After deployment, share the public HTTPS URL and the app password. Each user can open the sidebar and enter their own API key under:

```text
API keys ของผู้ใช้นี้
```
