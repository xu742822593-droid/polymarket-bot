from py_clob_client.client import ClobClient

PRIVATE_KEY = 0xcff40796843e9d54dc0942d361cada6701bce32332cb692fb727c5d9e9d834bf

client = ClobClient(
    host="https://clob.polymarket.com",
    key=PRIVATE_KEY,
    chain_id=137,
)

creds = client.create_or_derive_api_creds()
print("POLY_API_KEY=" + creds.api_key)
print("POLY_API_SECRET=" + creds.api_secret)
print("POLY_API_PASSPHRASE=" + creds.api_passphrase)
print("POLY_PRIVATE_KEY=" + PRIVATE_KEY)

