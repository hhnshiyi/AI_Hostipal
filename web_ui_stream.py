import gradio as gr

import json
from DB_option import DB
from tools import Tools
from audio_format_convert import *
from asr_function.asr_api_qwen2 import *
from datetime import datetime
from tts_func.chat_tts_api_docker import *
from asr_function.asr_api_sensevoice import *

import os
import logging

from tts_func.cosyvoice_client import main

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    handlers=[
        logging.FileHandler("chatbot_debug.log"),  # 将日志写入文件
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

# 获取模块的日志记录器
logger = logging.getLogger(__name__)

# 获取当前脚本的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))


# 常量定义
DEFAULT_QUESTION = "您好，请问是张三先生/女士或者他的亲属吗？"
END_CONVERSATION = "若感到身体不适，请及时到医院复查。感谢您的配合，祝您身体健康，如果有任何问题随时联系我们，再见"
AUDIO_BASE_PATH = "audio_file/"

DEFAULT_DOCTOR_AUDIO = f"{AUDIO_BASE_PATH}doctor_question_20240912175406.mp3"

# 全局状态
step = 0  # 对话步骤
messages = []  # 定义全局 messages 变量


# 重置对话步骤
def reset_step():
    global step
    logger.info("Resetting conversation step.")
    step = 0
    return [(None, DEFAULT_QUESTION)]


# 根据用户选择获取数据
def get_data_from_db(department_name="神经内科"):
    global messages
    logger.info(f"Fetching data for department: {department_name}")
    try:
        messages = db.fetch_record_by_name("*", "hospital_department", department_name)
        logger.info(f"Fetching data for department: {messages}")
        return [(None, DEFAULT_QUESTION)]  # 重置聊天记录
    except Exception as e:
        logger.error(f"Error fetching data from DB: {e}")
        return [(None, DEFAULT_QUESTION)]


# 用户输入处理函数
def user(user_message, history):
    return "", history + [[user_message, None]]

# 清除用户音频
def clear_user_audio():
    logger.info("Clearing user audio.")
    return None


# 机器人回复处理逻辑
def bot(history):
    global step

    if not messages:
        logger.warning("No messages found. Returning default question.")
        return history, DEFAULT_DOCTOR_AUDIO

    try:
        item = messages[0]
        question_answer = json.loads(item['question_anwser'])
        logger.info("Parsed question-answer JSON.")
        qa = question_answer[step]

        user_input = history[-1][0]
        logger.info(f"User input: {user_input}")

        # 判断是否适用
        prompt = tool.read_file("Prompt/jugement.txt").format(
            doctor_question=qa['question'],
            patient_answer=user_input,
            response=qa["anwsers"]
        )

        result_llm = tool.model(prompt, "gpt-4o-mini")

        step += 1

        if step >= len(question_answer):
            next_question = END_CONVERSATION


        else:
            next_qa = question_answer[step]
            next_question = next_qa['question']



        response= generate_response(result_llm, qa, user_input, next_question,)
        history[-1][1] = response
        logger.info(f"Bot response set: {response}")

        # 获取音频生成器
        audio_stream = main(response)  # 假设 main(response) 返回一个生成器，逐步生成音频数据

        # 遍历音频流，并逐步更新 audio_output
        for audio_chunk in audio_stream:
            logger.info(f"Generated audio chunk: {audio_chunk}")
            # 确保 audio_chunk 是有效的文件路径或兼容的音频数据
            yield history, audio_chunk

        logger.info("Audio stream generation completed.")
    except Exception as e:
        logger.error(f"Error in bot function: {e}")
        return history, DEFAULT_DOCTOR_AUDIO



# 构建回复以及回复的音频文件路径
def generate_response(result_llm, qa, user_input, next_question):


    try:
        if "不适用" in result_llm:
            logger.info(f"Result indicates '不适用'. Generating LLM response：{result_llm}")
            response_llm = generate_llm_response(qa['question'], user_input)

            if "再说一遍" in response_llm or "再问一遍" in response_llm:

                global step
                step -= 1
                return response_llm

            response = response_llm + next_question

        else:
            index = 0 if "0" in result_llm else 1
            response_doctor = qa["anwsers"][index]["response"]


            if qa['description'] == "确认姓名" and "打错了" in response_doctor:

                return response_doctor

            response = response_doctor + next_question


        return response

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "抱歉，发生了错误。"


# 生成 LLM 回复
def generate_llm_response(question, user_input):

    try:
        prompt = f"""
        你是一名负责病人回访的医生，请根据病人回答做出简短回复。
        医生问题：{question}
        病人回答：{user_input}
        医生回复：
        """

        response = tool.model(prompt, "gpt-4o-mini")
        logger.info(f"LLM Response received: {response}")
        return response
    except Exception as e:
        logger.error(f"Error generating LLM response: {e}")
        return "抱歉，无法生成回复。"


# 创建 Gradio 界面
def create_interface():

    with gr.Blocks(title="AI智能回访系统") as demo:
        department = ["神经内科", "心血管内科"]
        gr.HTML("<h1 style='color: blue; font-size: 30px; font-weight: bold; text-align: center;'>AI智能回访系统</h1>")
        chatbot = gr.Chatbot([(None, DEFAULT_QUESTION)], avatar_images=("icon/病人类别.png", "icon/医生.png"))
        # 音频输入与输出部分
        with gr.Row(elem_classes="audio-row"):
            audio_file_doctor = gr.Audio(
                # value=DEFAULT_DOCTOR_AUDIO,
                autoplay=True,
                sources=['upload', 'microphone'],
                streaming=True,
                label="Doctor's Audio"
            )
            audio_file_user = gr.Audio(
                type="filepath",
                sources=["microphone"],
                label="User's Audio",
                streaming=True
            )
            with gr.Row(elem_classes="audio-row"):
                # asr_button = gr.Button("点击开始语音识别", variant="primary")
                department_dropdown = gr.Dropdown(
                    choices=department,
                    label="Select Department",
                    allow_custom_value=True
                )


        msg = gr.Textbox(label="Type a message or upload output")
        clear = gr.Button("Clear Chat")
        # 当学院下拉框的值改变时，更新系下拉框的选项
        department_dropdown.change(get_data_from_db, inputs=department_dropdown, outputs=chatbot)

        # 设置流式输入

        audio_file_user.stream(speech_to_text, inputs=[audio_file_user,msg], outputs=msg)

        msg.submit(
            user,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],

        ).then(
            bot,
            inputs=chatbot,
            outputs=[chatbot, audio_file_doctor]
        ).then(
            clear_user_audio,
            outputs=audio_file_user
        )

        clear.click(reset_step, inputs=None, outputs=chatbot)
        logger.info("Clear button click event set.")

    logger.info("Gradio interface creation completed.")
    return demo


if __name__ == '__main__':
    try:
        logger.info("Starting chatbot application.")
        db = DB(host='localhost', user='root', password='1230', database='ai_follow-up_system')
        tool = Tools()
        logger.info("Database and Tools initialized.")

        demo = create_interface()
        logger.info("Launching Gradio interface.")

        demo.launch(server_name="0.0.0.0", share=True)

    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
