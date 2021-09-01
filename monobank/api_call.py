import requests
import time
calls = [0,]

def monocall(token, urltail):
    url = f'https://api.monobank.ua/personal/{urltail}'
    headers = {'X-Token': token}
    
    td = time.time() - calls[-1]
    if td < 60:
        print('Waiting before the next API call to avoid rate-limiting...')
        time.sleep(60-td)
    response = requests.request("GET", url, headers=headers)
    calls.append(time.time())
    return response