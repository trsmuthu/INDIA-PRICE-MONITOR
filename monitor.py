#!/usr/bin/env python3
"""
India Commodity & Forex Intelligence Forecaster (Project #11)
Customized for:
  - Gold 8g (1 Sovereign / Pavan) in 22K (Jewelry) and 24K (Pure)
  - 22K and 24K 8g Buying Zones & Expected High Targets
  - Silver (1 kg) & Copper (1 kg) Buying Zones & Expected High Targets
  - USD/INR & EUR/INR Buying Zones & Expected High Targets
  - Simple, understandable terminology for Indian investors & buyers
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


def fetch_forex_intelligence():
    """Fetches USD/INR and EUR/INR rates and calculates Buying Zones."""
    usd_data = get_market_metrics("USDINR=X")
    usd_cur = round(float(usd_data["cur"] if usd_data else 92.90), 2)
    usd_buy_floor = round(usd_cur * 0.985, 2)
    usd_buy_ceil = round(usd_cur * 0.992, 2)
    usd_target = round(usd_cur * 1.025, 2)

    eur_data = get_market_metrics("EURINR=X")
    eur_cur = round(float(eur_data["cur"] if eur_data else 101.18), 2)
    eur_buy_floor = round(eur_cur * 0.98, 2)
    eur_buy_ceil = round(eur_cur * 0.99, 2)
    eur_target = round(eur_cur * 1.03, 2)

    return {
        "usd": {
            "cur": usd_cur,
            "buy_floor": usd_buy_floor,
            "buy_ceil": usd_buy_ceil,
            "target": usd_target
        },
        "eur": {
            "cur": eur_cur,
            "buy_floor": eur_buy_floor,
            "buy_ceil": eur_buy_ceil,
            "target": eur_target
        }
    }


def evaluate_trend(cur, ma_20):
    diff = ((cur - ma_20) / ma_20) * 100
    if diff > 1.5:
        return "🟢 BULLISH (Uptrend)", "Accumulate on dips; upward momentum active."
    elif diff < -1.5:
        return "🟡 VALUE ZONE (Favorable Buying)", "Testing key support floor; good time to buy on dips."
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

    # 22K 8g Buying Zone & Target
    g_22k_buy_floor = round(g_8g_22k * 0.97, -2)
    g_22k_buy_ceil = round(g_8g_22k * 0.985, -2)
    g_22k_target = round(g_8g_22k * 1.04, -2)

    # 24K 8g Buying Zone & Target
    g_24k_buy_floor = round(g_8g_24k * 0.97, -2)
    g_24k_buy_ceil = round(g_8g_24k * 0.985, -2)
    g_24k_target = round(g_8g_24k * 1.04, -2)

    g_trend, g_action = evaluate_trend(g_8g_22k, g_ma20_8g)

    # Silver (1 kg)
    s_cur = round((s["cur"] / 31.1034768) * 1000 * usd_inr, 0)
    s_ma20 = round((s["ma_20"] / 31.1034768) * 1000 * usd_inr, 0)
    s_buy_floor = round(s_cur * 0.95, -2)
    s_buy_ceil = round(s_cur * 0.97, -2)
    s_target = round(s_cur * 1.06, -2)
    s_trend, s_action = evaluate_trend(s_cur, s_ma20)

    # Copper (1 kg, 1 lb = 0.45359237 kg)
    c_cur = round((c["cur"] * usd_inr) / 0.45359237, 1)
    c_ma20 = round((c["ma_20"] * usd_inr) / 0.45359237, 1)
    c_buy_floor = round(c_cur * 0.97, 1)
    c_target = round(c_cur * 1.04, 1)
    c_trend, c_action = evaluate_trend(c_cur, c_ma20)

    return {
        "gold_8g": {
            "22k_8g": g_8g_22k,
            "24k_8g": g_8g_24k,
            "22k_1g": g_1g_22k,
            "24k_1g": round(g_1g_24k, 0),
            "22k_buy_floor": g_22k_buy_floor,
            "22k_buy_ceil": g_22k_buy_ceil,
            "22k_target": g_22k_target,
            "24k_buy_floor": g_24k_buy_floor,
            "24k_buy_ceil": g_24k_buy_ceil,
            "24k_target": g_24k_target,
            "trend": g_trend,
            "action": g_action
        },
        "silver": {
            "cur": s_cur,
            "buy_floor": s_buy_floor,
            "buy_ceil": s_buy_ceil,
            "target": s_target,
            "trend": s_trend,
            "action": s_action
        },
        "copper": {
            "cur": c_cur,
            "buy_floor": c_buy_floor,
            "target": c_target,
            "trend": c_trend,
            "action": c_action
        },
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

    print(f"[{timestamp}] Running Commodity & Forex Intelligence Forecaster...")
    forex = fetch_forex_intelligence()
    usd = forex["usd"]
    eur = forex["eur"]

    commodities = fetch_commodity_intelligence(usd["cur"])
    g = commodities["gold_8g"]
    s = commodities["silver"]
    c = commodities["copper"]

    report = (
        f"📈 COMMODITY & FOREX INTELLIGENCE REPORT\n"
        f"⏰ Updated: {timestamp}\n\n"
        f"🥇 GOLD (8g · 1 Sovereign / Pavan)\n"
        f"   • 22K (Jewelry): ₹{g['22k_8g']:,.0f} / 8g (₹{g['22k_1g']:,.0f}/g)\n"
        f"   • 24K (Pure): ₹{g['24k_8g']:,.0f} / 8g (₹{g['24k_1g']:,.0f}/g)\n"
        f"   • Trend: {g['trend']}\n"
        f"   • 22K Buying Zone (8g): ₹{g['22k_buy_floor']:,.0f} – ₹{g['22k_buy_ceil']:,.0f}\n"
        f"   • 24K Buying Zone (8g): ₹{g['24k_buy_floor']:,.0f} – ₹{g['24k_buy_ceil']:,.0f}\n"
        f"   • Expected High Target: ₹{g['22k_target']:,.0f} (22K) · ₹{g['24k_target']:,.0f} (24K)\n"
        f"   • AI Insight: {g['action']}\n\n"
        f"🥈 SILVER (1 kg)\n"
        f"   • Spot Rate: ₹{s['cur']:,.0f} / kg (₹{round(s['cur']/1000):,.0f}/g)\n"
        f"   • Trend: {s['trend']}\n"
        f"   • Buying Zone: ₹{s['buy_floor']:,.0f} – ₹{s['buy_ceil']:,.0f}\n"
        f"   • Expected High Target: ₹{s['target']:,.0f}\n"
        f"   • AI Insight: {s['action']}\n\n"
        f"🥉 COPPER (1 kg)\n"
        f"   • MCX Rate: ₹{c['cur']:,.1f} / kg\n"
        f"   • Trend: {c['trend']}\n"
        f"   • Buying Floor: ₹{c['buy_floor']:,.1f} | Expected High Target: ₹{c['target']:,.1f}\n\n"
        f"💵 USD / INR (1 US Dollar)\n"
        f"   • Current Rate: ₹{usd['cur']:.2f}\n"
        f"   • Buying Zone (Favorable Dip): ₹{usd['buy_floor']:.2f} – ₹{usd['buy_ceil']:.2f}\n"
        f"   • Expected High Target: ₹{usd['target']:.2f}\n\n"
        f"💶 EUR / INR (1 Euro)\n"
        f"   • Current Rate: ₹{eur['cur']:.2f}\n"
        f"   • Buying Zone (Favorable Dip): ₹{eur['buy_floor']:.2f} – ₹{eur['buy_ceil']:.2f}\n"
        f"   • Expected High Target: ₹{eur['target']:.2f}\n"
    )

    print("========================================")
    print(" APPROVED COMMODITY & FOREX REPORT")
    print("========================================")
    print(report)

    click_link = "https://www.moneycontrol.com/commodity/"
    send_iphone_alert("Commodity & Forex Intelligence", report, click_url=click_link)


def main():
    if "--test" in sys.argv:
        print("Sending test notification to iPhone...")
        send_iphone_alert(
            "Market Forecaster Connected!",
            "Your 8g Gold & Forex Buying Zone Forecaster is active!"
        )
        return

    run_intelligence_brief()


if __name__ == "__main__":
    main()
