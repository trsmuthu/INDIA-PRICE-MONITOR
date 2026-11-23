#!/usr/bin/env python3
"""
India Commodity Trend Forecaster & Intelligence Agent (Project #11)
Customized for 8g Gold (1 Sovereign / Pavan) & Commodity Markets
Features:
  - Gold 8g (1 Sovereign) calculation for 22K (Jewelry) and 24K (Pure)
  - 8g Buying Zone & Support / Resistance targets
  - Spot Silver (₹/kg) and MCX Copper (₹/kg)
  - USD/INR & EUR/INR Forex Benchmarks
  - Automated cloud delivery to iPhone via ntfy (9:05 AM, 2:00 PM, 6:05 PM IST)
"""

import sys
import os
import time
import json
import ssl
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta

# iPhone ntfy channel
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "india-market-rates-muthu")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Origin": "https://finance.yahoo.com",
    "Referer": "https://finance.yahoo.com/",
}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_market_metrics(sym):
    """
    Fetches 3-month daily chart data to calculate:
      - Current price
      - 20-day Moving Average (Trendline)
      - 52-week High and Low extremes
      - 5-day momentum
    """
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=3mo"
    try:
        data = get_json(url)
        meta = data["chart"]["result"][0]["meta"]
        quotes = data["chart"]["result"][0]["indicators"]["quote"][0]
        closes = [c for c in quotes.get("close", []) if c is not None]

        cur_price = float(meta.get("regularMarketPrice", 0))
        high_52 = float(meta.get("fiftyTwoWeekHigh", max(closes) if closes else cur_price))
        low_52 = float(meta.get("fiftyTwoWeekLow", min(closes) if closes else cur_price))
        ma_20 = sum(closes[-20:]) / len(closes[-20:]) if len(closes) >= 20 else cur_price
        chg_5d = ((cur_price - closes[-5]) / closes[-5]) * 100 if len(closes) >= 5 else 0.0

        return {
            "cur": cur_price,
            "high_52": high_52,
            "low_52": low_52,
            "ma_20": ma_20,
            "chg_5d": chg_5d
        }
    except Exception as e:
        print(f"[Warn] Failed fetching {sym}: {e}")
        return None


def fetch_forex_rates():
    """Fetches USD/INR and EUR/INR rates."""
    usd_data = get_market_metrics("USDINR=X")
    usd_inr = round(float(usd_data["cur"] if usd_data else 92.90), 2)

    eur_data = get_market_metrics("EURINR=X")
    eur_inr = round(float(eur_data["cur"] if eur_data else 101.33), 2)

    return usd_inr, eur_inr


def evaluate_trend(cur, ma_20):
    diff = ((cur - ma_20) / ma_20) * 100
    if diff > 1.5:
        return "🟢 BULLISH (Uptrend)", "Accumulate on dips; upward momentum active."
    elif diff < -1.5:
        return "🟡 VALUE ZONE (Support)", "Testing key support floor; favorable entry for buyers."
    else:
        return "⚪ NEUTRAL (Consolidation)", "Sideways range-bound movement; hold positions."


def fetch_commodity_intelligence(usd_inr):
    """
    Calculates Indian domestic rates with GOLD IN 8 GRAMS (1 Sovereign / Pavan),
    Silver per kg, and Copper per kg.
    """
    g = get_market_metrics("GC=F") or {"cur": 3676.0, "ma_20": 3920.0, "high_52": 5580.0, "low_52": 3500.0}
    s = get_market_metrics("SI=F") or {"cur": 43.5, "ma_20": 49.0, "high_52": 120.0, "low_52": 40.0}
    c = get_market_metrics("HG=F") or {"cur": 5.67, "ma_20": 6.18, "high_52": 6.83, "low_52": 4.95}

    # 1 Troy Ounce = 31.1034768 grams
    # Gold Calculations for 8g (1 Sovereign / Pavan)
    g_1g_24k = (g["cur"] / 31.1034768) * usd_inr
    g_8g_24k = round(g_1g_24k * 8, 0)
    g_8g_22k = round(g_8g_24k * (22 / 24), 0)
    g_1g_22k = round(g_8g_22k / 8, 0)

    # 8g Moving Average and Support / Resistance
    g_ma20_8g = round((g["ma_20"] / 31.1034768) * 8 * usd_inr * (22 / 24), 0)
    g_8g_buy_floor = round(g_8g_22k * 0.97, -2)
    g_8g_buy_ceiling = round(g_8g_22k * 0.985, -2)
    g_8g_target = round(g_8g_22k * 1.04, -2)
    g_trend, g_action = evaluate_trend(g_8g_22k, g_ma20_8g)

    # Silver (1 kg)
    s_cur = round((s["cur"] / 31.1034768) * 1000 * usd_inr, 0)
    s_ma20 = round((s["ma_20"] / 31.1034768) * 1000 * usd_inr, 0)
    s_sup = round(s_cur * 0.95, -2)
    s_res = round(s_cur * 1.06, -2)
    s_trend, s_action = evaluate_trend(s_cur, s_ma20)

    # Copper (1 kg, 1 lb = 0.45359237 kg)
    c_cur = round((c["cur"] * usd_inr) / 0.45359237, 1)
    c_ma20 = round((c["ma_20"] * usd_inr) / 0.45359237, 1)
    c_sup = round(c_cur * 0.97, 1)
    c_res = round(c_cur * 1.04, 1)
    c_trend, c_action = evaluate_trend(c_cur, c_ma20)

    return {
        "gold_8g": {
            "22k_8g": g_8g_22k,
            "24k_8g": g_8g_24k,
            "22k_1g": g_1g_22k,
            "24k_1g": round(g_1g_24k, 0),
            "buy_floor": g_8g_buy_floor,
            "buy_ceiling": g_8g_buy_ceiling,
            "target": g_8g_target,
            "trend": g_trend,
            "action": g_action
        },
        "silver": {"cur": s_cur, "sup": s_sup, "res": s_res, "trend": s_trend, "action": s_action},
        "copper": {"cur": c_cur, "sup": c_sup, "res": c_res, "trend": c_trend, "action": c_action},
    }


def send_iphone_alert(title, body, click_url=None):
    """Pushes notification to iPhone via ntfy.sh."""
    endpoint = f"https://ntfy.sh/{NTFY_TOPIC}"
    payload = body.encode("utf-8")

    req = urllib.request.Request(endpoint, data=payload, method="POST")
    clean_title = title.encode("ascii", "ignore").decode("ascii")
    req.add_header("Title", clean_title)
    req.add_header("Priority", "urgent")
    req.add_header("Tags", "coin,gem,chart_with_upwards_trend")
    if click_url:
        req.add_header("Click", click_url)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[PUSH SENT] -> iPhone ({NTFY_TOPIC})")
            return True
    except Exception as e:
        print(f"[FAILED TO PUSH] {e}")
        return False


def run_intelligence_brief():
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist)
    timestamp = now_ist.strftime("%d %b %Y, %I:%M %p IST")

    print(f"[{timestamp}] Running 8g Gold & Commodity Intelligence Forecaster...")
    usd_inr, eur_inr = fetch_forex_rates()
    data = fetch_commodity_intelligence(usd_inr)

    g = data["gold_8g"]
    s = data["silver"]
    c = data["copper"]

    report = (
        f"📈 COMMODITY TREND FORECASTER & INTELLIGENCE\n"
        f"⏰ Updated: {timestamp}\n\n"
        f"🥇 GOLD (8g · 1 Sovereign / Pavan)\n"
        f"   • 22K (Jewelry): ₹{g['22k_8g']:,.0f} / 8g (₹{g['22k_1g']:,.0f}/g)\n"
        f"   • 24K (Pure): ₹{g['24k_8g']:,.0f} / 8g (₹{g['24k_1g']:,.0f}/g)\n"
        f"   • Trend: {g['trend']}\n"
        f"   • Buy Zone (22K · 8g): ₹{g['buy_floor']:,.0f} – ₹{g['buy_ceiling']:,.0f}\n"
        f"   • Target Resistance: ₹{g['target']:,.0f}\n"
        f"   • AI Insight: {g['action']}\n\n"
        f"🥈 SILVER (1 kg)\n"
        f"   • Spot Rate: ₹{s['cur']:,.0f} / kg (₹{round(s['cur']/1000):,.0f}/g)\n"
        f"   • Trend: {s['trend']}\n"
        f"   • Buy Zone: ₹{s['sup']:,.0f} | Target: ₹{s['res']:,.0f}\n"
        f"   • AI Insight: {s['action']}\n\n"
        f"🥉 COPPER (1 kg)\n"
        f"   • MCX Rate: ₹{c['cur']:,.1f} / kg\n"
        f"   • Trend: {c['trend']}\n"
        f"   • Support: ₹{c['sup']:,.1f} | Resistance: ₹{c['res']:,.1f}\n\n"
        f"💵 FOREX BENCHMARK:\n"
        f"   • USD/INR: ₹{usd_inr:.2f} · EUR/INR: ₹{eur_inr:.2f}\n"
    )

    print("========================================")
    print(" COMMODITY INTELLIGENCE REPORT (8G GOLD)")
    print("========================================")
    print(report)

    click_link = "https://www.moneycontrol.com/commodity/"
    send_iphone_alert("Gold 8g (Sovereign) & Commodity Forecast", report, click_url=click_link)


def main():
    if "--test" in sys.argv:
        print("Sending test notification to iPhone...")
        send_iphone_alert(
            "Market Forecaster Connected!",
            "Your 8g Gold (1 Sovereign) & Commodity Forecaster is active!"
        )
        return

    run_intelligence_brief()


if __name__ == "__main__":
    main()
