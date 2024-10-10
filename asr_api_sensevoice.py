import requests

def speech_to_text(speech):
    """
    将上传的音频文件转为文本。
    :param speech: 用户上传的音频文件路径
    :return: 识别后的文本
    """
    url = "http://10.220.138.111:8001/api/v1/asr"  # ASR API 接口地址
    files = {"files": open(speech, "rb")}  # 读取音频文件
    data = {"keys": "audio1", "lang": "zh"}  # 设置请求参数
    response = requests.post(url, files=files, data=data)  # 发送POST请求
    print(response.json())  # 输出返回结果
    return response.json()["result"][0]["clean_text"]  # 返回识别后的文本

