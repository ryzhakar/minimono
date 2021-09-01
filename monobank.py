import requests, json, os
from dotenv import load_dotenv
from time import time
from math import floor

load_dotenv()
try:
    mono_token = os.environ.get('mono_token')
except KeyError:
    pass

def_currency = 980
def_type = 'black'
jan01_2018 = 1514757600


class MonoCardStat:
    def __init__(self, token, cdcurrency=def_currency, cdtype=def_type, fromdate=(floor(time()) - 2682000), todate=floor(time())):
        if todate - fromdate > 2682000:
            raise ValueError("Can't fetch statement for time period longer than a month.")
        self.timestep = 2682000
        self.fromdate = fromdate
        self.todate = todate

        self.token = token
        self.currency = ('currencyCode', cdcurrency)
        self.type = ('type', 'black')
        self.account = [n for n in self.personal_info()['accounts'] if n[self.type[0]] == self.type[1] and n[self.currency[0]] == self.currency[1]][0]['id']
        self.raw_stat = self.get_statement()
        self.stat = {}
    
    def personal_info(self):
        url = 'https://api.monobank.ua/personal/client-info'
        headers = {
            'X-Token': self.token
        }
        response = requests.request("GET", url, headers=headers)
        print('personal info -', response.status_code)

        return response.json()

    def get_statement(self):
        url = f'https://api.monobank.ua/personal/statement/{self.account}/{self.fromdate}/{self.todate}'
        headers = {
            'X-Token': self.token
        }
        response = requests.request("GET", url, headers=headers)
        print('getting statement -', response.raise_for_status())

        return response.json()

    def inject_mcc_names(self, lang='en', filename='mcc_local_groups.json'):
            with open(filename, 'r') as mcc_codes:
                mcc_codes = dict([(int(n['mcc']), [n['shortDescription'][lang], n['group']['description'][lang]]) for n in json.load(mcc_codes)])
            for tran in self.raw_stat:
                tran['mcc_group'] = mcc_codes[int(tran['mcc'])][1]
                tran['mcc'] = mcc_codes[int(tran['mcc'])][0]

    def regroup(self, grouping_by, structure=False):
        '''
        
        '''
        items = []
        keys = list(set([n[grouping_by] for n in self.raw_stat]))

        if structure:
            structure = structure.replace(' ', '').split(':')
            structure[1] = structure[1].split(',')
        
        for k in keys:
            new_dict = list(filter(lambda x: x[grouping_by] == k, self.raw_stat))
            if any(new_dict):
                if structure:
                    new_dict = dict(sorted([(minidict[structure[0]], ([minidict[n] for n in structure[1]])) for minidict in self.raw_stat], key=lambda x: x[0]))
                items.append((k, new_dict))
        self.stat = items