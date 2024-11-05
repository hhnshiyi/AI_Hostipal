import requests

BASE_URL = "http://10.220.138.111:8004"  # 根据你的 FastAPI 服务器地址进行修改

# 指令模型
def get_instruct_model_api(prompt,audio_file):
    def add_text(text_content=None, audio_file_path=None):
        url = f"{BASE_URL}/add_text/"
        files = None
        data = {}
        if text_content:
            data["text_content"] = text_content
        if audio_file_path:
            files = {"audio_files": open(audio_file_path, "rb")}
        response = requests.post(url, data=data, files=files)
        return response.json()

    def predict():
        url = f"{BASE_URL}/predict/"
        response = requests.post(url)

        return response.json()["task_history"][-1]["content"]
    add_text(text_content=prompt,
             audio_file_path=audio_file)

    predict_response = predict()
    print("识别结果:",predict_response)
    return predict_response

# 指令模型
def get_instruct_model_api_only_audio(audio_file):
    print("当前的输入语音文件：",audio_file)
    def add_text(text_content=None, audio_file_path=None):
        url = f"{BASE_URL}/add_text/"
        files = None
        data = {}
        if text_content:
            data["text_content"] = text_content
        if audio_file_path:
            files = {"audio_files": open(audio_file_path, "rb")}
        response = requests.post(url, data=data, files=files)
        return response.json()

    def predict():
        url = f"{BASE_URL}/predict/"
        response = requests.post(url)

        return response.json()["task_history"][-1]["content"]
    add_text(text_content="请你直接返回你听到的内容",
             audio_file_path=audio_file)

    predict_response = predict()
    print("识别结果:",predict_response)
    return predict_response
# 基础模型
def get_base_model_api(audio_file):
    # API的URL
    url = "http://10.220.138.111:8004/generate_caption/"

    # 音频文件路径
    audio_file_path = audio_file

    # 发送POST请求
    with open(audio_file_path, "rb") as audio_file:
        files = {'file': audio_file}
        response = requests.post(url, files=files)

    # 检查请求是否成功
    if response.status_code == 200:
        # 打印生成的描述
        caption = response.json().get("caption", "")
        print("Generated Caption:", caption)
        return caption
    else:
        # 打印错误信息
        print("Error:", response.json().get("error", "Unknown error"))


if __name__ == "__main__":
    # get_base_model_api("/home/ubuntu/ASR_Dataset/sichuan_dataset/WAV/G0007/G0007_0001.wav")
    get_instruct_model_api(r"")

