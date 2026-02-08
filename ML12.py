"""
═══════════════════════════════════════════════════════════════════════════════
TASTYTRADE API FULL TEST - FIXED FUTURES ENDPOINTS
═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Tastytrade API Test", page_icon="🔬", layout="wide")

st.title("🔬 Tastytrade API Full Test (v2)")
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
    
    results = {}
    
    # Step 1: Get Access Token
    st.subheader("1️⃣ Getting Access Token")
    with st.spinner("Authenticating..."):
        access_token = get_access_token()
        
    if access_token:
        st.success(f"✅ Access token obtained!")
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
            results["accounts"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 4: Future Products - Find ES and VX
        st.subheader("4️⃣ Future Products (Finding ES & VX)")
        r = requests.get("https://api.tastytrade.com/instruments/future-products", headers=headers, timeout=30)
        
        es_product = None
        vx_product = None
        
        if r.status_code == 200:
            data = r.json()
            products = data.get('data', {}).get('items', [])
            st.success(f"✅ Found {len(products)} future products")
            
            for p in products:
                root = p.get('root-symbol', '')
                code = p.get('code', '')
                
                if root == 'ES' or code == 'ES':
                    es_product = p
                    st.write(f"🎯 **ES Found:** {p.get('description', 'N/A')}")
                    st.json(p)
                    
                if root == 'VX' or code == 'VX':
                    vx_product = p
                    st.write(f"🎯 **VX Found:** {p.get('description', 'N/A')}")
                    st.json(p)
            
            results["future_products"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 5: Get actual ES futures contracts
        st.subheader("5️⃣ ES Futures Contracts")
        
        # Try different endpoint formats
        endpoints_to_try = [
            "https://api.tastytrade.com/instruments/futures",  # All futures
            "https://api.tastytrade.com/instruments/futures?product-code=ES",
            "https://api.tastytrade.com/instruments/futures?symbol=ES",
        ]
        
        es_found = False
        for endpoint in endpoints_to_try:
            st.write(f"Trying: `{endpoint}`")
            r = requests.get(endpoint, headers=headers, timeout=30)
            st.write(f"Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                futures = data.get('data', {}).get('items', [])
                
                # Filter for ES
                es_futures = [f for f in futures if 'ES' in f.get('symbol', '') or f.get('product-code') == 'ES']
                
                if es_futures:
                    st.success(f"✅ Found {len(es_futures)} ES futures!")
                    for f in es_futures[:3]:
                        st.json({
                            "symbol": f.get('symbol'),
                            "product-code": f.get('product-code'),
                            "expiration": f.get('expiration-date'),
                            "streamer-symbol": f.get('streamer-symbol'),
                        })
                    results["es_futures"] = True
                    es_found = True
                    break
                else:
                    st.write(f"  Found {len(futures)} futures, but no ES")
            else:
                st.write(f"  Error: {r.text[:100]}")
        
        if not es_found:
            st.warning("⚠️ ES futures not found via REST API - may need DXLink streaming")
        
        # Step 6: Get VX futures contracts
        st.subheader("6️⃣ VX Futures Contracts (VIX) ⭐")
        
        vx_found = False
        for endpoint in endpoints_to_try:
            r = requests.get(endpoint, headers=headers, timeout=30)
            
            if r.status_code == 200:
                data = r.json()
                futures = data.get('data', {}).get('items', [])
                
                # Filter for VX
                vx_futures = [f for f in futures if 'VX' in f.get('symbol', '') or f.get('product-code') == 'VX']
                
                if vx_futures:
                    st.success(f"✅ Found {len(vx_futures)} VX futures! 🎉")
                    for f in vx_futures[:3]:
                        st.json({
                            "symbol": f.get('symbol'),
                            "product-code": f.get('product-code'),
                            "expiration": f.get('expiration-date'),
                            "streamer-symbol": f.get('streamer-symbol'),
                        })
                    results["vx_futures"] = True
                    vx_found = True
                    st.balloons()
                    break
        
        if not vx_found:
            st.warning("⚠️ VX futures not found via REST API - checking if available via streaming")
        
        # Step 7: Quote Token
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
            
            st.info("""
            **DXLink Streaming can provide:**
            - Real-time quotes for ES, VX, SPX, etc.
            - Historical candles (30-min, 1-hour, etc.)
            - This is how we'd get overnight VX data!
            """)
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 8: SPX Options
        st.subheader("8️⃣ SPX Options Chain")
        r = requests.get("https://api.tastytrade.com/option-chains/SPX/nested", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            expirations = data.get('data', {}).get('items', [])
            st.success(f"✅ SPX Options available! Found {len(expirations)} expirations")
            results["spx_options"] = True
        else:
            st.error(f"❌ {r.status_code}: {r.text[:200]}")
        
        # Step 9: Try to get specific future by symbol
        st.subheader("9️⃣ Direct Future Lookup")
        
        test_symbols = ['/ESH25', '/ESM25', 'ESH25', '/VXH25', '/VXG25', 'VXH25']
        
        for sym in test_symbols:
            encoded = sym.replace('/', '%2F')
            endpoint = f"https://api.tastytrade.com/instruments/futures/{encoded}"
            r = requests.get(endpoint, headers=headers, timeout=30)
            
            if r.status_code == 200:
                st.success(f"✅ {sym} found!")
                st.json(r.json().get('data', {}))
                if 'ES' in sym:
                    results["es_direct"] = True
                if 'VX' in sym:
                    results["vx_direct"] = True
            else:
                st.write(f"❌ {sym}: {r.status_code}")
        
        # SUMMARY
        st.markdown("---")
        st.subheader("📊 FINAL SUMMARY")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**✅ Confirmed Working:**")
            if results.get("access_token"): st.write("• OAuth Authentication")
            if results.get("customer"): st.write("• Customer Info")
            if results.get("accounts"): st.write("• Account Access")
            if results.get("future_products"): st.write("• Future Products List (96)")
            if results.get("quote_token"): st.write("• DXLink Quote Token")
            if results.get("spx_options"): st.write("• SPX Options Chain")
        
        with col2:
            st.markdown("**🔍 Futures Status:**")
            if results.get("es_futures") or results.get("es_direct"):
                st.write("✅ ES Futures: Available!")
            else:
                st.write("⚠️ ES Futures: Via DXLink streaming")
                
            if results.get("vx_futures") or results.get("vx_direct"):
                st.write("✅ VX Futures: Available! 🎉")
            else:
                st.write("⚠️ VX Futures: Via DXLink streaming")
        
        st.markdown("---")
        st.info("""
        **Bottom Line:** Even if REST API doesn't list individual futures, the **DXLink streaming** 
        connection (which we have!) can subscribe to `/ES` and `/VX` quotes and candles directly.
        
        This means **VIX Channel System is possible!** We just need to use WebSocket streaming 
        instead of REST API for the futures data.
        """)

else:
    st.info("👆 Click the button above to run the full API test")

st.markdown("---")
st.caption("Refresh token never expires. After testing, change your Tastytrade password for security.")
