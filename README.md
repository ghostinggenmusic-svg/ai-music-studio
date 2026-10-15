# AI Music Studio

Deploy on Streamlit Community Cloud from a GitHub repository, using app.py as the entrypoint.

Set the following in Advanced settings > Secrets. Choose your own password; never commit real secrets.

```toml
[auth]
username = "admin"
password = "REPLACE_WITH_YOUR_OWN_PASSWORD"
```

Dependencies: requirements.txt. This app was tested locally with Python 3.14.

Demo: kie.ai key = test_empty; Apiframe key = test_ok. Run Music API demonstrates fallback and plays a sample track. Chat and cover generation are placeholders. Real provider adapters need verification before production use; HTTP success does not guarantee completed music generation.

API keys entered in the UI remain in the current Streamlit session and are sent to the selected music provider when Run Music API is clicked.
