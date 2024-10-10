import gradio as gr
import requests
import json
from DB_option import DB
from tools import Tools
from audio_format_convert import *
from asr_api_qwen2 import *
from datetime import datetime
from chat_tts_api_docker import *
import time
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
print(script_dir)
# 切换到脚本所在的目录
os.chdir(script_dir)
# 常量定义
DEFAULT_QUESTION = "您好，请问是张三先生/女士或者他的亲属吗？"
END_CONVERSATION = "若感到身体不适，请及时到医院复查。感谢您的配合，祝您身体健康，如果有任何问题随时联系我们，再见"
AUDIO_BASE_PATH = "audio_file/"
COMBINED_AUDIO_PATH = "combine_audio/"
DEFAULT_DOCTOR_AUDIO = f"{AUDIO_BASE_PATH}doctor_question_20240912175406.mp3"

# 全局状态
step = 0  # 对话步骤


# 重置对话步骤
def reset_step():
    global step
    step = 0
    return [(None, DEFAULT_QUESTION)]


# 用户输入处理函数
def user(user_message, history):
    return "", history + [[user_message, None]]

# 根据用户选择获取数据
def get_data_from_db(department_name):
    global messages
    messages = db.fetch_record_by_name("*", "hospital_department", department_name)
    return messages

# 机器人回复处理逻辑
def bot(history):
    global step
    item = messages[0]
    question_answer = json.loads(item['question_anwser'])
    qa = question_answer[step]

    user_input = history[-1][0] if history else ""
    # 判断是否适用
    prompt = tool.read_file(r"E:\PycharmProjects\Hospital_AI\AI_Hostipal\Prompt\jugement.txt").format(
        doctor_question=qa['question'],
        patient_answer=user_input,
        response=qa["anwsers"]
    )

    result_llm = tool.model(prompt, "gpt-4o-mini")
    step += 1

    if step >= len(question_answer):
        next_question = END_CONVERSATION
        next_question_audio_path = f"{AUDIO_BASE_PATH}over_20240912213511.mp3"
    else:
        next_qa = question_answer[step]
        next_question = next_qa['question']
        next_question_audio_path = next_qa['question_audio_path']

    response, doctor_audio_path = generate_response(result_llm, qa, user_input, next_question, next_question_audio_path)

    history[-1][1] = response
    return history, doctor_audio_path


# 构建回复以及回复的音频文件路径
def generate_response(result_llm, qa, user_input, next_question, next_question_audio_path):
    merge_audio_list = []

    if "不适用" in result_llm:
        print(result_llm)
        response_llm = generate_llm_response(qa['question'], user_input)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        answer_audio_path = f'E:\PycharmProjects\Hospital_AI\AI_Hostipal/audio_file\output_{timestamp}.mp3'
        start_time=time.time()
        tts("http://10.220.138.111:8080", response_llm, 1111, answer_audio_path)
        end_time=time.time()
        print("生成音频时间：",end_time-start_time)

        if "再说一遍" in response_llm or "再问一遍" in response_llm:
            global step
            step -= 1
            return response_llm, answer_audio_path

        response = response_llm + next_question
        merge_audio_list = [answer_audio_path, next_question_audio_path]
    else:
        index = 0 if "0" in result_llm else 1
        response_doctor = qa["anwsers"][index]["response"]
        answer_audio_path = qa["anwsers"][index]["anwser_audio_path"]

        if qa['description'] == "确认姓名" and "打错了" in response_doctor:
            return response_doctor, answer_audio_path

        response = response_doctor + next_question
        merge_audio_list = [answer_audio_path, next_question_audio_path]

    doctor_audio_path = merge_and_save_audio(merge_audio_list)
    return response, doctor_audio_path


# 生成 LLM 回复
def generate_llm_response(question, user_input):
    prompt = f"""
    你是一名负责病人回访的医生，请根据病人回答做出简短回复。
    医生问题：{question}
    病人回答：{user_input}
    医生回复：
    """
    return tool.model(prompt, "gpt-4o-mini")


# 合并音频文件
def merge_and_save_audio(audio_list):
    print(audio_list)
    if len(audio_list) == 2:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f'{COMBINED_AUDIO_PATH}combined_audio_{timestamp}.wav'
        # print(audio_list[0])
        # print(audio_list[1])
        # merge_audio_files(audio_list[0], audio_list[1], "1111.wav", 'wav')
        file1 = r'E:\\PycharmProjects\\Hospital_AI\\AI_Hostipal\audio_file/doctor_response0_20240912175434.mp3'
        file2 = r'E:\\PycharmProjects\\Hospital_AI\\AI_Hostipal\audio_file/doctor_question_20240912175438.mp3'
        output_file = f'E:\PycharmProjects\Hospital_AI\AI_Hostipal\combine_audio\combined_audio_{timestamp}.wav'
        output_format = 'wav'  # 指定输出格式为 WAV
        merge_audio_files(file1, file2, output_file, output_format)
        return output_file
    return audio_list[0]


# 创建 Gradio 界面
def create_interface():
    with gr.Blocks(title="AI智能回访系统") as demo:
        department=["神经内科","心血管内科"]
        gr.HTML("<h1 style='color: blue; font-size: 30px; font-weight: bold; text-align: center;'>AI智能回访系统</h1>")
        chatbot = gr.Chatbot([(None, DEFAULT_QUESTION)], avatar_images=("icon/病人类别.png", "icon/医生.png"))
        # 音频输入与输出部分
        with gr.Row(elem_classes="audio-row"):
            audio_file_doctor = gr.Audio(value=DEFAULT_DOCTOR_AUDIO, type="filepath", label="Doctor's Audio")
            audio_file_user = gr.Audio(type="filepath", sources=["microphone"], label="User's Audio")
            with gr.Row(elem_classes="audio-row"):
                asr_button = gr.Button("点击开始语音识别", variant="primary")
                department_dropdown = gr.Dropdown(choices=department, label="Select Department", allow_custom_value=True)


        msg = gr.Textbox(label="Type a message or upload output")
        clear = gr.Button("Clear Chat")
        # 当学院下拉框的值改变时，更新系下拉框的选项
        department_dropdown.change(get_data_from_db, inputs=department_dropdown)
        asr_button.click(get_instruct_model_api_only_audio, inputs=audio_file_user, outputs=msg)
        msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(bot, chatbot, [chatbot, audio_file_doctor])
        clear.click(reset_step, None, chatbot, queue=False)

    return demo


if __name__ == '__main__':
    db = DB(host='localhost', user='root', password='1230', database='ai_follow-up_system')
    tool = Tools()

    demo = create_interface()
    demo.launch(share=True)
