from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain
from datetime import datetime, time, timedelta, tzinfo, timezone
from time import sleep
import json
import logging

import telegram
import os
t_key = os.getenv('TELEGRAM_BOT_KEY')

logging.basicConfig(level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


def get_allowed_accounts(acc_name) -> bool:
    """ get a list of all accounts allowed to post by acc_name (podcastindex)
        and only react to these accounts """

    hiveaccount = Account(acc_name, lazy=True)
    try:
        allowed = hiveaccount['posting']['account_auths']
        allowed = [x for (x,_) in allowed]

    except Exception as ex:
        allowed = []

    return allowed


def output(post) -> None:
    """ Prints out the post and extracts the custom_json """
    bot = telegram.Bot(token=t_key)
    data = json.loads(post.get('json'))
    print(json.dumps(post, indent=2, default=str))
    print('--------------------------------')
    print(json.dumps(data,indent=2,default=str))
    print('****************************************')
    title = data.get('title')
    url = data.get('url')
    if not title:
        title = "No Title"
        url = "No URL"
        t_message = json.dumps(data,indent=2,default=str)
    else:
        t_message = f"{title} updated ({url})"


    bot.send_message(chat_id="-1001375564114",text=t_message)


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
            logging.info(post['timestamp'])
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
        if time_dif > timedelta(minutes=15):
            logging.info(post['timestamp'])
            start_time =post['timestamp'].replace(tzinfo=None)
        if post['id'] == 'hive-hydra':
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)



if __name__ == "__main__":
    timed = timedelta(minutes=60)
    # timed = timedelta(days= 2)
    scan_history(timed)
    main()