# SafeDrive — mParivahan reliability companion

A Streamlit hackathon prototype addressing document loss, OTP friction, opaque rate limits, transaction failures, and support visibility. It now includes account-scoped virtual document passes with demo QR verification and transparent official-service handoffs. All content is simulated; it does not access government systems or personal data.

## Demo login

- Registered user mobile: 9876543210
- Demo OTP: generated randomly for each login challenge; open the in-app “Hackathon demo shortcut” during testing.

You can also create an account with any valid 10-digit Indian mobile number. A new random six-digit demo OTP is generated for every login, resend, and expiry. Accounts, documents, tickets, and search usage persist locally in safedrive_demo.db; this remains simulated hackathon data, not a government system.

## Optional OpenAI support triage

SafeDrive can use the OpenAI Responses API to draft a plain-language support route and priority. Set OPENAI_API_KEY before running the app to enable it; otherwise the app shows a clearly labelled local fallback. No API call is made unless the key is present.

## Run locally

1. Install Python 3.10+.
2. Run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.

## Demo flow

Start by logging in with the demo account or creating one. Then visit **Document vault**, use **Recover documents**, show transparent usage in **Vehicle search**, resilient OTP handling in **Secure access**, and live ticket visibility in **Support centre**.
