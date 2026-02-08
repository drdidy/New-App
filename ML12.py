"""
═══════════════════════════════════════════════════════════════════════════════
TASTYTRADE API CAPABILITY TEST - STREAMLIT VERSION
═══════════════════════════════════════════════════════════════════════════════
Deploy this to Streamlit Cloud to test what data we can get from Tastytrade.

requirements.txt needs:
    streamlit
    tastytrade
    pytz
═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import asyncio
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Tastytrade API Test", page_icon="🔬", layout="wide")

st.title("🔬 Tastytrade API Capability Test")
st.markdown("---")

# Credentials
USERNAME = "okanlawondavid@gmail.com"
PASSWORD = "Jivydado8492@10"

def run_async(coro):
    """Helper to run async code in Streamlit."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def run_all_tests():
    """Run all Tastytrade API tests."""
    results = {}
    
    # 1. SESSION TEST
    st.subheader("1️⃣ Creating Session")
    try:
        from tastytrade import Session
        session = Session(USERNAME, PASSWORD)
        st.success(f"✅ Session created!")
        st.code(f"Session Token: {session.session_token}")
        st.code(f"Is Test: {session.is_test}")
        results['session'] = session
    except Exception as e:
        st.error(f"❌ Session failed: {e}")
        return results
    
    # 2. ACCOUNT TEST
    st.subheader("2️⃣ Checking Accounts")
    try:
        from tastytrade import Account
        accounts = await Account.a_get(session)
        st.success(f"✅ Found {len(accounts)} account(s)")
        for acc in accounts:
            st.code(f"Account: {acc.account_number}")
        results['accounts'] = accounts
    except Exception as e:
        st.error(f"❌ Account error: {e}")
    
    # 3. FUTURES TEST
    st.subheader("3️⃣ Checking Futures Access")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**ES Futures (S&P 500)**")
        from tastytrade.instruments import Future
        es_symbols = ['/ESH25', '/ESM25', '/ESZ24']
        for symbol in es_symbols:
            try:
                future = await Future.get(session, symbol)
                st.success(f"✅ {symbol}")
                st.json({
                    "symbol": future.symbol,
                    "streamer_symbol": getattr(future, 'streamer_symbol', 'N/A'),
                    "product_code": getattr(future, 'product_code', 'N/A'),
                })
                results['es_future'] = future
                break
            except Exception as e:
                st.warning(f"❌ {symbol}: {str(e)[:100]}")
    
    with col2:
        st.markdown("**VX Futures (VIX)**")
        vx_symbols = ['/VXH25', '/VXG25', '/VXJ25']
        for symbol in vx_symbols:
            try:
                future = await Future.get(session, symbol)
                st.success(f"✅ {symbol}")
                st.json({
                    "symbol": future.symbol,
                    "streamer_symbol": getattr(future, 'streamer_symbol', 'N/A'),
                    "product_code": getattr(future, 'product_code', 'N/A'),
                })
                results['vx_future'] = future
                break
            except Exception as e:
                st.warning(f"❌ {symbol}: {str(e)[:100]}")
    
    # 4. INDEX TEST
    st.subheader("4️⃣ Checking Index/Equity Data")
    from tastytrade.instruments import Equity
    
    test_symbols = ['SPY', 'QQQ', 'SPX', '$SPX.X', 'VIX', '$VIX.X', 'AAPL']
    cols = st.columns(4)
    
    for i, symbol in enumerate(test_symbols):
        with cols[i % 4]:
            try:
                equity = await Equity.get(session, symbol)
                st.success(f"✅ {symbol}")
                results[f'equity_{symbol}'] = equity
            except Exception as e:
                st.error(f"❌ {symbol}")
    
    # 5. OPTIONS TEST
    st.subheader("5️⃣ Checking SPX Options Chain")
    try:
        from tastytrade.instruments import get_option_chain
        chain = await get_option_chain(session, 'SPX')
        expirations = list(chain.keys())[:5]
        st.success(f"✅ SPX Options available - {len(chain)} expirations")
        st.write("Next 5 expirations:", expirations)
        
        if expirations:
            first_exp = expirations[0]
            strikes = chain[first_exp][:3]
            st.write(f"Sample strikes for {first_exp}:")
            for strike in strikes:
                st.code(f"Strike {strike.strike_price}: {strike.streamer_symbol}")
        results['options'] = chain
    except Exception as e:
        st.error(f"❌ Options error: {e}")
    
    # 6. STREAMING TEST
    st.subheader("6️⃣ Testing Real-Time Streaming")
    try:
        from tastytrade.streamer import DXLinkStreamer
        
        st.info("⏳ Connecting to DXLink streamer...")
        
        async with DXLinkStreamer(session) as streamer:
            st.success("✅ Connected to streamer!")
            
            # Try to get a quote
            test_symbols = ['SPY']
            await streamer.subscribe_quote(test_symbols)
            
            st.info(f"⏳ Waiting for {test_symbols} quote (10 sec timeout)...")
            
            try:
                quote = await asyncio.wait_for(streamer.get_event(), timeout=10.0)
                st.success("✅ Received quote!")
                st.json({
                    "symbol": quote.event_symbol,
                    "bid": quote.bid_price,
                    "ask": quote.ask_price,
                    "bid_size": quote.bid_size,
                    "ask_size": quote.ask_size,
                })
                results['quote'] = quote
            except asyncio.TimeoutError:
                st.warning("⚠️ No quote received (market may be closed)")
                
    except Exception as e:
        st.error(f"❌ Streaming error: {e}")
        st.code(str(e))
    
    # 7. CANDLES TEST
    st.subheader("7️⃣ Testing Historical Candles")
    try:
        from tastytrade.streamer import DXLinkStreamer
        
        async with DXLinkStreamer(session) as streamer:
            from_time = datetime.now() - timedelta(hours=24)
            
            st.info(f"⏳ Requesting candles from {from_time}...")
            
            # Try SPY candles
            await streamer.subscribe_candle('SPY', from_time, '30m')
            
            candles = []
            try:
                for _ in range(5):
                    candle = await asyncio.wait_for(streamer.get_event(), timeout=5.0)
                    candles.append(candle)
            except asyncio.TimeoutError:
                pass
            
            if candles:
                st.success(f"✅ Received {len(candles)} candles")
                for c in candles[:3]:
                    st.code(f"Time: {c.time} | O: {c.open} H: {c.high} L: {c.low} C: {c.close}")
                results['candles'] = candles
            else:
                st.warning("⚠️ No candles received")
                
    except Exception as e:
        st.error(f"❌ Candles error: {e}")
        st.code(str(e))
    
    return results

# Run button
st.markdown("---")
if st.button("🚀 Run All Tests", type="primary", use_container_width=True):
    with st.spinner("Running tests..."):
        results = run_async(run_all_tests())
    
    st.markdown("---")
    st.subheader("📊 Summary")
    
    summary = []
    if results.get('session'):
        summary.append("✅ Session: Working")
    if results.get('accounts'):
        summary.append("✅ Accounts: Accessible")
    if results.get('es_future'):
        summary.append("✅ ES Futures: Available")
    if results.get('vx_future'):
        summary.append("✅ VX Futures: Available (VIX channel possible!)")
    if results.get('options'):
        summary.append("✅ SPX Options: Available (can replace Polygon)")
    if results.get('quote'):
        summary.append("✅ Real-time Quotes: Working")
    if results.get('candles'):
        summary.append("✅ Historical Candles: Working")
    
    for s in summary:
        st.write(s)
    
    if len(summary) >= 5:
        st.success("🎉 Tastytrade can likely replace Yahoo Finance + Polygon!")
    else:
        st.warning("⚠️ Some features unavailable - may still need other data sources")

st.markdown("---")
st.caption("After testing, please change your Tastytrade password for security.")
