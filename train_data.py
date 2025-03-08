import os
import re
import requests
import json
import argparse
from pathlib import Path

# Set up the argument parser
parser = argparse.ArgumentParser(description="Process files under the specified directory")
parser.add_argument('--dir', type=str, required=True, help="Path to the directory")
parser.add_argument('--model', type=str, required=True, help="The model name to use (e.g., qwen2.5)")

# Parse command line arguments
args = parser.parse_args()


ollama_url = "http://localhost:11434/v1/chat/completions"

# Define the headers, including the Authorization header with Bearer token
headers = {
    "Content-Type": "application/json"
}


def get_all_files(dir_path):
    path = Path(dir_path)
    files = [str(file) for file in path.rglob('*') if file.is_file()]
    return files

# 定义按块读取大文件的函数
def read_file_in_chunks(file_path, chunk_size=1000):
    """按块读取文件内容，每块最大为chunk_size字符"""
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk

# 微调数据的说明文本，嵌入到每个 chunk 的内容中
instruction = """
针对给定的短文，生成多条能够用于大模型微调的数据，目标是使大模型能够按照文章里的角色进行扮演。 每条数据应该满足以下条件。

1. 数据结构
数据应当以 输入-输出 的形式组织,每个训练示例包含角色的 对话、内心活动、动作描述、表情 和 场景背景。
    输入:表示角色的对话或其他行为,如动作、表情、场景等。
    输出:角色的回应、内心活动、表情变化,或场景/情境的描述。

2. 核心要素
准备训练数据时,要包含以下几类信息:
2.1. 人物对话
提取文本中的人物对话内容,确保每段对话都有明确的角色标签。对话是训练的基础。

2.2. 内心活动
描述人物在特定情境中的心理活动,反映人物的情感状态、动机、冲突等。

2.3. 动作描述
描述人物的肢体动作或其他行为,反映人物的反应或情感,帮助模型理解人物的行为。

2.4. 表情描述
描述人物的面部表情或情感波动,增强情感细腻度。

2.5. 场景描述
提供情境和环境描述,给出角色的行为背景,帮助模型理解上下文。

3. 组合与格式
根据上述要素,将它们组合成完整的训练示例。每个输入输出可以同时包含对话、内心活动、动作、表情和场景描述等元素,使模型能够从多个维度理解和生成对话。

4. 多维度情感训练
    确保内心活动、表情、动作等描述与对话相互关联。
    在训练数据中加入情感变化,如焦虑、愤怒、喜悦、绝望等,使模型能够理解人物情感的多样性。
    描述动作和表情时,应注意与对话和内心活动的协调。例如,人物因某种情感波动而表现出的身体语言(如微笑、皱眉、挥手)应与其对话内容相一致。

5. 训练数据的多样性
    保证训练数据的多样性,包括不同的情境和情感。例如:
        角色在愉快时的对话和行为。
        角色在困境中的心理活动、动作表现和情感变化。
        角色在紧张、冲突或矛盾中的反应。
    添加不同场景的变化,如室内、户外、危险环境等,以增强模型对环境因素的理解。

6. 数据格式
为了方便模型训练, 采用JSON格式, 每个示例都是一个输入输出对。
    示例:
    {
        "input": "[赵敏]（突然倾身向前，眼中寒光闪烁）'为什么？你帮助我的仇人么？'[场景] 窗外夜枭发出凄厉鸣叫",
        "output": "[张无忌]（长叹一声，将酒碗重重放下）'你杀一个人，自己便多一分罪业...'（内心：她终究是蒙古郡主，这般杀伐决断）[动作] 酒液在碗中荡起涟漪"
    }
===========================================================================
以下是需要处理的短文
"""

# 逐块处理文件内容并发送给 Ollama
def process_large_text(file_path):

    idx = 0
    for chunk in read_file_in_chunks(file_path):
        # 对每个块调用 API
        data = {
            "model": args.model,  # Use the model name specified by the user
            "messages": [
                {"role": "system", "content": "你是一个友好的助手。"},
                {"role": "user", "content": f"{instruction}\n\n{chunk}"}  # 加入微调说明和实际文件内容
            ],
            "temperature": 0.7
        }
        print(data)
        response = requests.post(ollama_url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            print("Assistant:", assistant_message)

            # Use regex to find all JSON-like structures in the text
            json_parts = re.findall(r'{.*?}', assistant_message, re.DOTALL)

            # Convert the found JSON strings into Python objects by parsing each one
            data = [json.loads(part) for part in json_parts]
            
            # Write the response into the JSON file
            output_json_file = f"{os.path.splitext(file_path)[0]}.{idx}.json"  # Create a .json file with the same name as the input file
            with open(output_json_file, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            idx = idx + 1
        else:
            print("Error:", response.status_code, response.text)

# pdb.set_trace()  # The debugger will pause here

for file in get_all_files(args.dir):
    process_large_text(file)
