# Copyright (c) 2024 Alibaba Inc (authors: Xiang Lyu)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import logging
import requests
import torch
import torchaudio
import numpy as np

# torchaudio.set_audio_backend("sox_io")
parser = argparse.ArgumentParser()
parser.add_argument('--host',
                    type=str,
                    default='10.220.138.111')
parser.add_argument('--port',
                    type=int,
                    default='8019')
parser.add_argument('--mode',
                    default='sft',
                    choices=['sft', 'zero_shot', 'cross_lingual', 'instruct'],
                    help='request mode')
parser.add_argument('--tts_text',
                    type=str,
                    default='该代码段通过HTTP请求实现了流式的语音合成，能够逐块接收合成音频数据，减少内存压力，并且根据不同的请求模式灵活处理输入。整体流程涵盖了请求构建、音频数据接收和处理、以及最终的音频文件保存。如果有特定的部分需要更深入的解释，请告诉我！')
parser.add_argument('--spk_id',
                    type=str,
                    default='中文女')
parser.add_argument('--prompt_text',
                    type=str,
                    default='希望你以后能够做的比我还好呦。')
parser.add_argument('--prompt_wav',
                    type=str,
                    default='../../../zero_shot_prompt.wav')
parser.add_argument('--instruct_text',
                    type=str,
                    default='Theo \'Crimson\', is a fiery, passionate rebel leader. \
                                Fights with fervor for justice, but struggles with impulsiveness.')
parser.add_argument('--tts_wav',
                    type=str,
                    default='demo.wav')
args = parser.parse_args()
prompt_sr, target_sr = 16000, 22050
def main(text):
    url = "http://{}:{}/inference_{}".format(args.host, args.port, args.mode)
    if args.mode == 'sft':
        payload = {
            'tts_text': text,
            'spk_id': args.spk_id
        }
        response = requests.request("GET", url, data=payload, stream=True)

    elif args.mode == 'zero_shot':
        payload = {
            'tts_text': args.tts_text,
            'prompt_text': args.prompt_text
        }
        files = [('prompt_wav', ('prompt_wav', open(args.prompt_wav, 'rb'), 'application/octet-stream'))]
        response = requests.request("GET", url, data=payload, files=files, stream=True)
    elif args.mode == 'cross_lingual':
        payload = {
            'tts_text': args.tts_text,
        }
        files = [('prompt_wav', ('prompt_wav', open(args.prompt_wav, 'rb'), 'application/octet-stream'))]
        response = requests.request("GET", url, data=payload, files=files, stream=True)
    else:
        payload = {
            'tts_text': args.tts_text,
            'spk_id': args.spk_id,
            'instruct_text': args.instruct_text
        }
        response = requests.request("GET", url, data=payload, stream=True)
    tts_audio = b''
    audio_chunks = []

    for chunk in response.iter_content(chunk_size=16000):
        tts_audio += chunk
        audio_array = np.frombuffer(chunk, dtype=np.int16)
        audio_chunks.append(audio_array)
        # You can update the Gradio interface with the current chunk here
        yield (22050,audio_array)  # Yielding current audio chunk
    tts_speech = torch.from_numpy(np.array(np.frombuffer(tts_audio, dtype=np.int16))).unsqueeze(dim=0)
    print(tts_speech)
    logging.info('save response to {}'.format(args.tts_wav))
    torchaudio.save(args.tts_wav, tts_speech, target_sr)
    logging.info('get response')


if __name__ == "__main__":


    audio_stream=main("我们走的每一步，都是我们策略的一部分；你看到的所有一切，包括我此刻与你交谈，所做的一切，所说的每一句话，都有深远的含义。")


        # 确保 audio_chunk 是有效的文件路径或兼容的音频数据

