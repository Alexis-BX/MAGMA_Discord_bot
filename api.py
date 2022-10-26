import requests
import base64
import json
from time import sleep
import os

def res_format(response):
    return response.status_code, json.loads(response.text)

def post_single(image_path, caption, output=15, temp=0.7, k=0, rearrange=False):
    url='https://hf.space/embed/EleutherAI/magma/api/queue/push/'

    if image_path[:4] == 'http':
        image_file = requests.get(image_path).content
    else:
        image_file = open(image_path, "rb").read()

    image_string = base64.b64encode(image_file)
    dtype = 'png' if image_path[-4:]=='png' else 'jpeg'

    data = {
        "data": [
            'data:image/'+dtype+';base64,'+str(image_string)[2:-1],
            caption, 
            output, 
            temp, 
            k, 
            rearrange
        ],
        "session_hash": "5sw1s5va5ta",
        "action": "predict"
    }

    response = requests.post(url, json=data)
    return res_format(response)

def get_status(hash):
    url='https://hf.space/embed/EleutherAI/magma/api/queue/status/'
    data = {
        "hash": hash
    }

    response = requests.post(url, json=data)
    return res_format(response)

def predict_single(image_path, caption, output=15, temp=0.7, k=0, rearrange=False):
    code, response = post_single(image_path, caption, output, temp, k, rearrange)
    if code != 200:
        print('ERROR', code)
        quit()
    
    hash = response['hash']
    status = 'QUEUED'
    while status != 'COMPLETE' and code == 200:
        sleep(1)
        code, response = get_status(hash)
        status = response['status']

    if status != 'COMPLETE' or code != 200:
        print('ERROR', code, status)
        quit()

    return response['data']['data'][0], response['data']['durations'][0], response['data']['avg_durations'][0]

if __name__ == '__main__':
    image_path = 'test.jpg'
    image_path = 'https://media.istockphoto.com/photos/red-apple-with-leaf-isolated-on-white-background-picture-id185262648?b=1&k=20&m=185262648&s=170667a&w=0&h=2ouM2rkF5oBplBmZdqs3hSOdBzA4mcGNCoF2P0KUMTM='
    caption = 'Q: Should I kill her?\nA: No. Q: Why not?\nA:'

    # Si on veut sauver les images
    # if 'images' not in os.listdir():
    #     os.mkdir('images')
    # img_data = requests.get(image_path).content
    # with open('images/image_name.jpg', 'wb') as handler:
    #     handler.write(img_data)

    # a mettre dans ton notebook
    # from api import predict_single
    # df['predictions'] = df.apply(lambda row : predict_single(row[0], row[1]), axis=1)

    pred, duration, avg = predict_single(image_path, caption)
    print(pred)