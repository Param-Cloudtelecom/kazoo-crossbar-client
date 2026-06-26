"""
example.py - basic usage of KazooClient against a KAZOO Crossbar API.
"""
from kazoo_client import KazooClient

client = KazooClient(
    base_url="https://crossbar.example.com:8443/v2",
    account_name="acme",
    username="admin",
    password="changeme",
)

client.authenticate()
print("Authenticated, account_id:", client.account_id)

devices = client.list_devices()
print(f"{len(devices)} devices provisioned")

new_device = client.create_device(
    device_name="Reception Desk Phone",
    sip_username="1050",
    sip_password="a-strong-random-password",
)
print("Created device:", new_device["id"])

cdrs = client.get_cdrs()
print(f"{len(cdrs)} recent CDRs")
