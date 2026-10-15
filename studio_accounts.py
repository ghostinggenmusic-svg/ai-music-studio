"""Account identities and channel access. Passwords stay in Streamlit Secrets."""
import hmac
CHANNELS=['1. GHOSTING MUSIC (หลัก)','2. The Ghost Music Studio (รอง)','3. @watermusic1987','4. AOMSO MUSIC']
USER_CHANNELS={'watermusic':[CHANNELS[2]],'aomsomusic':[CHANNELS[3]]}

def authenticate(username,password,secrets):
    auth=secrets.get('auth',{})
    admin_user=str(auth.get('username',''))
    admin_password=str(auth.get('password',''))
    if admin_user and admin_password and hmac.compare_digest(username.encode(),admin_user.encode()) and hmac.compare_digest(password.encode(),admin_password.encode()):
        return {'username':admin_user,'role':'admin','channels':list(CHANNELS)}
    if username not in USER_CHANNELS: return None
    config=secrets.get('users',{}).get(username,{})
    expected=str(config.get('password',''))
    if expected and hmac.compare_digest(password.encode(),expected.encode()):
        return {'username':username,'role':'user','channels':list(USER_CHANNELS[username])}
    return None

def allowed_channels(username,admin_username):
    if username==admin_username: return list(CHANNELS)
    return list(USER_CHANNELS.get(username,[]))
