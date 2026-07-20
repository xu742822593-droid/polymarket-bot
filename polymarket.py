import os, json, logging
from datetime import datetime
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

logger = logging.getLogger(__name__)

def get_client():
    return ClobClient(
        host="https://clob.polymarket.com",
        key=os.getenv("POLY_PRIVATE_KEY"),
        chain_id=int(os.getenv("POLY_CHAIN_ID", "137")),
        creds=ApiCreds(
            api_key=os.getenv("POLY_API_KEY"),
            api_secret=os.getenv("POLY_API_SECRET"),
            api_passphrase=os.getenv("POLY_API_PASSPHRASE"),
        ),
        signature_type=2,
    )

client = get_client()

def search_markets(keyword, limit=4):
    try:
        data = client.get_markets()
        out = []
        for m in data.get("data", []):
            if m.get("active") and not m.get("closed"):
                if keyword.lower() in m["question"].lower():
                    out.append({
                        "question": m["question"][:80],
                        "condition_id": m["condition_id"],
                        "tokens": m.get("tokens", []),
                        "end_date": m.get("end_date_iso", "")[:10],
                    })
                    if len(out) >= limit:
                        break
        return out
    except Exception as e:
        logger.error(f"search_markets: {e}")
        print(f"search_markets error: {e}")
        return []

def get_price_info(token_id):
    try:
        book = client.get_order_book(token_id)
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        bid = float(bids[0]["price"]) if bids else None
        ask = float(asks[0]["price"]) if asks else None
        return {
            "bid": bid, "ask": ask,
            "mid": round((bid + ask) / 2, 4) if bid and ask else None,
            "spread": round(ask - bid, 4) if bid and ask else None,
        }
    except Exception as e:
        logger.error(f"get_price_info: {e}")
        return {}

def place_order(token_id, price, size, side="BUY"):
    try:
        _side = BUY if side == "BUY" else SELL
        args = OrderArgs(token_id=token_id, price=price, size=size, side=_side)
        signed = client.create_order(args)
        resp = client.post_order(signed, OrderType.GTC)
        record = {
            "order_id": resp.get("orderID"),
            "side": side, "price": price, "size": size,
            "status": resp.get("status", "LIVE"),
            "time": datetime.now().isoformat()[:16],
        }
        _save(record)
        return {"success": True, **record}
    except Exception as e:
        logger.error(f"place_order: {e}")
        return {"success": False, "error": str(e)}

def get_open_orders():
    try:
        return client.get_orders().get("data", [])
    except:
        return []

def cancel_all_orders():
    try:
        client.cancel_all()
        return True
    except:
        return False

def get_history(limit=8):
    return _load()[-limit:]

def _save(r):
    data = _load()
    with open("orders.json", "w") as f:
        json.dump(data + [r], f, indent=2)

def _load():
    try:
        with open("orders.json") as f:
            return json.load(f)
    except:
        return []
