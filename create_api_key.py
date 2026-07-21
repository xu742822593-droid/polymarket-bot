import os
from py_clob_client.client import ClobClient

try:
    private_key = os.getenv("POLY_PRIVATE_KEY")

    if not private_key:
        raise Exception("Missing POLY_PRIVATE_KEY")

    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137,
        signature_type=1
    )

    creds = client.create_or_derive_api_creds()

    print("")
    print("========== POLYMARKET API ==========")
    print("")
    print("POLY_API_KEY=" + creds.api_key)
    print("POLY_API_SECRET=" + creds.api_secret)
    print("POLY_API_PASSPHRASE=" + creds.api_passphrase)
    print("")
    print("====================================")

except Exception as e:
    print("API Key generation failed:")
    print(e)
