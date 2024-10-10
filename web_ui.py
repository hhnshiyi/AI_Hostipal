import gradio as gr
import requests
import json
from DB_option import DB
from tools import Tools
from audio_format_convert import *
from asr_api_qwen2 import *
import time
from datetime import datetime
from chat_tts_api_docker import *
import torchaudio

print(torchaudio.list_audio_backends())
# 用户输入处理函数
def user(user_message, history):
    """
    处理用户的输入，将输入追加到聊天历史中。
    :param user_message: 用户输入的消息
    :param history: 聊天历史记录
    :return: 更新后的消息和历史记录
    """
    return "", history + [[user_message, None]]  # 将用户输入和空的回复添加到历史中

# 机器人回复函数
step = 0  # 用于追踪对话步骤
doctor_audio = "audio_file/doctor_question_20240912175406.mp3"  # 医生音频文件初始路径
def reset_step():
    global step
    step=0
    return [(None, "您好，请问是张三先生/女士或者他的亲属吗？")]

def bot(history):
    """
    根据聊天历史，生成机器人的回复。
    :param history: 聊天历史记录
    :return: 更新后的聊天历史和医生的音频文件路径
    """
    global step, doctor_audio
    item = messages[0]  # 从数据库中获取的第一条记录
    department_id = item['department_id']  # 获取科室ID
    department = item['department']  # 获取科室名称
    question_anwser = json.loads(item['question_anwser'])  # 解析问题与回答的JSON数据

    print(f"Department ID: {department_id}")
    print(f"Department: {department}")

    qa = question_anwser[step]  # 获取当前步骤的问题和答案

    question = qa['question']  # 当前问题
    description = qa['description']  # 当前问题的描述
    question_audio_path = qa['question_audio_path']  # 当前问题的音频路径
    print(f"Step: {step}")
    print(f"Doctor: {question}")


    user_input = history[-1][0] if history else ""  # 获取用户最新输入
    prompt = tool.read_file("Prompt/jugement.txt").format(
        doctor_question=question, patient_answer=user_input, response=qa["anwsers"])
    merge_audio_list=[]

    # 调用LLM进行判断
    result_llm = tool.model(prompt, "gpt-4o-mini")
    print("判断结果",result_llm)
    step += 1  # 进入下一个步骤
    # 有专门的结束话语，存在相应的位置。
    if step >= len(question_anwser):  # 如果已经到达最后一步，则结束对话
        next_question = "若感到身体不适，请及时到医院复查。感谢您的配合，祝您身体健康，如果有任何问题随时联系我们，再见"
        next_question_audio_path = r"audio_file/over_20240912213511.mp3"
    else:
        qa_next = question_anwser[step]  # 获取下一步的问题

        next_question = qa_next['question']  # 下一个问题

        next_question_audio_path = qa_next['question_audio_path']  # 下一个问题的音频路径
    # 如果不适用就让大模型回复，这里只合成模型回复
    if "不适用" in result_llm:
        prompt=f'''
        你是一名负责病人回访的医生，以了解出院后病人的情况。请你根据下面病人的回答，做出相应的回复。
        医生问题：{question}
        病人回答：{user_input}
        请你直接给出回复，字数不要太多。
        医生回复：
        '''
        response_llm=tool.model(prompt,"gpt-4o-mini")
        timestamp1 = datetime.now().strftime("%Y%m%d%H%M%S")
        # 合成之后的音频文件路径
        anwser_audio_path = f"audio_file/output_{timestamp1}.mp3"
        tts(
            "http://10.220.138.111:8080",
            response_llm,
            1111,
            anwser_audio_path,
        )
        # 如果病人没听清楚，再说一遍，且不加下一个问题
        if "再说一遍" in response_llm or "再问一遍" in response_llm or "没关系" in response_llm:
                step=step-1
                response=response_llm
        else:
            response=response_llm+next_question
        merge_audio_list.append(anwser_audio_path)
        merge_audio_list.append(next_question_audio_path)
    # 如果模板适用，则需要找到合适回答的序号
    else:
        index = 0 if "0" in result_llm else 1  # 根据模型返回结果选择答案
        response_doctor = qa["anwsers"][index]["response"]
        anwser_audio_path=qa["anwsers"][index]["anwser_audio_path"]
        #找错人,不需要接着往下问
        if description =="确认姓名" and "打错了" in response_doctor:
            response = response_doctor
            merge_audio_list.append(anwser_audio_path)
        else:
            response = response_doctor + next_question  # 生成回复
            merge_audio_list.append(anwser_audio_path)
            merge_audio_list.append(next_question_audio_path)

    bot_message = response
    print("Doctor:", bot_message)


    if len(merge_audio_list)==2:
        # 合并医生音频文件
        timestamp2 = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f'combine_audio/combined_audio_{timestamp2}.wav'  # 输出文件路径
        output_format = 'wav'  # 输出音频格式
        merge_audio_files(anwser_audio_path, next_question_audio_path, output_file, output_format)
        doctor_audio = output_file  # 更新医生音频路径
    else:
        doctor_audio = merge_audio_list[0]

    print("-" * 40)

    history[-1][1] = bot_message  # 更新聊天历史中的回复
    return history, doctor_audio  # 返回更新后的历史和医生音频路径

# 主界面创建函数
def create_interface():
    """
    创建Gradio界面。
    :return: 返回Gradio的界面对象
    """
    with gr.Blocks(title="AI智能回访系统") as demo:
        # 标题部分
        gr.HTML("""<h1 style="color: blue; font-size: 30px; font-family: 'Arial, sans-serif'; font-weight: bold; text-align: center; line-height: 1.5; margin: 5px; padding: 3px;">AI智能回访系统</h1>""")

        # 聊天窗口
        chatbot = gr.Chatbot(
            [(None, "您好，请问是张三先生/女士或者他的亲属吗？")],  # 默认消息
            elem_id="chatbot",
            bubble_full_width=False,
            height=400,
            avatar_images=("icon/病人类别.png", "icon/医生.png"),  # 使用患者和医生的头像
        )

        # 音频输入与输出部分
        with gr.Row(elem_classes="audio-row"):
            audio_file_doctor = gr.Audio(value=doctor_audio, type="filepath", label="Doctor's Audio")  # 医生音频
            audio_file_user = gr.Audio(type="filepath", sources=["microphone"],label="User's Audio")  # 用户音频
            with gr.Row(elem_classes="audio-row"):

                asr_button = gr.Button("点击开始语音识别", variant="primary")  # ASR按钮


        # 消息输入框与清除按钮
        msg = gr.Textbox(label="Type a message or upload output")  # 输入框
        clear = gr.Button("Clear Chat")  # 清除聊天按钮

        # 绑定音频转文本功能
        asr_button.click(get_instruct_model_api_only_audio, inputs=audio_file_user, outputs=msg)
        # 绑定用户输入和机器人回复
        msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot, chatbot, [chatbot, audio_file_doctor]
        )
        # 绑定清除聊天功能
        clear.click(reset_step,None,chatbot, queue=False)

    return demo  # 返回创建的界面对象

if __name__ == '__main__':
    # 初始化数据库和工具类
    db = DB(host='localhost', user='root', password='1230', database='ai_follow-up_system')  # 连接数据库
    tool = Tools()  # 初始化工具类

    # 从数据库中获取记录，表名为 "hospital_department"
    messages = db.fetch_record_by_name("*", "hospital_department", "神经内科")
    print(messages)
    # 启动界面
    demo = create_interface()
    demo.launch(share=True)  # 启动Gradio界面
