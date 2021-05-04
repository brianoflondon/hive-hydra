from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain
from datetime import datetime, time, timedelta, tzinfo, timezone
from time import sleep
import json
import logging

import telegram
import os

# Testnet instead of main Hive
USE_TEST_NODE = True
TEST_NODE = ['http://testnet.openhive.network:8091']

t_key = os.getenv('TELEGRAM_BOT_KEY')

logging.basicConfig(level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
if USE_TEST_NODE:
    logging.info('---------------> Using Test Node ' + TEST_NODE[0])
else:
    logging.info('---------------> Using Main Hive Chain ')

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

    if USE_TEST_NODE:
        h = Hive(node=TEST_NODE)
    else:
        h = Hive()

    blockchain = Blockchain(mode="head")
    logging.info('Watching live...')

    stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=False, thread_num=4)

    start_time = datetime.utcnow()
    count_posts = 0

    for post in stream:
        count_posts +=1
        time_dif = post['timestamp'].replace(tzinfo=None) - start_time
        if time_dif > timedelta(minutes=1):
            logging.info(str(post['timestamp']) + " Count: " + str(count_posts))
            start_time =post['timestamp'].replace(tzinfo=None)
            count_posts = 0

        if post['id'] == 'hive-hydra':
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)



def scan_history(timed):
    allowed_accounts = get_allowed_accounts('podcastindex')

    if USE_TEST_NODE:
        h = Hive(node=TEST_NODE)
    else:
        h = Hive()

    blockchain = Blockchain(mode="head")
    start_time = datetime.utcnow() - timed
    count_posts = 0
    block_num = blockchain.get_estimated_block_num(start_time)

    logging.info('Started catching up')
    stream = blockchain.stream(opNames=['custom_json'], start = block_num,
                               max_batch_size = 50,
                               raw_ops=False, threading=False)
    for post in stream:
        post_time = post['timestamp'].replace(tzinfo=None)
        time_dif = post_time - start_time
        time_to_now = datetime.utcnow() - post_time
        count_posts += 1
        if time_dif > timedelta(minutes=5):
            logging.info(str(post['timestamp']) + " Count: " + str(count_posts) + " Time Delta: " + str(time_to_now))
            start_time =post['timestamp'].replace(tzinfo=None)
            count_posts = 0
            if time_to_now < timedelta(minutes=5):
                # Break out of the for loop we've caught up.
                break

        if post['id'] == 'hive-hydra':
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)
    logging.info('Finished catching up')


if __name__ == "__main__":
    timed = timedelta(minutes=10)
    # timed = timedelta(days= 2)
    scan_history(timed)
    main()