from beem import Hive
from beem.blockchain import Blockchain
import json


blockchain = Blockchain()
stream = blockchain.stream(opNames=['custom_json'], raw_ops=False, threading=True, thread_num=4)

for post in stream:
    print(post)
    data = json.loads(post.get('json'))

    print(data.get('app'))
