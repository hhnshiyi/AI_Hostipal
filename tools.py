import os
from openai import OpenAI
from langchain_openai import ChatOpenAI

from collections import Counter
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
import datetime
import json
# 忽略所有警告
import warnings

from tqdm import tqdm

warnings.filterwarnings("ignore")


class Tools:
    def __init__(self):
        self.current_time = datetime.datetime.now().strftime("%Y%m%d%H%M")
        self.party_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.lawyer_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.model_config = {
            "model_name": [
                "glm",
                "gpt",
                "deepseek",
                "moonshot"
            ],
            "config": [
                {
                    "name": "glm",
                    "api_key": "1be72ae4afc8299aaaf00011c1b0bb24.8yAKxypUfj5H5Jig",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4/"
                },
                {
                    "name": "gpt",
                    "api_key": "sk-sidDDHsX7zwPtD7K75C129E0177f4d0b9c28F6B1C3Ce1127",
                    "base_url": "https://api.rcouyi.com/v1"
                },
                {
                    "name": "deepseek",
                    "api_key": "sk-1cdf8c5d0cb5442eac575c444821fa6a",
                    "base_url": "https://api.deepseek.com/v1"
                },
                {
                    "name": "moonshot",
                    "api_key": "sk-lSc2EpX8GpyPnOjQDEb9WKiQHSzGJ0zWKMwhzyBdzAzJ2bqO",
                    "base_url": "https://api.moonshot.cn/v1"
                }
            ]
        }

    def read_file(self, path):
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content

    def write_to_json(self, filename, content):
        with open(filename, 'w', encoding="utf-8") as file:
            json.dump(content, file, indent=4, ensure_ascii=False)

    def find_mode(self, lst):
        if not lst:
            return None  # 如果列表为空，返回 None

        counter = Counter(lst)
        mode, count = counter.most_common(1)[0]  # 获取出现频率最高的元素及其频率
        return mode

    def generateprompt(self, personality, policy, party):
        # 读取 JSON 文件
        with open('prompt/classify_prompt_v2.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        try:
            personality = data["personality"][personality]
            policy = data["policy"][policy]

        except KeyError as e:
            print(f"参数错误: 缺少字段 {e}")
        # 读取文件内容
        with open("prompt/lawyer_v2.txt", 'r', encoding='utf-8') as file:
            content = file.read()

        # 替换占位符
        content = content.format(party=party, personality=personality, policy=policy)
        return content

    def model(self, promte, model_name, format="text", n=1):
        for model in self.model_config["config"]:
            if model["name"] in model_name.lower():
                api_key = model["api_key"]
                base_url = model["base_url"]

        client = OpenAI(
            api_key=api_key,
            base_url=base_url

        )
        completion = client.chat.completions.create(
            model=model_name,
            response_format={"type": format},
            messages=[
                {"role": "system", "content": "你是一个有用的智能助手"},
                {"role": "user",
                 "content": promte}
            ],
            top_p=0.5,
            temperature=0.2,
            n=n
        )

        # print(completion.choices[0].message)
        all_reslut = []
        if n == 1:
            return completion.choices[0].message.content
        else:
            for item in completion.choices:
                all_reslut.append(item.message.content)
            return all_reslut

    def init_chatbot(self, template, model_name, memory):
        for model in self.model_config["config"]:
            if model["name"] in model_name.lower():
                api_key = model["api_key"]
                base_url = model["base_url"]

        llm = ChatOpenAI(temperature=0.6,
                         model=model_name,
                         openai_api_key=api_key,
                         openai_api_base=base_url
                         # base_url="http://10.220.138.110:8000/v1",
                         # api_key="EMPTY",

                         )
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_message_prompt = HumanMessagePromptTemplate.from_template("{question}")
        prompt = ChatPromptTemplate(
            messages=[system_message_prompt, MessagesPlaceholder(variable_name="chat_history"), human_message_prompt])

        conversation = LLMChain(llm=llm, prompt=prompt, memory=memory)

        return conversation


if __name__ == '__main__':
    pass
    # 调用示例
    agent = Tools()
    memore = agent.party_memory
    role1 = agent.init_chatbot("", "glm-4", memore)
    response = role1({"question": "你是那个公司开发的"})["text"]
    print(response)
    # response=agent.model("你是谁","glm-4","text",1)
    # print(response)








