# kazoo-crossbar-client

A lightweight Python client for **2600Hz's KAZOO** platform's Crossbar REST
API — provisioning devices, querying CDRs, and triggering click-to-call,
at the platform-API layer rather than talking to FreeSWITCH/Kamailio
directly.

## Why this is a different layer than the other repos here

[`freeswitch-cloud-pbx`](https://github.com/Param-Cloudtelecom/freeswitch-cloud-pbx)
and [`kamailio-sbc-router`](https://github.com/Param-Cloudtelecom/kamailio-sbc-router)
work at the raw telecom-core layer — dialplan XML, ESL, `kamailio.cfg`
routing logic. KAZOO is itself built on FreeSWITCH + Kamailio, but wraps
all of that behind **Crossbar**, an account/device/callflow-oriented REST
API. Working with both layers matters in practice: Crossbar is what a
provisioning UI or mobile app talks to day-to-day, but understanding what's
actually happening underneath it (the other repos here) is what lets you
actually debug it when something breaks.

## What it does

- **Auth** — Crossbar's `user_auth` flow (MD5 credential hash → short-lived
  `X-Auth-Token`), handled transparently on first request.
- **Devices** — list and provision SIP devices/extensions under an account.
- **Call origination** — trigger a click-to-call (`quickcall`) from a
  provisioned device to an external number.
- **CDRs** — pull recent call detail records for an account.

## Usage

```python
from kazoo_client import KazooClient

client = KazooClient(
    base_url="https://crossbar.example.com:8443/v2",
    account_name="acme",
    username="admin",
    password="changeme",
)

client.authenticate()

device = client.create_device(
    device_name="Reception Desk Phone",
    sip_username="1050",
    sip_password="a-strong-random-password",
)

client.originate_call(device_id=device["id"], to_number="14165551234")

recent_cdrs = client.get_cdrs()
```

See [`example.py`](example.py) for a complete runnable script.

## Install

```bash
pip install -r requirements.txt
```

## What I'd add next

- Automatic auth-token refresh on expiry instead of requiring a manual
  re-`authenticate()` call
- Pagination handling for `get_cdrs()` on accounts with high call volume
- A thin CLI (`kazoo-cli devices list`, `kazoo-cli call <device> <number>`)
  on top of this client for quick manual operations
