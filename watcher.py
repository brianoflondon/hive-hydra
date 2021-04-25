from beem import Hive
from beem.account import Account
from beem.blockchain import Blockchain
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




def main():
    """ watches the stream from the Hive blockchain """
    allowed_accounts = get_allowed_accounts('podcastindex')


    h = Hive(node='https://api.deathwing.me')
    blockchain = Blockchain()
    print('Watching...')

    stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=True, thread_num=4)

    for post in stream:
        if post['id'] == 'hive-hydra':
            if  (set(post['required_posting_auths']) & set(allowed_accounts)):
                data = json.loads(post.get('json'))
                print(json.dumps(post, indent=2, default=str))
                print('--------------------------------')
                print(json.dumps(data,indent=2,default=str))
                print('****************************************')



if __name__ == "__main__":
    main()