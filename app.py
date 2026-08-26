"""SafeDrive hackathon demo. All records and OTPs are simulated."""
from datetime import datetime
from io import BytesIO
from pathlib import Path
import re, sqlite3, time, uuid
import qrcode
import streamlit as st

st.set_page_config("SafeDrive | mParivahan companion", "🛡️", layout="wide")
DB = Path(__file__).with_name("safedrive_demo.db")
LIMIT, OTP, OTP_LIFETIME, OTP_COOLDOWN, MAX_ATTEMPTS = 10, "123456", 300, 30, 3

def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
def run(sql, args=()):
    with conn() as c: c.execute(sql,args); c.commit()
def one(sql,args=()):
    with conn() as c: return c.execute(sql,args).fetchone()
def all_rows(sql,args=()):
    with conn() as c: return c.execute(sql,args).fetchall()
def mobile(v): return "".join(x for x in v if x.isdigit())
def number(v): return v.replace(" ","").upper()
def me(): return st.session_state.user
def person(): return one("SELECT * FROM users WHERE phone=?",(me(),))
def title(a,b): st.title(a); st.caption(b)
def context_bar(page):
    st.caption(f"SafeDrive / {page}")

def init_db():
    with conn() as c:
        c.executescript("""CREATE TABLE IF NOT EXISTS users(phone TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS state(phone TEXT PRIMARY KEY,searches INTEGER NOT NULL DEFAULT 0,usage_date TEXT NOT NULL,trusted INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS docs(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT NOT NULL,kind TEXT NOT NULL,num TEXT NOT NULL,status TEXT NOT NULL,updated TEXT NOT NULL,UNIQUE(phone,kind,num));
        CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY,phone TEXT NOT NULL,subject TEXT NOT NULL,detail TEXT NOT NULL,status TEXT NOT NULL,updated TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS retries(id INTEGER PRIMARY KEY AUTOINCREMENT,phone TEXT NOT NULL,task TEXT NOT NULL,saved TEXT NOT NULL);""")
        now,today=datetime.now().isoformat(timespec="seconds"),datetime.now().date().isoformat()
        c.execute("INSERT OR IGNORE INTO users VALUES(?,?,?)",("9876543210","Aarav Sharma",now))
        c.execute("INSERT OR IGNORE INTO state VALUES(?,?,?,?)",("9876543210",1,today,1))
        if not c.execute("SELECT 1 FROM docs WHERE phone=?",("9876543210",)).fetchone():
            c.executemany("INSERT INTO docs(phone,kind,num,status,updated) VALUES(?,?,?,?,?)",[("9876543210","Registration Certificate","DL01AB1234","Synced","Today, 10:42 AM"),("9876543210","Driving Licence","DL-0420110123456","Synced","Today, 10:39 AM")])
        if not c.execute("SELECT 1 FROM tickets WHERE phone=?",("9876543210",)).fetchone():
            c.executemany("INSERT INTO tickets VALUES(?,?,?,?,?,?)",[("SD-1024","9876543210","Vehicle record was missing","Demo issue for the hackathon walkthrough.","In review","18 minutes ago"),("SD-1017","9876543210","OTP did not arrive","Demo issue for the hackathon walkthrough.","Resolved","Yesterday")])
        c.commit()
def init_session():
    for k,v in {"logged":False,"user":None,"page":"Dashboard","step":"choose","pending":None,"attempts":0,"expires":0.0,"resend":0.0}.items(): st.session_state.setdefault(k,v)
def start_otp(phone):
    st.session_state.pending,st.session_state.step=phone,"otp"; st.session_state.attempts=0
    st.session_state.expires=time.time()+OTP_LIFETIME; st.session_state.resend=time.time()+OTP_COOLDOWN
def quota(phone):
    s,today=one("SELECT * FROM state WHERE phone=?",(phone,)),datetime.now().date().isoformat()
    if s["usage_date"]!=today: run("UPDATE state SET searches=0,usage_date=? WHERE phone=?",(today,phone)); return 0
    return s["searches"]
def ticket(phone,subject,detail):
    ident="SD-"+uuid.uuid4().hex[:6].upper(); run("INSERT INTO tickets VALUES(?,?,?,?,?,?)",(ident,phone,subject,detail.strip(),"New","Just now")); return ident

init_db(); init_session()
st.markdown("""<style>.stApp{background:#f6f8fc}[data-testid="stSidebar"]{background:#0b1f3a}[data-testid="stSidebar"] *{color:#eef5ff!important}.hero{background:linear-gradient(120deg,#0c3266,#0b7a75);padding:2rem;border-radius:20px;color:white;margin-bottom:1.4rem}.card{background:#fff;border:1px solid #e5eaf2;border-radius:16px;padding:1rem;min-height:100px}.metric{font-size:1.7rem;font-weight:700;color:#102a50}.pill{padding:.18rem .58rem;border-radius:999px;background:#e5f6ee;color:#137a4d;font-size:.8rem}</style>""",unsafe_allow_html=True)

def login():
    st.markdown('<div class="hero"><h1>SafeDrive</h1><p>A safer, more reliable way to access transport documents.</p></div>',unsafe_allow_html=True)
    st.caption("Hackathon demo only. No real mParivahan account, document, SMS, or government data is used.")
    if st.session_state.step=="otp":
        left=max(0,int(st.session_state.expires-time.time())); cooldown=max(0,int(st.session_state.resend-time.time())); locked=st.session_state.attempts>=MAX_ATTEMPTS
        title("Verify your mobile number",f"OTP sent to +91 ••••••{st.session_state.pending[-4:]}")
        st.caption(f"OTP is valid for {left//60}:{left%60:02d}.")
        with st.expander("Hackathon demo shortcut"):
            st.code(f"Demo OTP: {OTP}", language=None)
            st.caption("This shortcut exists only for the prototype. Production uses a unique OTP sent through an approved SMS provider.")
        if locked: st.error("Too many incorrect attempts. Resend an OTP to start a new challenge.")
        code=st.text_input("Enter the 6-digit OTP",max_chars=6,type="password")
        a,b=st.columns(2)
        with a:
            if st.button("Verify and continue",type="primary",use_container_width=True,disabled=locked):
                if time.time()>st.session_state.expires: st.error("This OTP expired. Resend a new OTP.")
                elif code==OTP: st.session_state.logged,st.session_state.user,st.session_state.step=True,st.session_state.pending,"choose"; st.rerun()
                else:
                    st.session_state.attempts+=1; remaining=MAX_ATTEMPTS-st.session_state.attempts
                    st.error("Too many incorrect attempts. Resend an OTP." if remaining<=0 else f"Incorrect OTP. {remaining} attempt(s) remaining.")
        with b:
            if st.button("Resend OTP",use_container_width=True,disabled=cooldown>0): start_otp(st.session_state.pending); st.rerun()
        if cooldown:
            st.caption(f"You can resend in {cooldown} seconds.")
            if st.button("Refresh OTP timer"):
                st.rerun()
        if st.button("Use a different mobile number"): st.session_state.step,st.session_state.pending="choose",None; st.rerun()
        return
    a,b=st.tabs(["Log in","Create account"])
    with a:
        with st.form("login_form"): p,sent=mobile(st.text_input("Registered mobile number",placeholder="9876543210")),st.form_submit_button("Send OTP")
        if sent:
            if len(p)!=10: st.error("Enter a valid 10-digit mobile number.")
            elif not one("SELECT phone FROM users WHERE phone=?",(p,)): st.warning("No account found. Create one first.")
            else: start_otp(p); st.rerun()
    with b:
        with st.form("signup_form"):
            name=st.text_input("Full name"); p=mobile(st.text_input("Mobile number",placeholder="9876543210")); ok=st.checkbox("I agree to receive a demo verification OTP."); sent=st.form_submit_button("Create account and send OTP")
        if sent:
            if not name.strip() or len(p)!=10: st.error("Enter your name and a valid 10-digit mobile number.")
            elif not ok: st.error("Please confirm OTP consent.")
            elif one("SELECT phone FROM users WHERE phone=?",(p,)): st.warning("An account already exists. Log in instead.")
            else:
                run("INSERT INTO users VALUES(?,?,?)",(p,name.strip(),datetime.now().isoformat(timespec="seconds")));run("INSERT INTO state VALUES(?,?,?,?)",(p,0,datetime.now().date().isoformat(),0));start_otp(p);st.rerun()

def dashboard():
    p,used=me(),quota(me()); docs=one("SELECT COUNT(*) n FROM docs WHERE phone=?",(p,))["n"]; open_tickets=one("SELECT COUNT(*) n FROM tickets WHERE phone=? AND status!='Resolved'",(p,))["n"]; trusted=one("SELECT trusted FROM state WHERE phone=?",(p,))["trusted"]
    context_bar("Dashboard")
    st.markdown('<div class="hero"><h1>Your documents. Always within reach.</h1><p>Transparent sync, recovery, and safe official-service handoffs.</p></div>',unsafe_allow_html=True)
    for col,label,value,pill in zip(st.columns(4),["Protected documents","Searches remaining today","Secure session","Open support requests"],[docs,f"{LIMIT-used} / {LIMIT}","Verified" if trusted else "Verification needed",open_tickets],["Account isolated","Resets daily","Privacy first","Live tracking"]):
        with col: st.markdown(f'<div class="card">{label}<div class="metric">{value}</div><span class="pill">{pill}</span></div>',unsafe_allow_html=True)
    if not trusted:
        if st.button("Verify now", type="primary"):
            st.session_state.page="Secure access"; st.rerun()
    for col,label,page in zip(st.columns(5),["Document vault","Vehicle search","Challan check","Support centre","Service hub"],["Document vault","Vehicle search","Challan check","Support centre","Service hub"]):
        with col:
            if st.button(label,use_container_width=True): st.session_state.page=page;st.rerun()

def vault():
    p=me(); context_bar("Document vault"); title("Document vault","Account-scoped virtual RC/DL passes. They are not replacements for official documents.")
    rows=all_rows("SELECT * FROM docs WHERE phone=? ORDER BY id DESC",(p,))
    if not rows: st.info("No documents saved yet. Add a demo document or use the official Service hub.")
    for d in rows:
        with st.container(border=True):
            a,b,c=st.columns([2,2,1]);a.markdown(f"**{d['kind']}** — {d['num']}");b.markdown(f"Owner: {person()['name']} — Last sync: {d['updated']}");c.success(d["status"])
        with st.expander(f"Open secure verification pass · {d['kind']}"):
            token=f"SAFEDRIVE-DEMO|{d['kind']}|{d['num']}|{d['updated']}";buf=BytesIO();qrcode.make(token).save(buf,format="PNG");x,y=st.columns([1,2])
            with x: st.image(buf.getvalue(),width=170)
            with y: st.write("Demo-only minimal-data verification pass.");st.code(token,language=None)
    with st.expander("Add a document safely"):
        kind=st.selectbox("Document type",["Registration Certificate","Driving Licence"]);num=number(st.text_input("Document number"))
        if st.button("Verify and add"):
            if not re.fullmatch(r"[A-Z0-9-]{6,20}",num): st.error("Use 6–20 letters, numbers, or hyphens.")
            elif one("SELECT id FROM docs WHERE phone=? AND kind=? AND num=?",(p,kind,num)): st.warning("That document is already in your vault.")
            else: run("INSERT INTO docs(phone,kind,num,status,updated) VALUES(?,?,?,?,?)",(p,kind,num,"Synced","Just now"));st.success("Demo document added.");st.rerun()

def recovery():
    p=me();count=one("SELECT COUNT(*) n FROM docs WHERE phone=?",(p,))["n"];context_bar("Recover documents");title("Recover documents","Recover only this account’s local demo vault; SafeDrive never silently overwrites records.")
    source=st.radio("Where should we look first?",["My secure device backup","Verify against official record","I need guided support"],horizontal=True);allowed=st.checkbox("I confirm that I am authorised to access these records")
    if st.button("Start recovery",type="primary"):
        if not allowed: st.error("Confirm authorisation before recovery.")
        elif source=="I need guided support": st.success(f"Request {ticket(p,'Guided document recovery','User requested guided recovery assistance.')} created.")
        elif source=="Verify against official record": run("INSERT INTO retries(phone,task,saved) VALUES(?,?,?)",(p,"Verify document through official service","Just now"));st.info("No official lookup was performed. Continue through the Service hub.")
        elif count: st.success(f"Recovery complete: {count} saved document(s) found for this account. Nothing was overwritten.")
        else: st.warning("No SafeDrive backup exists for this account yet.")
    st.dataframe([{"Action":"Account-scoped backup check","Result":f"{count} document(s) available"}],hide_index=True,use_container_width=True)

def search():
    p,used=me(),quota(me());remaining=LIMIT-used;context_bar("Vehicle search");title("Vehicle search","A transparent quota that resets automatically each calendar day.");st.progress(used/LIMIT,text=f"{remaining} of {LIMIT} standard searches remain today")
    vehicle=number(st.text_input("Vehicle registration number",placeholder="e.g. DL01AB1234"))
    if st.button("Search vehicle",type="primary"):
        if not re.fullmatch(r"[A-Z0-9-]{6,15}",vehicle): st.error("Enter a valid vehicle registration number.")
        elif remaining==0: st.warning("Today's standard limit is reached. It resets automatically at midnight.")
        else:
            run("UPDATE state SET searches=searches+1 WHERE phone=?",(p,));saved=one("SELECT id FROM docs WHERE phone=? AND num=?",(p,vehicle))
            st.success(f"Demo lookup complete for {vehicle}. This was search {used+1} of {LIMIT}.")
            st.dataframe([{"Registration":vehicle,"Owner":"Protected — official verification required","Registration date":"Demo data","Registering authority":"Demo RTO","Make / model":"Demo vehicle","Fuel type":"Demo data","Insurance validity":"Verify officially","Vault match":"Saved in your vault" if saved else "Not in your vault"}],hide_index=True,use_container_width=True)
            st.link_button("Verify with the official service","https://services.parivahan.gov.in/ntr/#/knowurdetails/login")

def hub():
    context_bar("Service hub");title("Service hub","Clear handoffs to official services. SafeDrive does not change government records.")
    a,b,c=st.columns(3)
    with a: st.subheader("Vehicle services");st.link_button("Know vehicle details","https://services.parivahan.gov.in/ntr/#/knowurdetails/login",use_container_width=True);st.link_button("Vehicle-related services","https://parivahan.gov.in/en/content/vehicle-related-services",use_container_width=True)
    with b: st.subheader("Licence services");st.link_button("Know licence details","https://services.parivahan.gov.in/ntr/#/knowurdetails/login",use_container_width=True);st.link_button("Driving licence services","https://sarathi.parivahan.gov.in/sarathiservice/stateSelection.do",use_container_width=True)
    with c: st.subheader("Mobile number updates");st.link_button("Update Vahan mobile number","https://vahan.parivahan.gov.in/mobileupdate/",use_container_width=True);st.link_button("Update Sarathi mobile number","https://sarathi.parivahan.gov.in/sarathiservice/mobNumUpdpub.do",use_container_width=True)

def access():
    p=me();context_bar("Secure access");title("Secure access","Trusted-device preference and retry support for failed access.")
    if st.button("Save trusted-device preference"):run("UPDATE state SET trusted=1 WHERE phone=?",(p,));st.success("Preference saved.")
    if st.button("Save current task and retry later"):run("INSERT INTO retries(phone,task,saved) VALUES(?,?,?)",(p,"OTP verification or account access","Just now"));st.success("Saved.")
    rows=all_rows("SELECT task,saved FROM retries WHERE phone=? ORDER BY id DESC",(p,))
    if rows:st.dataframe(rows,hide_index=True,use_container_width=True)

def support():
    p=me();context_bar("Support centre");title("Support centre","Every ticket retains its description and status.");rows=all_rows("SELECT * FROM tickets WHERE phone=? ORDER BY rowid DESC",(p,))
    if not rows:st.info("No support requests yet.")
    for t in rows:
        with st.container(border=True):
            a,b,c=st.columns([1,3,1]);a.markdown(f"**{t['id']}**");b.markdown(f"**{t['subject']}**  \n{t['detail']}  \nUpdated {t['updated']}");c.write(t["status"])
    with st.form("ticket"):subject=st.selectbox("What do you need help with?",["Missing document","OTP or login","Vehicle search","Unexpected error","Other"]);detail=st.text_area("Briefly describe what happened",max_chars=1000);submitted=st.form_submit_button("Create request")
    if submitted:
        if not detail.strip():st.error("Describe the issue so support can act on it.")
        else:st.success(f"Request {ticket(p,subject,detail)} created.");st.rerun()

def challan():
    context_bar("Challan check")
    title("Challan check", "A clear simulated status check with an official verification handoff.")
    st.info("This screen uses simulated data only. It never retrieves or pays an official challan.")
    value=number(st.text_input("Vehicle registration number or challan number",placeholder="e.g. DL01AB1234"))
    if st.button("Check challan status",type="primary"):
        if not re.fullmatch(r"[A-Z0-9-]{6,20}",value):
            st.error("Enter a valid vehicle registration or challan number.")
        else:
            st.success(f"No simulated pending challans found for {value}.")
            st.dataframe([{"Reference":value,"Status":"No simulated dues","Last checked":datetime.now().strftime("%d %b %Y, %I:%M %p")}],hide_index=True,use_container_width=True)
            st.link_button("Verify on official eChallan", "https://echallan.parivahan.gov.in/")

PAGES={"Dashboard":dashboard,"Document vault":vault,"Recover documents":recovery,"Vehicle search":search,"Challan check":challan,"Service hub":hub,"Secure access":access,"Support centre":support}
if not st.session_state.logged:login()
else:
    if not one("SELECT phone FROM users WHERE phone=?",(me(),)):st.session_state.logged,st.session_state.user=False,None;st.error("Session is no longer valid.");st.stop()
    with st.sidebar:
        st.markdown("# 🛡️ SafeDrive");st.caption("mParivahan reliability companion");st.write(f"Signed in as **{person()['name']}**")
        page=st.session_state.page if st.session_state.page in PAGES else "Dashboard";st.session_state.page=st.radio("Navigate",list(PAGES),index=list(PAGES).index(page))
        if st.button("Log out",use_container_width=True):st.session_state.logged,st.session_state.user,st.session_state.step,st.session_state.pending=False,None,"choose",None;st.rerun()
        st.caption("Hackathon prototype · Uses local simulated data only")
    PAGES[st.session_state.page]()
