import os
from py_clob_client.client import ClobClient

PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY")

client = ClobClient(
    host="https://clob.polymarket.com",
    key=PRIVATE_KEY,
    chain_id=137,
)

creds = client.create_or_derive_api_creds()
print("POLY_API_KEY=" + creds.api_key)
print("POLY_API_SECRET=" + creds.api_secret)
print("POLY_API_PASSPHRASE=" + creds.api_passphrase)
