import json
import os
import random
import sys
import requests
import utils.file_io as fio


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from source.CONST_ENV import CONST_ENV as ENV

def get_api(key_type: str) -> str:
    """
    获取API密钥

    Args:
        kry_type (str): API密钥类型

    Returns:
            str: API密钥
    """
    # 加载api key
    api_keys = fio.load_json(os.path.join(ENV.INFO_PATH, "api_keys.json"))
    api = api_keys["key_type"]
    if type(api) == list:
        return random.choice(api)
    else:
        return api



def get_random_user_agent() -> str:
    """获取随机User-Agent."""

    user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.161 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:60.0) Gecko/20100101 Firefox/60.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.141 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.38",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.47 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.361 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.391 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.171 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.291 Safari/537.36",
    "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.56 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.311 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.191 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.431 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.351 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.131 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.201 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.421 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.301 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.251 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.151 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.271 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.381 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/601.7.7 (KHTML, like Gecko) Version/9.1.2 Safari/601.7.7",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.101 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.211 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.221 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.47 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.121 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.91 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.401 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.181 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.31",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.261 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:94.0) Gecko/20100101 Firefox/94.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.371 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.41 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.331 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.411 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.41 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.231 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.441 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.51 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.31",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.111 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.321 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.281 Safari/537.36"]

    return random.choice(user_agents)


def get_headers() -> dict:
    """获取请求头信息."""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept-Language': 'en-US,en;q=0.9',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    return headers


def create_interval_tuples(start: int, interval_length: int, totalSupply: int) -> list:
    """
    使用给定的间隔和结束值创建一个区间元组列表。

    :param interval: 区间值，整数。
    :param totalSupply: 结束值，整数。
    :return: 一个区间元组列表。
    """
    result = []
    while start < totalSupply:
        result.append((start, min(start + interval_length, totalSupply)))
        start += interval_length
    return result

def create_interval_tuples_for_getNFTsForCollection(start: int, interval_length: int, totalSupply: int) -> list:
    """
    使用给定的间隔和结束值创建一个区间元组列表, 列表中的元素形式为（区间开始，区间间隔）。

    :param interval: 区间值，整数。
    :param totalSupply: 区间结束值，整数。
    :return: 一个区间元组列表。
    """
    result = []
    while start < totalSupply:
        if start + interval_length < totalSupply:
            result.append((start, interval_length))
        else:
            result.append((start, totalSupply - start + 1))
        start += interval_length 
    return result


def generate_payload_for_a_collection(download_range, contractAddress) -> dict:
    """
    生成负载，用于下载一个合约的全部NFT
    Args:
        download_range (tuple): 要下载的区间
        contractAddress (str): 要下载的合约地址

        Returns:
            dict: 负载
    """
    start, end = download_range
    tokens = []
    for index in range(start, end+1):
        tokens.append({
            "contractAddress": contractAddress,
            "tokenId": str(index)
        })
    payload = {
        "tokens": tokens,
        "refreshCache": True
    }
    return payload

def payload_factory_a_collection(start, totalSupply, interval_length, contractAddress) -> list:
    """负载生成器，用于下载一个合约的全部NFT

    Args:
        totalSupply (int): 声明一共要下载多少个NFT
        contractAddress (_type_): 要下载NFT的合约地址

    Returns:
        list: 负载列表
    """
    task_list = create_interval_tuples(start, interval_length, totalSupply)
    payload_list = []
    for task in task_list:
        payload_body = generate_payload_for_a_collection(task, contractAddress)
        payload_list.append(payload_body)
    return payload_list


def create_tasks_for_missing_nft(missing_list: list[int], interval_length: int = 50) -> list[list[int]]:
    """
    使用给定的间隔和结束值将 missing_list 划分为子列表。

    Args:
    :param interval_length: 区间值，整数。
    :param missing_list: 结束值，整数。

    :return: 一个区间元组列表。
    """
    return [missing_list[i:i+interval_length] for i in range(0, len(missing_list), interval_length)]


def generate_payload_for_missing_NFT(missing_list, contractAddress) -> dict:
    """
    生成负载，用于下载 missing_list 中的NFT
    Args:
        download_range (list): 要下载的个别NFT的列表
        contractAddress (str): 要下载的合约地址

        Returns:
            dict: 负载
    """
    tokens = []
    for index in missing_list:
        tokens.append({
            "contractAddress": contractAddress,
            "tokenId": str(index)
        })
    payload = {
        "tokens": tokens,
        "refreshCache": True
    }
    return payload

def generate_payload_for_missing_NFT_by_V4_byNFTScan(missing_list, contractAddress) -> dict:
    """
    生成负载，用于下载 missing_list 中的NFT
    Args:
        download_range (list): 要下载的个别NFT的列表
        contractAddress (str): 要下载的合约地址

        Returns:
            dict: 负载
    """
    tokens = []
    for index in missing_list:
        tokens.append({
            'contract_address': contractAddress,
            'token_id': str(index)
        })
    payload = {
        'show_attribute': 'true',
        'contract_address_with_token_id_list': tokens
    }
    return payload

def payload_factory_for_missing_NFT(missing_list, contractAddress, interval_length=80) -> list:
    """负载生成器，用于missing_list 中的NFT

    Args:
        missing_list (list): 要下载的NFT组成的编号列表
        contractAddress (_type_): 要下载NFT的合约地址

    Returns:
        list: 负载列表
    """

    task_list = create_tasks_for_missing_nft(missing_list, interval_length)
    payload_list = []
    for task in task_list:
        payload_body = generate_payload_for_missing_NFT(task, contractAddress)
        payload_list.append(payload_body)
    return payload_list

def payload_factory_for_missing_NFT_V4_byNFTScan(missing_list, contractAddress, interval_length=80) -> list:
    """负载生成器，用于missing_list 中的NFT

    Args:
        missing_list (list): 要下载的NFT组成的编号列表
        contractAddress (_type_): 要下载NFT的合约地址

    Returns:
        list: 负载列表
    """

    task_list = create_tasks_for_missing_nft(missing_list, interval_length)
    payload_list = []
    for task in task_list:
        payload_body = generate_payload_for_missing_NFT_by_V4_byNFTScan(task, contractAddress)
        payload_list.append(payload_body)
    return payload_list

def get_start_file_index(contract_address) -> int:
    
    """
    判断文件编号是从0开始还是从1开始

    Args:
        contract_address (str): 将要被检查的合约地址

    Returns:
        int: 文件编号从0开始返回0，从1开始返回1
    """

    # 获取随机的alchemy api
    api = get_random_api()
    url = f"https://eth-mainnet.g.alchemy.com/nft/v2/{api}/getNFTMetadata?contractAddress={contract_address}&tokenId=0&refreshCache=false"
    headers = {"accept": "application/json"}
    try:
        print("requesting...")
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response_body = json.loads(response.text)
            # 如果返回的json文件中有error字段，说明文件编号从1开始
            if "error" in response_body.keys():
                return 1
            else:
                return 0
    except Exception as e:
        print(f"Error: {e}")
        return None 


def get_media_format(url: str) -> str:
    """
    获取文件格式，如果文件名包含常见文件扩展名则返回该扩展名
    
    :param url: 文件资源链接
    :return: 文件扩展名例如(".jpg", ".png", ".mp4" 等), 如果无法获取则返回 NULL
    
    """

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        content_type = response.headers.get('Content-Type')
        if content_type:
            fmt = f".{content_type.split('/')[-1]}"
            return fmt
        else:
            common_formats = ['.jpg', '.jpeg', '.png', 'webp', '.gif', '.mp4', ".svg", '.xml']
            for fmt in common_formats:
                if fmt in url:
                    return fmt
    else:
        return None