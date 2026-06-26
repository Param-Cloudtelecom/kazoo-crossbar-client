"""
kazoo_client.client

A lightweight Python client for 2600Hz's KAZOO platform Crossbar REST API.

KAZOO is built on FreeSWITCH + Kamailio under the hood, but exposes a
high-level, account/device/callflow-oriented REST API (Crossbar) instead of
raw ESL or dialplan XML. This client wraps the handful of Crossbar
endpoints needed for day-to-day provisioning and call automation, so a
provisioning UI or automation script doesn't need to hand-build Crossbar
requests/auth tokens itself.

Docs: https://docs.2600hz.com/dev/ (Crossbar API reference)
"""
import requests


class KazooAuthError(Exception):
    pass


class KazooClient:
    def __init__(self, base_url: str, account_name: str, username: str, password: str):
        """
        base_url: e.g. https://crossbar.example.com:8443/v2
        """
        self.base_url = base_url.rstrip("/")
        self.account_name = account_name
        self.username = username
        self.password = password
        self.auth_token = None
        self.account_id = None
        self._session = requests.Session()

    def authenticate(self):
        """
        Crossbar's user-auth flow: POST credentials (md5 of account/user/pass
        per the Crossbar auth spec) and receive a short-lived auth token used
        on every subsequent request via the X-Auth-Token header.
        """
        import hashlib
        creds_hash = hashlib.md5(
            f"{self.username}:{self.password}".encode()
        ).hexdigest()

        resp = self._session.put(
            f"{self.base_url}/user_auth",
            json={
                "data": {
                    "credentials": creds_hash,
                    "account_name": self.account_name,
                }
            },
        )
        if resp.status_code != 201:
            raise KazooAuthError(f"Authentication failed: {resp.status_code} {resp.text}")

        body = resp.json()["data"]
        self.auth_token = body["auth_token"]
        self.account_id = body["account_id"]
        self._session.headers.update({"X-Auth-Token": self.auth_token})
        return self.auth_token

    def _require_auth(self):
        if not self.auth_token:
            self.authenticate()

    # --- Accounts -----------------------------------------------------

    def get_account(self, account_id: str = None):
        self._require_auth()
        account_id = account_id or self.account_id
        resp = self._session.get(f"{self.base_url}/accounts/{account_id}")
        resp.raise_for_status()
        return resp.json()["data"]

    # --- Devices --------------------------------------------------------

    def list_devices(self):
        self._require_auth()
        resp = self._session.get(f"{self.base_url}/accounts/{self.account_id}/devices")
        resp.raise_for_status()
        return resp.json()["data"]

    def create_device(self, device_name: str, sip_username: str, sip_password: str,
                       device_type: str = "sip_device"):
        """
        Provisions a new SIP device/extension under the account - the
        Crossbar equivalent of adding a `<user>` directory entry directly
        in a raw FreeSWITCH/Kamailio deployment.
        """
        self._require_auth()
        payload = {
            "data": {
                "name": device_name,
                "device_type": device_type,
                "sip": {
                    "username": sip_username,
                    "password": sip_password,
                    "method": "password",
                },
                "enabled": True,
            }
        }
        resp = self._session.put(
            f"{self.base_url}/accounts/{self.account_id}/devices", json=payload
        )
        resp.raise_for_status()
        return resp.json()["data"]

    # --- Call origination ------------------------------------------------

    def originate_call(self, device_id: str, to_number: str):
        """
        Triggers a click-to-call from a provisioned device to an external
        number - the Crossbar-layer equivalent of the raw ESL `originate`
        used in the freeswitch-cloud-pbx repo's api/originate.py, but
        routed through KAZOO's call control instead of talking to
        FreeSWITCH directly.
        """
        self._require_auth()
        payload = {
            "data": {
                "action": "originate",
                "device_id": device_id,
                "endpoints": [{"endpoint_type": "device", "endpoint_id": device_id}],
                "to": to_number,
            }
        }
        resp = self._session.put(
            f"{self.base_url}/accounts/{self.account_id}/quickcall", json=payload
        )
        resp.raise_for_status()
        return resp.json()["data"]

    # --- CDRs -------------------------------------------------------------

    def get_cdrs(self, created_from: int = None, created_to: int = None):
        """created_from/created_to are gregorian (epoch+62167219200) timestamps per Crossbar convention."""
        self._require_auth()
        params = {}
        if created_from:
            params["created_from"] = created_from
        if created_to:
            params["created_to"] = created_to
        resp = self._session.get(
            f"{self.base_url}/accounts/{self.account_id}/cdrs", params=params
        )
        resp.raise_for_status()
        return resp.json()["data"]
