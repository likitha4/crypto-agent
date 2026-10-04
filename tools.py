import requests
import os
BACKEND_URL = os.getenv("BACKEND_URL","http://localhost:8000")

def get_coin_prices(coin_ids:list = None):

    """ 
    Get live prices.
    1. Try CoinGecko first
    2. If rate-limited or fails->fall back to your backend /coins
    """
    if not coin_ids:
        coin_ids = ["bitcoin","ethereum","solana","ripple","cardano"]
    try:
        ids = ",".join(coin_ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=inr&include_24hr_change=true"
        response = requests.get(url,timeout= 6)
        if response.status_code ==429:
            raise Exception("CoinGecko rate limit")

        response.raise_for_status()
        data= response.json()
        print("✅ From Coingecko")
        return {"source":"coingecko", "prices":data}

    except Exception as e:
        print(f"⚠️ CoinGecko failed:{e}")
        print(" ➡️ Falling back to backend...")

        try:
            res= requests.get(f"{BACKEND_URL}/coins", timeout=8)
            res.raise_for_status()
            coins = res.json()

            simplified = {}
            for coin in coins:
                simplified[coin["id"]]={
                    "inr": coin.get("current_price"),
                    "inr_24h_change": coin.get("price_change_percentage_24h")
                }
            print("✅ From backend (cached)")
            return {"source":"backend", "prices": simplified}
        
        except Exception as backend_error:
            return {
                "source":"none",
                "error":f"Both failed. Backend error :{str(backend_error)}"
            }

def suggest_coins(limit: int = 5):
    """
    Suggest some interesting coins based on market data.
    Uses your backend /coins endpoint (already cached) to avoid rate limts.

    """
    try:
        res = requests.get(f"{BACKEND_URL}/coins", timeout = 8)
        res.raise_for_status()
        coins = res.json()

        suggestions = []
        for coin in coins:
            coin_id = coin.get("id","")
            if coin_id in ["bitcoin", "ethereum"]:
                continue

            market_cap_rank = coin.get("market_cap_rank") or 999
            volume = coin.get("total_volume") or 0
            change_24h = coin.get("price_change_percentage_24h")

            if market_cap_rank <=100 and volume >10_000_000:
                suggestions.append({
                    "id":coin_id,
                    "name":coin.get("name"),
                    "symbol":coin.get("symbol"),
                    "price": coin.get("current_price"),
                    "change_24h": change_24h,
                    "market_cap_rank":market_cap_rank,
                    "volume":volume
                })

            if len(suggestions)>=limit:
                break
            if not suggestions:
                return {
                    "source":"backend",
                    "suggestions":[],
                    "message":"No coins matched filters; try relaxing volume/rank rules"
                }
        return {
            "source":"backend",
            "suggestions":suggestions
        }
    except Exception as e:
        return {
            "source":"none",
            "error":f"Could not fetch suggestions: {str(e)}"
        }