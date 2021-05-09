import json
import logging
import os
import queue
import threading
from datetime import datetime, timedelta
from time import sleep

import telegram
from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain

# Testnet instead of main Hive

USE_TEST_NODE = os.getenv("USE_TEST_NODE", 'False').lower() in ('true', '1', 't')
TELEGRAM_ALERTS = os.getenv("TELEGRAM_ALERTS", 'False').lower() in ('true', '1', 't')
WATCHED_OPERATION_IDS = ['podping','hive-hydra']
TEST_NODE = ['http://testnet.openhive.network:8091']
TELEGRAM_CHAT_ID = "-1001454810391"     # Hive Hydra Podcasting 2.0 Channel on Telegram


logging.basicConfig(level=logging.INFO,
                    format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')


if USE_TEST_NODE:
    t_key = os.getenv('TELEGRAM_BOT_KEY_TEST')
    logging.info('---------------> Using Test Node ' + TEST_NODE[0])
    hive = Hive(node=TEST_NODE)

else:
    t_key = os.getenv('TELEGRAM_BOT_KEY')
    logging.info('---------------> Using Main Hive Chain ')
    hive = Hive()

if TELEGRAM_ALERTS:
    telegram_q = queue.Queue()
    telegram_alive_q = queue.Queue()



def get_allowed_accounts(acc_name='podping') -> bool:
    """ get a list of all accounts allowed to post by acc_name (podping)
        and only react to these accounts """

    # Switching to a simpler authentication system. Only podpings from accounts which
    # the PODPING Hive account FOLLOWS will be watched.
    master_account = Account(acc_name, blockchain_instance=hive, lazy=True)
    allowed = master_account.get_following()
    return allowed

    # Depreciated OLD method which was silly. Will remove later
    if USE_TEST_NODE:
        return ['learn-to-code','hive-hydra','hivehydra','flyingboy','blocktvnews']

    hiveaccount = Account(acc_name, blockchain_instance=hive, lazy=True)
    try:
        allowed = hiveaccount['posting']['account_auths']
        allowed = [x for (x,_) in allowed]

    except Exception as ex:
        allowed = []

    return allowed

def allowed_op_id(operation_id):
    """ Checks if the operation_id is in the allowed list """
    if operation_id in WATCHED_OPERATION_IDS:
        return True
    else:
        return False

def output(post) -> None:
    """ Prints out the post and extracts the custom_json """
    data = json.loads(post.get('json'))
    data['required_posting_auths'] = post.get('required_posting_auths')
    data['trx_id'] = post.get('trx_id')
    data['timestamp'] = post.get('timestamp')
    if USE_TEST_NODE:
        data['test_node'] = True
    logging.info('Found alert: ' + data.get('url'))
    if TELEGRAM_ALERTS:
        telegram_q.put( (telegram_post, data) )

def output_status(timestamp, pings, count_posts, time_to_now='', current_block_num='') -> None:
    """ Writes out a status update at with some count data """
    if time_to_now:
        logging.info(f'{timestamp} PodPings: {pings} - Count: {count_posts} - Time Delta: {time_to_now}')

    else:
        logging.info(f'{timestamp} PodPings: {pings} - Count: {count_posts} - Current BlockNum: {current_block_num}')




def telegram_post(data) -> None:
    """ Outputs to Telegram """
    if TELEGRAM_ALERTS:
        logging.info('Sending to telegram')
        bot = telegram.Bot(token=t_key)
        lines = []
        for key, value in data.items():
            if type(value) is list:
                value = ' '.join(value)
            text = f'<b>{key}</b> : {value}\n'
            lines.append(text)
        text = ''.join(lines)

        bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                    text=text,
                    parse_mode=telegram.ParseMode.HTML)
        sleep(10)



def telegram_alive() -> None:
    """ Sends a message to telegram every 15 minutes """
    text = __file__ + ' running at ' + str(datetime.now()) + ' Test: ' + str(USE_TEST_NODE)
    bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_KEY'))
    bot.send_message(chat_id='-1001389993620',
                        text=text,
                        parse_mode=telegram.ParseMode.HTML)
    logging.info("I'm alive notification sent")
    sleep(15*60)
    telegram_alive_q.put( (telegram_alive, ) )

def telegram_alive_worker():
    """ Infinite run the Telegram alive code """
    telegram_alive_q.put( (telegram_alive, ) )
    while True:
        items = telegram_alive_q.get()
        func = items[0]
        func()


def telegram_worker():
    while True:
        logging.info(f'Telegram send Q operating. Q size : '+ str(telegram_q.qsize()))
        items = telegram_q.get()
        func = items[0]
        args = items[1:]
        func(*args)
        telegram_q.task_done()
        logging.info(f'Finished sending to telegram. Q size : '+ str(telegram_q.qsize()))


def scan_live(report_freq = None):
    """ watches the stream from the Hive blockchain """

    if not report_freq:
        report_freq = timedelta(minutes=1)

    if type(report_freq) == int:
        report_freq = timedelta(minutes=report_freq)
    allowed_accounts = get_allowed_accounts()

    blockchain = Blockchain(mode="head", blockchain_instance=hive)
    current_block_num = blockchain.get_current_block_num()
    logging.info('Watching live from block_num: ' + str(current_block_num))

    # If you want instant confirmation, you need to instantiate
    # class:beem.blockchain.Blockchain with mode="head",
    # otherwise, the call will wait until confirmed in an irreversible block.
    stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=False, thread_num=4)

    start_time = datetime.utcnow()
    count_posts = 0
    pings = 0

    for post in stream:
        count_posts +=1
        time_dif = post['timestamp'].replace(tzinfo=None) - start_time
        if time_dif > report_freq:
            current_block_num = blockchain.get_current_block_num()
            timestamp = str(post['timestamp'])
            output_status(timestamp, pings, count_posts, current_block_num=current_block_num)
            start_time =post['timestamp'].replace(tzinfo=None)
            count_posts = 0
            pings = 0

        if allowed_op_id(post['id']):
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)
                pings += 1

        if time_dif > timedelta(hours=1):
            # Refetch the allowed_accounts every hour in case we add one.
            allowed_accounts = get_allowed_accounts()

def scan_history(timed= None, report_freq = None):
    """ Scans back in history timed time delta ago, reporting with report_freq
        if timed is an int, treat it as hours, if report_freq is int, treat as min """
    scan_start_time = datetime.utcnow()

    if not report_freq:
        report_freq = timedelta(minutes=5)

    if not timed:
        timed = timedelta(hours=1)

    if type(timed) == int:
        timed = timedelta(hours=timed)

    if type(report_freq) == int:
        report_freq = timedelta(minutes=report_freq)

    allowed_accounts = get_allowed_accounts()

    blockchain = Blockchain(mode="head", blockchain_instance=hive)
    start_time = datetime.utcnow() - timed
    count_posts = 0
    pings = 0
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
        if time_dif > report_freq:
            timestamp = str(post['timestamp'])
            output_status(timestamp, pings, count_posts, time_to_now)
            start_time =post['timestamp'].replace(tzinfo=None)
            count_posts = 0
            pings = 0

        if allowed_op_id(post['id']):
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                output(post)

        if time_to_now < timedelta(seconds=2):
            logging.info('block_num: ' + str(post['block_num']))
            # Break out of the for loop we've caught up.
            break

    scan_time = datetime.utcnow() - scan_start_time
    logging.info('Finished catching up at block_num: ' + str(post['block_num']) + ' in '+ str(scan_time))

if TELEGRAM_ALERTS:
    threading.Thread(target=telegram_worker, daemon=True).start()
    threading.Thread(target=telegram_alive_worker, daemon=True).start()

def main() -> None:
    """ Main file """
    scan_history(1, 15)
    scan_live(2)



if __name__ == "__main__":
    main()
