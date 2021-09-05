from api_call import monocall
from time import time
from math import floor
#from dotenv import load_dotenv
#load_dotenv()
mono_token = environ.get('mono_oken')

curr_code = {
	980: 'UAH',
	940: 'USD',
	978: 'EUR',
	985: 'PLN'
}

card_type = ['black', 'white', 'platinum',
			'iron', 'fop', 'yellow']

class Client:
	def __init__(self, token):
		# Token and raw API personal response.
		self.token = token
		self.raw_info = self.personal_info()
		# Account structure
		self.accounts = {}
		accounts = self.raw_info['accounts']
		tps = list(set([n['type'] for n in accounts]))
		for ctp in tps:
			self.accounts[ctp] = dict([(curr_code[n['currencyCode']], n['id']) for n in accounts if n['type'] == ctp])
		# Webhook
		if 'webHookUrl' in self.raw_info.keys():
			self.webhook = self.raw_info['webHookUrl']
		else:
			self.webhook = None

	def __str__(self):
		return self.raw_info['name']

	def personal_info(self):
        response = monocall(self.token, 'client-info')
        print('personal info -', response.raise_for_status())


        return response.json()