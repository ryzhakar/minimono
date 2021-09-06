from time import time
from math import floor
from os import environ
from dotenv import load_dotenv
from monobank.api_call import monocall
load_dotenv()
mono_token = environ.get('mono_token')

curr_code = {
	980: 'UAH',
	840: 'USD',
	978: 'EUR',
	985: 'PLN'
}

# In descending order of main-account probability.
card_type = ['iron', 'platinum', 'black',
			'white', 'fop', 'yellow']

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
		for tp in card_type[:3]:
			if tp in self.accounts.keys():
				self.accounts['default'] = self.accounts[tp]['UAH']
				break		
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
	
class Statement:
	def __init__(self, client_obj, account='default', fromdate=floor(time()) - 2682000, todate=floor(time())):
		self.id = client_obj.accounts[account]
		self.token = client_obj.token
		self.unfo = client_obj.__str__()
		self.fromdate = fromdate
		self.todate = todate
		self.raw = self.get_statement()

	def __str__(self):
		expenses = abs(sum([n["operationAmount"] for n in self.raw if n["operationAmount"] < 0]))/100
		return f'{self.unfo} spent {expenses} UAH in this timeframe.'
	
	def get_statement(self):
		response = monocall(self.token, f'statement/{self.id}/{self.fromdate}/{self.todate}')
		print('getting statement -', response.raise_for_status())
		return response.json()