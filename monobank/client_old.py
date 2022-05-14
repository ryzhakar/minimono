import json

from time import time
from math import floor
from os import environ
from dotenv import load_dotenv

from API.api_call import monocall
from API.exceptions import EmptyStatement, WrongObject

load_dotenv()
mono_token = environ.get('mono_token')
curr_code = {
	980: 'UAH',
	840: 'USD',
	978: 'EUR',
	985: 'PLN'
}
jan01_2018 = 1514757600
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
			# Faux statement for dict to contain the expected key.
			faux_stat = [{
				"id": "ZuHWzqkKGVo=",
				"time": 1554466347,
				"description": "Покупка щастя",
				"mcc": 7997,
				"hold": False,
				"amount": -95000,
				"operationAmount": -95000,
				"currencyCode": 980,
				"commissionRate": 0,
				"cashbackAmount": 19000,
				"balance": 10050000,
				"comment": "За каву",
				"receiptId": "XXXX-XXXX-XXXX-XXXX",
				"counterEdrpou": "3096889974",
				"counterIban": "UA898999980000355639201001404"
				}]
			self.raw = faux_stat
			
		self.processed = self.process_statement('mcc', structure='description:time, amount')

	def __str__(self):
		expenses = abs(sum([n["operationAmount"] for n in self.raw if n["operationAmount"] <= 0]))/100
		return f'{self.unfo} spent {expenses} UAH in this timeframe.'
	
	def get_statement(self, fromdate=floor(time()) - 2682000, todate=floor(time()), inject_mcc_desc=True, mcc_lang='en', mcc_filename='monobank/mcc_groups_localized.json'):
		response = monocall(self.token, f'statement/{self.id}/{fromdate}/{todate}')
		print('getting statement -', response.raise_for_status())
		# Check for response content.
		if not bool(response.json()):
			raise EmptyStatement("No transactions in this timeframe.")
		else:
			stat = response.json()
		# Inject names of business types instead of MCC codes.
		# Also, add broader MCC group names.
		if inject_mcc_desc:
			with open(mcc_filename, 'r') as mcc_codes:
				# Build a dict of mcc codes in the following format:
				# {mcc(int): (mcc_description (str), mcc_group (str))}.
				# Uses specified language.
				mcc_codes = dict([(int(n['mcc']), (n['shortDescription'][mcc_lang], n['group']['description'][mcc_lang])) for n in json.load(mcc_codes)])
			for tran in stat:
				tran['mcc_group'] = mcc_codes[int(tran['mcc'])][1]
				tran['mcc'] = mcc_codes[int(tran['mcc'])][0]
		return stat

	def process_statement(self, grouping_by, structure=False):
		items = []
		keys = list(set([n[grouping_by] for n in self.raw]))

		if structure:
			structure = structure.replace(' ', '').split(':')
			structure[1] = structure[1].split(',')

		for k in keys:
			new_dict = list(filter(lambda x: x[grouping_by] == k, self.raw))
			if any(new_dict):
				if structure:
					new_dict = dict(sorted([(minidict[structure[0]], ([minidict[n] for n in structure[1]])) for minidict in self.raw], key=lambda x: x[0]))
				items.append((k, new_dict))
		return items