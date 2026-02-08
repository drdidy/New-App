"""
═══════════════════════════════════════════════════════════════════════════════
TASTYTRADE API CAPABILITY TEST - OAUTH VERSION
═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Tastytrade API Test", page_icon="🔬", layout="wide")

st.title("🔬 Tastytrade API Capability Test (OAuth)")
st.markdown("---")

# OAuth Credentials
CLIENT_ID = "61d8c3a5-d259-4ac9-bf9c-a47ed1e6463f"
CLIENT_SECRET = "a00eac3f462f488b4de1655ab43024aa393bbadf"

# We need to get a refresh token first
st.subheader("Step 1: Get Refresh Token")

st.markdown("""
The OAuth grant was created but we need the **refresh token**. 

Go to: **my.tastytrade.com → API → Manage OAuth Grants**

Click on your app "drdidy Personal OAuth2 App" and look for a way to:
- **View** the refresh token, OR
- **Regenerate/Create** a new grant that shows the token

If you can't find it there, we need to do the OAuth authorization flow manually.
""")

st.markdown("---")

# Manual OAuth Flow
st.subheader("Step 2: Manual OAuth Authorization")

redirect_uri = "https://localhost"
auth_url = f"https://api.tastytrade.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope=read"

st.markdown(f"""
**Option A: Browser Authorization Flow**

1. Click this link (opens in new tab):
   
   [🔗 Authorize Tastytrade App]({auth_url})

2. Log in and approve the app
3. You'll be redirected to a URL like:
   ```
   https://localhost/?code=SOME_CODE_HERE
   ```
4. Copy that **code** and paste it below:
""")

auth_code = st.text_input("Paste the authorization code here:", placeholder="abc123xyz...")

if auth_code:
    st.subheader("Step 3: Exchange Code for Tokens")
    
    if st.button("🔑 Get Tokens", type="primary"):
        with st.spinner("Exchanging code for tokens..."):
            try:
                # Exchange auth code for tokens
                token_url = "https://api.tastytrade.com/oauth/token"
                
                data = {
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": redirect_uri,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                }
                
                response = requests.post(token_url, data=data)
                
                st.write(f"Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    tokens = response.json()
                    st.success("✅ Got tokens!")
                    st.json(tokens)
                    
                    # Save for next step
                    st.session_state['access_token'] = tokens.get('access_token')
                    st.session_state['refresh_token'] = tokens.get('refresh_token')
                    
                    st.code(f"Access Token: {tokens.get('access_token', 'N/A')[:50]}...")
                    st.code(f"Refresh Token: {tokens.get('refresh_token', 'N/A')}")
                    
                    st.warning("⚠️ SAVE THE REFRESH TOKEN! It doesn't expire and you'll need it.")
                else:
                    st.error(f"❌ Error: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Exception: {e}")

st.markdown("---")

# If we have tokens, test the API
st.subheader("Step 4: Test API with Tokens")

refresh_token_input = st.text_input(
    "Enter Refresh Token (if you have one):", 
    value=st.session_state.get('refresh_token', ''),
    type="password"
)

if refresh_token_input and st.button("🧪 Test API Access", type="primary"):
    with st.spinner("Testing API..."):
        try:
            # First, get a fresh access token using refresh token
            token_url = "https://api.tastytrade.com/oauth/token"
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token_input,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                access_token = tokens.get('access_token')
                st.success("✅ Got access token from refresh token!")
                
                # Now test API calls
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                # Test 1: Get customer info
                st.markdown("**Testing Customer Info...**")
                r = requests.get("https://api.tastytrade.com/customers/me", headers=headers)
                if r.status_code == 200:
                    st.success("✅ Customer info accessible!")
                    st.json(r.json())
                else:
                    st.error(f"❌ Customer: {r.status_code} - {r.text[:200]}")
                
                # Test 2: Get accounts
                st.markdown("**Testing Accounts...**")
                r = requests.get("https://api.tastytrade.com/customers/me/accounts", headers=headers)
                if r.status_code == 200:
                    st.success("✅ Accounts accessible!")
                    st.json(r.json())
                else:
                    st.error(f"❌ Accounts: {r.status_code} - {r.text[:200]}")
                
                # Test 3: Get futures
                st.markdown("**Testing ES Futures...**")
                r = requests.get("https://api.tastytrade.com/instruments/futures/ES", headers=headers)
                if r.status_code == 200:
                    st.success("✅ ES Futures accessible!")
                    st.json(r.json())
                else:
                    st.error(f"❌ ES Futures: {r.status_code} - {r.text[:200]}")
                
                # Test 4: Get VX futures
                st.markdown("**Testing VX Futures (VIX)...**")
                r = requests.get("https://api.tastytrade.com/instruments/futures/VX", headers=headers)
                if r.status_code == 200:
                    st.success("✅ VX Futures accessible! 🎉")
                    st.json(r.json())
                else:
                    st.error(f"❌ VX Futures: {r.status_code} - {r.text[:200]}")
                
                # Test 5: Get future products list
                st.markdown("**Testing Future Products List...**")
                r = requests.get("https://api.tastytrade.com/instruments/future-products", headers=headers)
                if r.status_code == 200:
                    st.success("✅ Future products accessible!")
                    data = r.json()
                    products = data.get('data', {}).get('items', [])
                    st.write(f"Found {len(products)} future products")
                    # Look for VX
                    vx_products = [p for p in products if 'VX' in str(p.get('root-symbol', ''))]
                    if vx_products:
                        st.success("🎯 VX (VIX Futures) found!")
                        st.json(vx_products[0])
                else:
                    st.error(f"❌ Future Products: {r.status_code} - {r.text[:200]}")
                    
            else:
                st.error(f"❌ Token refresh failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            st.error(f"❌ Exception: {e}")
            import traceback
            st.code(traceback.format_exc())

st.markdown("---")
st.caption("After testing, please change your Tastytrade password for security.")
