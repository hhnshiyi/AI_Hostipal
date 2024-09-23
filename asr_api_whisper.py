import requests


def send_post_request(url, params, file_path):
    # 使用二进制模式打开本地音频文件
    with open(file_path, 'rb') as audio_file:
        # 定义headers或额外的数据如果API需要的话
        headers = {'Content-Type': 'multipart/form-data'}
        files = {'audio_file': (file_path, audio_file)}

        # 发送POST请求
        response = requests.post(url, params=params, headers=headers, files=files)

    return response.text


# 示例参数
url = "https://172.16.12:9000/asr"
params = {
    "encode": True,
    "task": "transcribe",
    "language": "",
    "initial_prompt": "initial_prompt",
    "word_timestamps": False,
    "output": "txt",
}
file_path = 'common_voice_pt_19273358.wav'

result = send_post_request(url, params, file_path)

print(result)