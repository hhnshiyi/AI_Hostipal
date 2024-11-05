import requests


import requests


def asr(audio_name):
      # 定义URL和请求头
    url = "http://172.16.12.61:9000/asr"

    params = {

    "encode": "true",

    "task": "transcribe",

    "word_timestamps": "false",

    "output": "txt"
    }

    headers = {

    "accept": "application/json",}
    file_path = audio_name
    with open(file_path, 'rb') as audio_file:

        files = {'audio_file': (file_path, audio_file, 'audio/mpeg')}
    response = requests.post(url, params=params, headers=headers, files=files)
 # 输出响应内容
    print(response.text)
