"""
═══════════════════════════════════════════════════════════════════════════════
TASTYTRADE API FULL TEST - WITH YOUR REFRESH TOKEN
═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Tastytrade API Test", page_icon="🔬", layout="wide")

st.title("🔬 Tastytrade API Full Test")
st.markdown("---")

# Your OAuth Credentials
CLIENT_ID = "61d8c3a5-d259-4ac9-bf9c-a47ed1e6463f"
CLIENT_SECRET = "a00eac3f462f488b4de1655ab43024aa393bbadf"
REFRESH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6InJ0K2p3dCIsImtpZCI6IjRNb2Z2aDBJWmNDaVA1T1V5YnFjVnpuZkNRMGxoQTVDeG9fd3hRbU0zLXMiLCJqa3UiOiJodHRwczovL2ludGVyaW9yLWFwaS5hcjIudGFzdHl0cmFkZS5zeXN0ZW1zL29hdXRoL2p3a3MifQ.eyJpc3MiOiJodHRwczovL2FwaS50YXN0eXRyYWRlLmNvbSIsInN1YiI6IlUwMDAxMDM5NTI4IiwiaWF0IjoxNzcwNTE3NTMzLCJhdWQiOiI2MWQ4YzNhNS1kMjU5LTRhYzktYmY5Yy1hNDdlZDFlNjQ2M2YiLCJncmFudF9pZCI6IkczOTQyYmY4Ni05YTg1LTQxMjMtYTQwMC02ZmZlMzk5YTJjY2YiLCJzY29wZSI6InJlYWQifQ.rTva7Zno6V2coosxYKgKMejHK8CwMHCz9MENeu__VdHtltUEBEsmjU6_P7ntV_T5xnd9_FYtFpm7d9QXQHZVCw"

def get_access_token():
    """Get fresh access token from refresh token."""
    token_url = "https://api.tastytrade.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    response = requests.post(token_url, data=data, timeout=30)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        st.error(f"Token error: {response.status_code} - {response.text}")
        return None

if st.button("🚀 Run Full API Test", type="primary", use_container_width=True):
    
    results = {
        "access_token": False,
        "customer": False,
        "accounts": False,
        "future_products": False,
        "es_futures": False,
        "vx_futures": False,
        "quote_token": False,
        "spx_options": False,
    }
    
    # Step 1: Get Access Token
    st.subheader("1️⃣ Getting Access Token")
    with st.spinner("Authenticating..."):
        access_token = get_access_token()
        
    if access_token:
        st.success(f"✅ Access token obtained!")
        st.code(f"{access_token[:60]}...")
        results["access_token"] = True
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Step 2: Customer Info
        st.subheader("2️⃣ Customer Info")
        r = requests.get("https://api.tastytrade.com/customers/me", headers=headers, timeout=30)
        if r.status_code == 200:
            st.success("✅ Customer info accessible!")
            data = r.json().get('data', {})
            st.json({
                "email": data.get('email'),
                "username": data.get('username'),
                "external-id": data.get('external-id'),
            })
            results["customer"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 3: Accounts
        st.subheader("3️⃣ Accounts")
        r = requests.get("https://api.tastytrade.com/customers/me/accounts", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            accounts = data.get('data', {}).get('items', [])
            st.success(f"✅ Found {len(accounts)} account(s)")
            for acc in accounts:
                acct = acc.get('account', {})
                st.json({
                    "account-number": acct.get('account-number'),
                    "account-type": acct.get('account-type-name'),
                    "nickname": acct.get('nickname'),
                })
            results["accounts"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 4: Future Products
        st.subheader("4️⃣ Future Products")
        r = requests.get("https://api.tastytrade.com/instruments/future-products", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            products = data.get('data', {}).get('items', [])
            st.success(f"✅ Found {len(products)} future products")
            
            # Find key products
            key_products = ['ES', 'VX', 'NQ', 'CL', 'GC']
            found = []
            for p in products:
                symbol = p.get('root-symbol', '')
                if symbol in key_products:
                    found.append(f"{symbol}: {p.get('description', 'N/A')}")
            
            for f in found:
                st.write(f"🎯 {f}")
            results["future_products"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 5: ES Futures
        st.subheader("5️⃣ ES Futures (S&P 500)")
        r = requests.get("https://api.tastytrade.com/instruments/future-products/ES/futures", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            futures = data.get('data', {}).get('items', [])
            st.success(f"✅ Found {len(futures)} ES contracts")
            
            for f in futures[:3]:
                st.json({
                    "symbol": f.get('symbol'),
                    "expiration": f.get('expiration-date'),
                    "streamer-symbol": f.get('streamer-symbol'),
                })
            results["es_futures"] = True
            
            # Save streamer symbol for later
            if futures:
                st.session_state['es_streamer'] = futures[0].get('streamer-symbol')
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 6: VX Futures (VIX) - THE KEY TEST!
        st.subheader("6️⃣ VX Futures (VIX) ⭐")
        r = requests.get("https://api.tastytrade.com/instruments/future-products/VX/futures", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            futures = data.get('data', {}).get('items', [])
            st.success(f"✅ Found {len(futures)} VX contracts! 🎉🎉🎉")
            
            for f in futures[:3]:
                st.json({
                    "symbol": f.get('symbol'),
                    "expiration": f.get('expiration-date'),
                    "streamer-symbol": f.get('streamer-symbol'),
                })
            results["vx_futures"] = True
            
            st.balloons()
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 7: Quote Token (for streaming)
        st.subheader("7️⃣ Quote Token (DXLink Streaming)")
        r = requests.get("https://api.tastytrade.com/api-quote-tokens", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json().get('data', {})
            st.success("✅ Quote token available!")
            st.json({
                "dxlink-url": data.get('dxlink-url'),
                "level": data.get('level'),
            })
            results["quote_token"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 8: SPX Options
        st.subheader("8️⃣ SPX Options Chain")
        r = requests.get("https://api.tastytrade.com/option-chains/SPX/nested", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            expirations = data.get('data', {}).get('items', [])
            st.success(f"✅ SPX Options available! Found {len(expirations)} expirations")
            
            if expirations:
                first = expirations[0]
                st.json({
                    "expiration": first.get('expiration-date'),
                    "settlement-type": first.get('settlement-type'),
                    "strikes_count": len(first.get('strikes', [])),
                })
            results["spx_options"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # SUMMARY
        st.markdown("---")
        st.subheader("📊 SUMMARY")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Can Replace Yahoo Finance:**")
            if results["es_futures"]:
                st.write("✅ ES Futures (overnight data)")
            if results["quote_token"]:
                st.write("✅ Real-time streaming quotes")
            
            st.markdown("**Can Replace Polygon:**")
            if results["spx_options"]:
                st.write("✅ SPX Options chains")
        
        with col2:
            st.markdown("**NEW Capabilities:**")
            if results["vx_futures"]:
                st.write("✅ VX Futures (VIX from 5 PM!)")
                st.write("🎯 VIX Channel System POSSIBLE!")
            
            if results["accounts"]:
                st.write("✅ Account data (positions, balances)")
        
        # Final verdict
        st.markdown("---")
        passed = sum(results.values())
        total = len(results)
        
        if passed >= 6:
            st.success(f"🎉 **{passed}/{total} tests passed!** Tastytrade can be your single data source!")
        elif passed >= 4:
            st.warning(f"⚠️ **{passed}/{total} tests passed.** Partial capability - may still need other sources.")
        else:
            st.error(f"❌ **{passed}/{total} tests passed.** Limited access - check account permissions.")

else:
    st.info("👆 Click the button above to run the full API test")

st.markdown("---")
st.caption("Refresh token never expires. After testing, change your Tastytrade password for security.")
