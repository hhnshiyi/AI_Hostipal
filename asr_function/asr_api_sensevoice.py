import requests
import os




def speech_to_text(speeches, msg,lang="zh"):
    """
    将上传的音频文件转为文本。
    :param speeches: 包含多个音频文件路径的列表
    :param lang: 音频内容的语言，默认为中文（zh）
    :return: 识别后的文本
    """
    global current_text
    print("正在识别音频文件...")
    print(speeches)
    url = "http://10.220.138.111:8001/api/v1/asr"  # asr_function API 接口地址
    files = []
    keys_list = []
    if type(speeches) is not list:

           speeches = [speeches]

    for i, speech in enumerate(speeches):
        try:
            f = open(speech, "rb")
            files.append(("files", f))
            key = os.path.splitext(os.path.basename(speech))[0]  # 使用文件名作为key
            keys_list.append(key)
        except FileNotFoundError:
            print(f"错误：文件 '{speech}' 未找到。")
            continue
    if not files:
        print("没有有效的音频文件上传。")
        return None
    keys = ",".join(keys_list) if keys_list else "audio_tmp_name"
    data = {"keys": keys, "lang": lang}  # 设置请求参数
    try:
        response = requests.post(url, files=files, data=data)  # 发送POST请求
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP请求错误：{e}")
        return None
    finally:
        for _, file in files:
            file.close()

    try:
        response_json = response.json()
        print(response_json)  # 输出返回结果
        results = response_json.get("result", [])
        if not results:
            print("没有识别结果。")
            return current_text
        for result in results:
            new_text = result.get("clean_text", "")
            msg += new_text + " "  # 可选：添加空格分隔
        return msg.strip()  # 返回识别后的文本，去除末尾空格
    except (ValueError, KeyError, IndexError) as e:
        print(f"处理响应时出错：{e}")
        return None


if __name__ == '__main__':
    # 单个文件识别
    # speech_to_text(["demo.wav"], lang="zh")

    # 多个文件识别
    speech_files = ["demo.wav", "demo2.wav"]

    language = "zh"  # 例如：中文
    recognized_text = speech_to_text(speech_files, lang=language)
    if recognized_text:
        print("识别结果：")
        print(recognized_text)
    else:
        print("识别失败或无结果。")
