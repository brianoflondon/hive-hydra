from flask import Flask, request
from beem import Hive
import os

app = Flask(__name__)


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

    except Exception as ex:
        print(f'{ex.__class__} occurred')
        trx_id = 'failure'

    return trx_id


@app.route("/")
def home():
    return "Hydra is Here!"


@app.route("/hydra_ping/")
def hydra_ping():
    trx_id = send_notification(request.json)
    if trx_id == 'failure':
        return({'message':'pinged'})
    else:
        trx_url = f'https://hive.ausbit.dev/tx/{trx_id}'
        return(
            {'message':'success',
             'trx_id': trx_id,
             'trx_url': trx_url
             })