import pandas as pd
from aidbox.aidbox import Aidbox

def list_models(aidbox: Aidbox):
    response = aidbox.rpc("aidbox.mdm/list-models", {})
    return pd.DataFrame({"model_symbol": response['result']})

def get_model(aidbox: Aidbox, model_symbol: str):
    response = aidbox.rpc('aidbox.mdm/get-model', {'model': model_symbol})
    return response

class Model:
    def __init__(self, resource_type: str, fields = None, frequencies_for = None):
        self.rt = resource_type
        self.fields = {} if fields is None else fields
        self.frequencies_for = set() if frequencies_for is None else frequencies_for
    def __setitem__(self, key: str, value):
        self.fields[key] = value
    def __delitem__(self, key: str):
        del self.fields[key]
    def __getitem__(self, key: str):
        return self.fields[key]
    def enable_frequencies(self, field_name: str):
        self.frequencies_for = self.frequencies_for | {field_name}
    def disable_frequencies(self, field_name: str):
        self.frequencies_for = self.frequencies_for - {field_name}
    def as_dict(self):
        return {
            'fields': self.fields,
            'use-frequencies-for': list(self.frequencies_for),
            'resource-type': self.rt
        }
    def apply(self, aidbox: Aidbox):
        response = aidbox.rpc(
            'aidbox.mdm/execute-etl',
            {
                'model': self.as_dict()
            }
        )
        return response
    def table_name(self):
        return self.rt.lower() + '_mdm_data'