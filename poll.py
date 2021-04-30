
import requests
import json
import hashlib
import os
from datetime import datetime
import xmltodict

from beem import Hive


all_checks = {}

def get_feed_hash(url):
    """ Returns hash of a feed and timestamp """
    fetched = requests.get(url)
    m= hashlib.sha256()
    m.update(fetched.text.encode())
    text_hash = m.hexdigest()
    ts = int(datetime.utcnow().timestamp())
    return text_hash, ts

def update_all_checks(feed, text_hash, ts):
    """ Takes in a feed and a hash, timestamp and updates disk file """
    global all_checks
    url = feed['url']
    all_checks[url] = {
        "title": feed['title'],
        "hash" : text_hash,
        "timestamp" : ts
    }
    with open('all_hash.json', 'w') as f:
        json.dump(all_checks, f, indent=2)


def get_feeds():
    """ Read in a json with a list of feeds and start polling them """

    global all_checks
    # This is the account name of polling agent 'learn-to-code'
    server_account = os.getenv('HIVE_SERVER_ACCOUNT')

    with open('all_value_feeds.json', 'r') as f:
        ans = json.load(f)

    with open('all_hash.json', 'r') as f:
        all_checks = json.load(f)

    for feed in ans['feeds']:
        url = feed['url']
        text_hash, ts = get_feed_hash(url)

        if all_checks.get(url):
            if text_hash != all_checks[url].get('hash'):
                custom_json = {
                    "id" : feed['id'],
                    "url": url,
                    "timestamp": ts,
                    "hash":text_hash,
                    "pollAgent": server_account
                }
                trx_id = send_notification(custom_json)
                if trx_id != 'failure':
                    update_all_checks(feed,text_hash,ts)

        else:
            # New feed
            update_all_checks(feed,text_hash,ts)


        print(f'fetched {url} - {ts}')


def send_notification(custom_json):
    """ Sends a custom_json to Hive """
    id = 'hive-hydra'

    try:
        # This is the posting key for 'learn-to-code'
        server_account = os.getenv('HIVE_SERVER_ACCOUNT')
        wif = [os.getenv('HIVE_POSTING_KEY')]
        h = Hive(keys=wif)

        tx = h.custom_json(id=id, json_data= custom_json,
                            required_posting_auths=[server_account])
        trx_id = tx['trx_id']
        print(f'Json saved in https://hive.ausbit.dev/tx/{trx_id}')

    except Exception as ex:
        print(f'{ex.__class__} occurred')

        trx_id = "failure"

    return trx_id




def main():
    get_feeds()

if __name__ == "__main__":
    main()