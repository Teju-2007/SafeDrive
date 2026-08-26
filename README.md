# SafeDrive — mParivahan reliability companion

A Streamlit hackathon prototype addressing document loss, OTP friction, opaque rate limits, transaction failures, and support visibility. It now includes account-scoped virtual document passes with demo QR verification and transparent official-service handoffs. All content is simulated; it does not access government systems or personal data.

## Demo login

- Registered user mobile: 9876543210
- Demo OTP: 123456

You can also create an account with any 10-digit mobile number. The same demo OTP (123456) completes verification. Accounts, documents, tickets, and search usage persist locally in safedrive_demo.db; this remains simulated hackathon data, not a government system.

## Run locally

1. Install Python 3.10+.
2. Run `pip install -r requirements.txt`.
3. Run `streamlit run app.py`.

## Demo flow

Start by logging in with the demo account or creating one. Then visit **Document vault**, use **Recover documents**, show transparent usage in **Vehicle search**, resilient OTP handling in **Secure access**, and live ticket visibility in **Support centre**.
