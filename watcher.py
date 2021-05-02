from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain
from datetime import datetime, time, timedelta, tzinfo, timezone
from time import sleep
import json


def get_allowed_accounts(acc_name):
    """ get a list of all accounts allowed to post by acc_name (podcastindex)
        and only react to these accounts """

    hiveaccount = Account(acc_name, lazy=True)
    try:
        allowed = hiveaccount['posting']['account_auths']
        allowed = [x for (x,_) in allowed]

    except Exception as ex:
        allowed = []

    return allowed


def output(post):
    """ Prints out the post and extracts the custom_json """
    data = json.loads(post.get('json'))
    print(json.dumps(post, indent=2, default=str))
    print('--------------------------------')
    print(json.dumps(data,indent=2,default=str))
    print('****************************************')


def main():
    """ watches the stream from the Hive blockchain """
    allowed_accounts = get_allowed_accounts('podcastindex')

    h = Hive(node='https://api.deathwing.me')
    blockchain = Blockchain(mode="head")
    print('Watching...')
    start_time = datetime.utcnow()

    stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=True, thread_num=4)

    for post in stream:
        time_dif = post['timestamp'].replace(tzinfo=None) - start_time
        if time_dif > timedelta(minutes=1):
            print(post['timestamp'])
            start_time =post['timestamp'].replace(tzinfo=None)

        if post['id'] == 'hive-hydra':
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)



def scan_history(timed):
    allowed_accounts = get_allowed_accounts('podcastindex')
    h = Hive()
    blockchain = Blockchain(mode="head")
    start_time = datetime.utcnow() - timed
    block_num = blockchain.get_estimated_block_num(start_time)

    stream = blockchain.stream(opNames=['custom_json'], start = block_num,
                               max_batch_size = 50,
                               raw_ops=False, threading=False)
    for post in stream:
        time_dif = post['timestamp'].replace(tzinfo=None) - start_time
        if time_dif > timedelta(minutes=1):
            print(post['timestamp'])
            start_time =post['timestamp'].replace(tzinfo=None)
        if post['id'] == 'hive-hydra':
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)



if __name__ == "__main__":
    timed = timedelta(minutes= 240)
    scan_history(timed)
    main()