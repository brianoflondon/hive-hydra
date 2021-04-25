from beem import Hive
from beem.blockchain import Blockchain
import json



def main():
    """ watches the stream from the Hive blockchain """
    h = Hive(rpcuser='podcastindex',node='https://api.deathwing.me')
    blockchain = Blockchain()
    print('Watching...')

    stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=True, thread_num=4)

    for post in stream:
        if 'podcastindex' in post['required_posting_auths'] and post['id'] == 'hive-hydra':
            data = json.loads(post.get('json'))
            print(json.dumps(post, indent=2, default=str))
            print('--------------------------------')
            print(json.dumps(data,indent=2,default=str))
            print('****************************************')



if __name__ == "__main__":
    main()