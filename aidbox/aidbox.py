import requests
import json
from typing import Any
import pandas as pd

class Aidbox:
    def __init__(self, base_url: str, client: str, secret: str):
        self.base_url = base_url
        self.client = client
        self.secret = secret

    def url(self, path: str):
        return f"{self.base_url}/{path}"

    def check(self):
        url = self.url('$version')
        response = requests.get(url, auth=(self.client, self.secret))
        return response.json()

    def post_request(self, url: str, data: Any):
        full_url = self.url(url)
        response = requests.post(
            full_url,
            auth=(self.client, self.secret),
            json=data
        )
        return response.json()

    def _prepare_rpc_payload(self, method: str, params: Any):
        if not params:
            return {"method": method}
        return {
            "method": method,
            "params": params
        }

    def rpc(self, method: str, params=Any):
        response = self.post_request(
            '/rpc',
            self._prepare_rpc_payload(method, params)
        )
        if self._rpc_has_error(response):
            raise ValueError(response)
        return response
    
    def _rpc_has_error(self, response):
        if 'resourceType' in response and response['resourceType'] == 'OperationOutcome':
            return True
        if 'error' in response:
            return True

    def sql(self, query):
        response = self.post_request(
            '/$notebook-psql',
            {
                "query": query
            }
        )
        if self._rpc_has_error(response): # Note: same format as RPC for historical resons
            raise ValueError(response)
        return response['result'][0]['data'] # FIXME: this endpoint supports many result sets and queries which do not return results
