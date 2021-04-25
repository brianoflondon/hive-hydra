# hive-hydra
A first try at building a Podcast update signaling system built on the Hive Blockchain


This is in two parts:

watcher.py and poll.py.


## watcher.py is a passive listener

Watcher.py reads the Hive blockchain as it updates every 3 seconds. This is like watching the twitter firehose back when that was allowed. It is permissionless, you don't need an account to do this. This will miss blocks if it goes off line but it is trivial to write a listener that can "catch up" if it has missed blocks.

It tests every block in two ways looking for a transaction recorded on the Hive blockchain which looks like this:

```
{
  "type": "custom_json",
  "required_auths": [],
  "required_posting_auths": [
    "learn-to-code",
    "podcastindex"
  ],
  "id": "hive-hydra",
  "json": "{\"id\":508054,\"url\":\"https://feeds.fireside.fm/fiddlydicking/rss\",\"timestamp\":1619341855,\"hash\":\"970b7e7c8ed76f0f6060c43426aad553235362998efe09efcea57c86bc81527d\",\"pollAgent\":\"learn-to-code\"}",
  "_id": "78a43918db06c8e612cbb7ee2def775781f18a08",
  "timestamp": "2021-04-25 09:10:57+00:00",
  "block_num": 53331807,
  "trx_num": 82,
  "trx_id": "a4769cffb6abf9fb05b210dc72808c8c92fd5b52"
}
```
If the ```id``` matches ```"hive-hdra"``` it further checks if the account which sent this update is in a list of accounts authorised to give updates. That list is under the control of the account ```podcastindex```.

If that is the case this transaction can be used (it's just printed in this basic version). The transaction contains a JSON payload which can hold any information we like but which we should keep to the minimum necessary.

```
{
  "id": 508054,
  "url": "https://feeds.fireside.fm/fiddlydicking/rss",
  "timestamp": 1619341855,
  "hash": "970b7e7c8ed76f0f6060c43426aad553235362998efe09efcea57c86bc81527d",
  "pollAgent": "learn-to-code"
}
```


## poll.py

This is just a rought polling script (which is very poor at its job). It hashes RSS feeds and compares the hash to one it recorded earlier. If the feed has changed it posts from the account ```learn-to-code``` the transaction which ```watcher.py``` above sees.

The important part of the code is this:

```
def send_notification(custom_json):
    """ Sends a custom_json to Hive """
    id = 'hive-hydra'

    try:
        # This is the posting key for 'learn-to-code' but we will post on
        # behalf of 'podcastindex': this permission can be revoked.
        server_account = os.getenv('HIVE_SERVER_ACCOUNT')
        wif = os.getenv('HIVE_POSTING_KEY')
        h = Hive(keys=wif, node='https://api.deathwing.me', rpcuser=server_account)
        tx = h.custom_json(id=id, json_data= custom_json,
                           required_posting_auths=[server_account])
        trx_id = tx['trx_id']
        print(f'Json saved in https://hive.ausbit.dev/tx/{trx_id}')

    except Exception as ex:
        print(f'{ex.__class__} occurred')
        trx_id = "failure"

    return trx_id
```

The field ```wif``` which the code gets from an ENV variable is the ```posting authority key``` for the ```learn-to-code``` account on Hive. This is a low authority key: it doesn't allow movement of valuable tokens and only allows posting to the blockchain.

Any entity wishing to notify the PodcastIndex of a change to a feed woudl need their own Hive account to replace ```learn-to-code```.

The account ```learn-to-code``` uses up renewable ```resource credits``` but there is no direct cost for each post. The infrastructure costs of running the entire Hive system cover all the many servers which process Hive transactions and social posts. An account with even $50 of staked value would probably be sufficient for many 100's of notifications per day. Staked value can be "loaned" or delegated in the paralance of Hive.

Block times are 3s so notifications should be visible to any watching party within something like 6 to 10 seconds in practice.
