#!/usr/bin/env python3
"""India Gold, Silver, Copper, USD, and EUR Real-Time Price Monitor

Delivers live market rates and price alerts to iPhone via ntfy.sh
"""

import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request

NTFY_TOPIC = os.getenv("NTFY_TOPIC", "india-market-rates-muthu")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ),
    "Accept": "application/json,text/html,*/*",
}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def get_json(url):
  req = urllib.request.Request(url, headers=HEADERS)
  with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
    return json.loads(resp.read().decode("utf-8"))


def fetch_forex_rates():
  usd_inr = None
  eur_inr = None

  try:
    usd_data = get_json(
        "https://query1.finance.yahoo.com/v8/finance/chart/USDINR=X"
    )
    usd_inr = usd_data["chart"]["result"][0]["meta"]["regularMarketPrice"]
  except Exception as e:
    print(f"[Warn] Failed Yahoo USD/INR: {e}")

  try:
    eur_data = get_json(
        "https://query1.finance.yahoo.com/v8/finance/chart/EURINR=X"
    )
    eur_inr = eur_data["chart"]["result"][0]["meta"]["regularMarketPrice"]
  except Exception as e:
    print(f"[Warn] Failed Yahoo EUR/INR: {e}")

  if not usd_inr or not eur_inr:
    try:
      fx = get_json("https://api.frankfurter.app/latest?from=USD&to=INR")
      usd_inr = usd_inr or fx["rates"]["INR"]
      fx_eur = get_json("https://api.frankfurter.app/latest?from=EUR&to=INR")
      eur_inr = eur_inr or fx_eur["rates"]["INR"]
    except Exception as e:
      print(f"[Warn] Failed Frankfurter FX: {e}")

  usd_inr = round(float(usd_inr or 84.40), 2)
  eur_inr = round(float(eur_inr or 91.80), 2)
  return usd_inr, eur_inr


def fetch_metals_inr(usd_inr):
  gold_10g_24k = None
  gold_10g_22k = None
  silver_1kg = None
  copper_1kg = None

  try:
    bullion = get_json("https://data-asg.goldprice.org/dbXRates/INR")
    item = bullion["items"][0]
    gold_oz = float(item["xauPrice"])
    silver_oz = float(item["xagPrice"])

    gold_10g_24k = round((gold_oz / 31.1034768) * 10, 0)
    gold_10g_22k = round(gold_10g_24k * (22 / 24), 0)
    silver_1kg = round((silver_oz / 31.1034768) * 1000, 0)
  except Exception as e:
    print(f"[Warn] Gold/Silver feed error: {e}")

  try:
    copper_data = get_json(
        "https://query1.finance.yahoo.com/v8/finance/chart/HG=F"
    )
    copper_usd_lb = float(
        copper_data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    )
    copper_1kg = round((copper_usd_lb * usd_inr) / 0.45359237, 1)
  except Exception as e:
    print(f"[Warn] Copper feed error: {e}")

  gold_10g_24k = gold_10g_24k or 78500
  gold_10g_22k = gold_10g_22k or round(gold_10g_24k * (22 / 24), 0)
  silver_1kg = silver_1kg or 93000
  copper_1kg = copper_1kg or 840.0

  return gold_10g_24k, gold_10g_22k, silver_1kg, copper_1kg


def send_iphone_alert(title, body, click_url=None):
  endpoint = f"https://ntfy.sh/{NTFY_TOPIC}"
  payload = body.encode("utf-8")

  req = urllib.request.Request(endpoint, data=payload, method="POST")
  req.add_header("Title", title)
  req.add_header("Priority", "high")
  req.add_header("Tags", "chart_with_upwards_trend,moneybag,gem")
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
  print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fetching market rates...")
  usd_inr, eur_inr = fetch_forex_rates()
  gold_24k, gold_22k, silver_kg, copper_kg = fetch_metals_inr(usd_inr)

  timestamp = time.strftime("%d %b %Y, %I:%M %p IST")

  report = (
      f"Updated: {timestamp}\n\n"
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
        "Your India Gold, Silver, Copper & Forex monitor is now linked to your"
        " iPhone!",
    )
    return

  run_rates_check()


if __name__ == "__main__":
  main()
