import requests
import json
import argparse

# Set up the argument parser
parser = argparse.ArgumentParser(description="Specify the model for Ollama API")
parser.add_argument('--model', type=str, required=True, help="The model name to use (e.g., qwen2.5)")

# Parse command line arguments
args = parser.parse_args()


ollama_url = "http://localhost:11434/v1/chat/completions"

# Define the headers, including the Authorization header with Bearer token
headers = {
    "Content-Type": "application/json"
}


# 定义按块读取大文件的函数
def read_file_in_chunks(file_path, chunk_size=500):
    """按块读取文件内容，每块最大为chunk_size字符"""
    with open(file_path, 'r', encoding='utf-8') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk

# 微调数据的说明文本，嵌入到每个 chunk 的内容中
instruction = """
针对下面的短文，生成多条能够用于大模型微调的数据，目标是使大模型能够按照文章里的角色进行扮演

微调数据的结构说明： 
    输入：描述当前情境、动作或对话中的背景和人物行为。通常是模型所需要理解的上下文信息。 
    输出：根据当前情境，模拟每个角色在该情境下的对话和行为。输出应具有角色个性特征的语气和情感反应。
"""

# 逐块处理文件内容并发送给 Ollama
def process_large_text(file_path):
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
            print("Assistant:", result['choices'][0]['message']['content'])
        else:
            print("Error:", response.status_code, response.text)

# pdb.set_trace()  # The debugger will pause here

# 调用函数逐块读取并处理大文件
file_path = 'c1.txt'  # 替换为你的文件路径
process_large_text(file_path)
