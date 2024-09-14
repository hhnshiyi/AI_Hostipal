
from DB_option import DB

import json
import time
from datetime import datetime
from chat_tts_api_docker import *
from tqdm import tqdm


if __name__ == '__main__':
    # 创建数据库连接对象，连接到本地数据库
    db = DB(host='localhost', user='root', password='1230', database='ai_follow-up_system')

    # 从数据库中获取记录，表名为 "question_anwser" 和 "hospital_department"
    messages = db.fetch_records("*", "hospital_department")

    url="http://10.220.138.111:8080"
    updated_messages = []
    # 开始进行对应的TTS（文本转语音），并返回语音文件的路径
    for message in messages:
        print(message)
        # 将数据库中的 JSON 字符串转换为 Python 字典
        all_questions_anwsers = json.loads(message["question_anwser"])
        department_id= message["department_id"]
        updated_questions_anwsers = []

        for question_anwser in tqdm(all_questions_anwsers):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # 因为是现合成的，调用TTS合成回复
            doctor_question_audio=f"audio_file/doctor_question_{timestamp}.mp3"

            # 如果描述中包含 "结束"，则跳过该条记录
            if "结束" in question_anwser["description"]:
                break

            # 获取问题文本
            question = question_anwser["question"]
            # 进行 TTS 处理，获取问题语音文件的路径
            question_audio_path = tts(url,question,1111, doctor_question_audio)

            # 将问题语音文件的路径添加到问题字典中
            question_anwser["question_audio_path"] = doctor_question_audio

            # 获取所有答案
            all_anwser = question_anwser["anwsers"]
            updated_anwsers = []

            for index,anwser in enumerate(all_anwser):
                doctor_response_audio = f"audio_file/doctor_response{index}_{timestamp}.mp3"
                # 获取答案文本
                response = anwser["response"]
                # 进行 TTS 处理，获取答案语音文件的路径
                anwser_audio_path = tts(url,response,1111, doctor_response_audio)
                # 将答案语音文件的路径添加到答案字典中
                anwser["anwser_audio_path"] = doctor_response_audio
                updated_anwsers.append(anwser)

            # 更新问题字典中的答案列表
            question_anwser["anwsers"] = updated_anwsers
            updated_questions_anwsers.append(question_anwser)

        # 将更新后的问题答案列表转换为 JSON 字符串，并更新消息字典
        message["question_anwser"] = json.dumps(updated_questions_anwsers, ensure_ascii=False)
        # 更新数据库
        db.insert_or_update_record_to_direct(department_id, message["question_anwser"], "hospital_department")
        print("数据更新成功")
        updated_messages.append(message)

    # 统一的结束语

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    final_message = "若感到身体不适，请及时到医院复查。感谢您的配合，祝您身体健康，如果有任何问题随时联系我们，再见"
    tts(url,final_message,1111, f"audio_file/over_{timestamp}.mp3")






