import gradio as gr
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 的模块搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from source.CONST_ENV import CONST_ENV as ENV
from utils import file_io as fio
from utils import spider_toolbox as stb
from utils import downloading_toolbox as dtb

# 从 JSON 文件加载区块链信息
platform_info = fio.load_json(ENV.INFO_PATH / "platform_info.json")
# 获取初始平台的初始选项
initial_platform = "Alchemy"
initial_chain_options = platform_info.get(initial_platform, [])
# 用于跟踪下载状态的全局变量
is_downloading = False  # 初始状态为未下载

def update_options(platform):
    """设置回调函数，当第一个下拉列表变化时，更新第二个下拉列表的选项"""
    return gr.update(choices=platform_info.get(platform, []))

def toggle_download_button():
    """切换按钮状态"""
    global is_downloading  # 使用 global 声明来修改全局变量
    if is_downloading:
        # 当前正在下载，点击后应停止下载
        is_downloading = False
        return gr.update(value="Download", variant="primary")  # 恢复为蓝色
    else:
        # 当前未下载，点击后应开始下载
        is_downloading = True
        return gr.update(value="Stop", variant="stop")  # 变为红色，表示停止

def download_nft_collection(contract_address, platform, chain_type, process_num, thread_num, save_path):
    """下载整个 NFT 集合"""
    if contract_address is None or contract_address == "":
        raise ValueError("Contract address cannot be empty!")
    
    # 去掉contract_address最后可能存在的空格
    contract_address = contract_address.strip()

    # 将chain_type转换为小写
    chain_type = chain_type.lower()

    # 获取 NFT 集合信息
    target_collection_path = ENV.INFO_PATH / f"{chain_type}_target_collection_info.json"
    target_collection_info = fio.load_json(target_collection_path)
    if target_collection_info is None:
        # 创建文件并保存
        collection_info = stb.get_target_collection_info(chain_type= chain_type, contract_address= contract_address)
        collection_info_json = {contract_address: collection_info}
        fio.save_json(target_collection_path, collection_info_json)

    elif target_collection_info.get(contract_address) is None:
        # 更新文件并保存
        collection_info = stb.get_target_collection_info(chain_type= chain_type, contract_address= contract_address)
        target_collection_info[contract_address] = collection_info
        fio.save_json(target_collection_path, target_collection_info)
    else:
        collection_info = target_collection_info[contract_address]

    # 构建下载器的参数列表
    args_dict = {
        "NFT_name": collection_info["NFT_name"],
        "chain_type": collection_info["chain_type"],
        "contract_address": collection_info["contract_address"],
        "total_supply": collection_info["total_supply"],
        "candidate_format": collection_info["candidate_format"],
        "start_index": collection_info["start_index"],
        "process_num": process_num,
        "thread_num": thread_num,
        "save_path": Path(save_path)
    }

    if platform == "Alchemy":
        # 构建 Alchemy 下载器
        NFT_downloader = dtb.NFT_Downloader_for_Whole_Collection_Alchemy(**args_dict)
    elif platform == "NFTScan":
        # 构建 NFTScan 下载器
        NFT_downloader = dtb.NFT_Downloader_for_Whole_Collection_NFTScan(**args_dict)
    elif platform == "NFTGo":
        # 构建 NFTGo 下载器
        NFT_downloader = dtb.NFT_Downloader_for_Whole_Collection_NFTGo(**args_dict)
    elif platform == "OpenSea":
        # 构建 OpenSea 下载器
        NFT_downloader = dtb.NFT_Downloader_for_Whole_Collection_OpenSea(**args_dict)
    else:
        raise ValueError("Platform not supported!")
    
    # 开始下载
    NFT_downloader.download_media_and_metadata()



if __name__ == "__main__":

# 创建 Gradio 接口
    with gr.Blocks(theme=gr.themes.Soft()) as demo:

        with gr.Tab("Download Entire NFT Collection"):
            gr.Markdown("# Single Download")

            contract_address = gr.Textbox(label="Contract Address", 
                                        placeholder="Input contract address here",
                                        value="0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d")
            
            platform = gr.Dropdown(
                label="Platform",
                choices=list(platform_info.keys()),
                interactive=True,
                value=initial_platform
            )
            
            chain_type = gr.Dropdown(
                label="Chain Type",
                choices=initial_chain_options,  # 设置初始选项
                interactive=True,
                value="Ethereum"
            )
            
            # 连接回调函数，当第一个下拉列表变化时，更新第二个下拉列表的选项
            platform.change(update_options, inputs=platform, outputs=chain_type)
            process_num = gr.Slider(label="Process Number", minimum=1, maximum=8, step=1, value=4, interactive=True)
            thread_num = gr.Slider(label="Thread Number Per Process", minimum=1, maximum=10, step=1, value=6, interactive=True)
            
            # 使用文本框让用户输入保存路径
            save_path = gr.Textbox(label="Save Path", placeholder="Enter the path where you want to save files", interactive=True, value=f"{ENV.DATASET_PATH}")

            # 创建按钮，点击后开始下载，再次点击停止下载
            download_button = gr.Button(value="Download", variant="primary")
            download_button.click(
                toggle_download_button,
                inputs=[],
                outputs=download_button
            )
            download_button.click(
                download_nft_collection,
                inputs=[contract_address, platform, chain_type, process_num, thread_num, save_path],
                outputs=[]
            )

        with gr.Tab("Add missing NFTs"):
            gr.Markdown("# Coming soon!")



    # 启动 Gradio 接口
    demo.launch(server_port=5645)
