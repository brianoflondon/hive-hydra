from beem import Hive
from beem.blockchain import Blockchain
import json



def main():
    """ watches the stream from the Hive blockchain """

    blockchain = Blockchain()
    stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=True, thread_num=4)

    for post in stream:
        if 'podcastindex' in post['required_posting_auths']:
            print(post)
            data = json.loads(post.get('json'))
            print(data.get('id'))
            print('--------------------------------')


if __name__ == "__main__":
    main()