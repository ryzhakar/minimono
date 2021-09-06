from time import time
from math import floor
from os import environ
from dotenv import load_dotenv
from monobank.api_call import monocall
from monobank.exceptions import EmptyStatement, WrongObject
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

class Base:
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
	def __init__(self, base_obj, account='default', fromdate=floor(time()) - 2682000, todate=floor(time())):
		if todate-fromdate > 2682000 or todate-fromdate <= 0:
			raise ValueError("Time period between 'todate' and 'fromdate' should be in 1-2682000 secods range.")
		if not ('accounts' in base_obj.__dict__.keys() and 'token' in base_obj.__dict__.keys()):
			raise WrongObject("Instance of the Base class is expected: recieved wrong object.")
		self.id = base_obj.accounts[account]
		self.token = base_obj.token
		self.unfo = base_obj.__str__()
		self.timeframe = (fromdate, todate)
		try:
			self.raw = self.get_statement(fromdate=fromdate, todate=todate)
		except EmptyStatement:
			self.raw = [{'operationAmount': 0}]

	def __str__(self):
		expenses = abs(sum([n["operationAmount"] for n in self.raw if n["operationAmount"] <= 0]))/100
		return f'{self.unfo} spent {expenses} UAH in this timeframe.'
	
	def get_statement(self, fromdate=floor(time()) - 2682000, todate=floor(time())):
		response = monocall(self.token, f'statement/{self.id}/{fromdate}/{todate}')
		print('getting statement -', response.raise_for_status())

		if not bool(response.json()):
			raise EmptyStatement("No transactions in this timeframe.")
		return response.json()