import os
import datetime
import os
import zipfile
from io import BytesIO
import requests
chattts_service_host = os.environ.get("CHATTTS_SERVICE_HOST", "localhost")
chattts_service_port = os.environ.get("CHATTTS_SERVICE_PORT", "8080")

CHATTTS_URL = f"http://10.220.138.110:8090/generate_voice"
import json
def get_tts(text):
    # main infer params
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # print("当前脚本所在的目录是:", script_dir)
    body = {
        "text": text,
        "stream": False,
        "lang": None,
        "skip_refine_text": True,
        "refine_text_only": False,
        "use_decoder": True,
        "audio_seed": 12345678,
        "text_seed": 87654321,
        "do_text_normalization": True,
        "do_homophone_replacement": False,
    }

    # refine text params
    params_refine_text = {
        "prompt": "",
        "top_P": 0.7,
        "top_K": 20,
        "temperature": 0.7,
        "repetition_penalty": 1,
        "max_new_token": 384,
        "min_new_token": 0,
        "show_tqdm": True,
        "ensure_non_empty": True,
        "stream_batch": 24,
    }
    body["params_refine_text"] = params_refine_text

    # infer code params
    params_infer_code = {
        "prompt": "[speed_3]",
        "top_P": 0.1,
        "top_K": 20,
        "temperature": 0.3,
        "repetition_penalty": 1.05,
        "max_new_token": 2048,
        "min_new_token": 0,
        "show_tqdm": True,
        "ensure_non_empty": True,
        "stream_batch": True,
        "spk_emb": None,
        "custom_voice": 1111
    }
    body["params_infer_code"] = params_infer_code
    try:
        response= requests.post(CHATTTS_URL, json=body)
        response.raise_for_status()
        # Extract filenames from the headers
        filename = json.loads(response.headers.get("X-Filenames", "[]"))
        print("生成的文件名：", filename)
        with zipfile.ZipFile(BytesIO(response.content), "r") as zip_ref:
            # save files for each request in a different folder
            # 使用 os.path.join 处理路径
            tgt = os.path.join(

                "audio",
            )

            zip_ref.extractall(tgt)
            print("Extracted files into", tgt)

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    audio_path=os.path.join(

        "audio",
                filename
            )
    return audio_path
def add_audio_to_json(instructions):
    """
    Adds audio paths to the given JSON instructions by synthesizing text fields.

    Args:
        instructions (list): A list of dictionaries containing 'text' fields.

    Returns:
        list: Updated list with audio paths added.
    """
    updated_instructions = []
    for instruction in instructions:
        audio_path = get_tts(instruction['text'])
        instruction['audio'] = audio_path
        updated_instructions.append(instruction)
    return updated_instructions
if __name__ == '__main__':

    # 读取 JSON 文件
    with open('Instruct_data/audio-text-Instruct.json', 'r',encoding="utf-8") as file:
        data = json.load(file)

    # 添加音频路径
    updated_data = add_audio_to_json(data)

    # 输出处理后的数据
    print(json.dumps(updated_data, indent=2))

    # 将更新后的数据写入新的 JSON 文件
    with open('Instruct_data/instructions_with_audio.json', 'w', encoding='utf-8') as file:
        json.dump(updated_data, file, indent=2, ensure_ascii=False)
