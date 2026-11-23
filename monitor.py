#!/usr/bin/env python3
"""
India Gold, Silver, Copper, USD, and EUR Real-Time Price Monitor
Delivers live market rates and price alerts to iPhone via ntfy.sh
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


def get_yahoo_chart_price(sym):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
    try:
        data = get_json(url)
        return float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except Exception as e:
        print(f"[Warn] Yahoo query2 failed for {sym}: {e}")
        return None


def fetch_forex_rates():
    """Fetches USD/INR and EUR/INR rates."""
    usd_inr = get_yahoo_chart_price("USDINR=X")
    eur_inr = get_yahoo_chart_price("EURINR=X")

    # Fallback to Frankfurter if needed
    if not usd_inr or not eur_inr:
        try:
            fx = get_json("https://api.frankfurter.app/latest?from=USD&to=INR,EUR")
            usd_inr = usd_inr or float(fx["rates"]["INR"])
            eur_to_usd = float(fx["rates"]["EUR"])
            eur_inr = eur_inr or round(usd_inr / eur_to_usd, 2)
        except Exception as e:
            print(f"[Warn] Frankfurter FX failed: {e}")

    usd_inr = round(float(usd_inr or 92.68), 2)
    eur_inr = round(float(eur_inr or 101.40), 2)
    return usd_inr, eur_inr


def fetch_metals_inr(usd_inr):
    """Fetches Gold, Silver, and Copper spot rates converted to INR."""
    gold_oz = get_yahoo_chart_price("GC=F") or 3660.0
    silver_oz = get_yahoo_chart_price("SI=F") or 43.5
    copper_lb = get_yahoo_chart_price("HG=F") or 5.68

    # 1 Troy Ounce = 31.1034768 grams
    gold_10g_24k = round((gold_oz / 31.1034768) * 10 * usd_inr, 0)
    gold_10g_22k = round(gold_10g_24k * (22 / 24), 0)
    silver_1kg = round((silver_oz / 31.1034768) * 1000 * usd_inr, 0)
    # 1 lb = 0.45359237 kg
    copper_1kg = round((copper_lb * usd_inr) / 0.45359237, 1)

    return gold_10g_24k, gold_10g_22k, silver_1kg, copper_1kg


def send_iphone_alert(title, body, click_url=None):
    """Pushes notification to iPhone via ntfy.sh."""
    endpoint = f"https://ntfy.sh/{NTFY_TOPIC}"
    payload = body.encode("utf-8")
    
    req = urllib.request.Request(endpoint, data=payload, method="POST")
    clean_title = title.encode("ascii", "ignore").decode("ascii")
    req.add_header("Title", clean_title)
    req.add_header("Priority", "urgent")
    req.add_header("Tags", "moneybag,chart_with_upwards_trend,gem")
    if click_url:
        req.add_header("Click", click_url)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[PUSH SENT] -> iPhone ({NTFY_TOPIC})")
            return True
    except Exception as e:
        print(f"[FAILED TO PUSH] {e}")
        return False


def run_rates_check():
    # Accurate IST timestamp
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist)
    timestamp = now_ist.strftime("%d %b %Y, %I:%M %p IST")

    print(f"[{timestamp}] Fetching live market rates...")
    usd_inr, eur_inr = fetch_forex_rates()
    gold_24k, gold_22k, silver_kg, copper_kg = fetch_metals_inr(usd_inr)

    report = (
        f"📊 India Metals & Forex Rates\n"
        f"⏰ Updated: {timestamp}\n\n"
        f"🥇 Gold (24K): ₹{gold_24k:,.0f} / 10g\n"
        f"🥇 Gold (22K): ₹{gold_22k:,.0f} / 10g\n"
        f"🥈 Silver: ₹{silver_kg:,.0f} / kg\n"
        f"🥉 Copper: ₹{copper_kg:,.1f} / kg\n\n"
        f"💵 USD / INR: ₹{usd_inr:.2f}\n"
        f"💶 EUR / INR: ₹{eur_inr:.2f}\n"
    )

    print("========================================")
    print(" INDIA METALS & FOREX RATES")
    print("========================================")
    print(report)

    click_link = "https://www.moneycontrol.com/commodity/"
    send_iphone_alert("India Metals & Forex Rates", report, click_url=click_link)


def main():
    if "--test" in sys.argv:
        print("Sending test notification to iPhone...")
        send_iphone_alert(
            "Market Monitor Connected!",
            "Your India Gold, Silver, Copper & Forex monitor is now linked to your iPhone!"
        )
        return

    # Single run mode for GitHub Actions or cron
    run_rates_check()


if __name__ == "__main__":
    main()
