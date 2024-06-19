import functools
import io
import json
import multiprocessing as mp
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import urllib
from abc import ABC, abstractmethod
from pathlib import Path
import re


import requests
import utils.file_io as fio
import utils.spider_toolbox as stb
from internetdownloadmanager import Downloader
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from source.CONST_ENV import CONST_ENV as ENV

# 用于生成payload的工厂类，可以根据需要生成不同的NFT资源payload
class PayloadFactory:
    def __init__(self,
                candidate_format: str,
                start=0,
                interval_length=80,
                total_supply=0):

        self.start = start
        self.interval_length = interval_length
        self.total_supply = total_supply
        self.candidate_format = candidate_format

    def create_interval_tuples_with_start_end(self) -> list:
        """
        使用给定的间隔和结束值创建一个区间元组列表。

        :return: 一个区间元组列表。
        """
        result = []
        start = self.start
        while start < self.totalSupply:
            result.append((start, min(start + self.interval_length, self.totalSupply)))
            start += self.interval_length
        return result

    def create_interval_tuples_with_start_len(self) -> list:
        """
        使用给定的间隔和结束值创建一个区间元组列表, 列表中的元素形式为（区间开始，区间间隔）。

        :return: 一个区间元组列表。
        """
        result = []
        start = self.start
        while start < self.total_supply:
            if start + self.interval_length < self.total_supply:
                result.append((start, self.interval_length))
            else:
                result.append((start, self.total_supply - start + 1))
            start += self.interval_length
        return result
    

    def create_tasks_for_missing_nft(self, missing_list: list[int]) -> list[list[int]]:
        """
        使用给定的间隔和结束值将 missing_list 划分为子列表。

        Args:
        :param interval_length: 区间值，整数。
        :param missing_list: 结束值，整数。

        :return: 一个区间元组列表。
        """
        return [missing_list[i:i+self.interval_length] for i in range(0, len(missing_list), self.interval_length)]


# 定义一个NFT下载器类的通用接口类，使用不同平台的下载器类继承这个接口类
class NFT_Downloader(ABC):

    def __init__(self,  
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num: int,
                thread_num: int,
                total_supply: int):

        self.chain_type = chain_type
        self.NFT_name = NFT_name
        self.contract_address = contract_address
        self.candidate_format = candidate_format
        self.save_path = Path(save_path)
        self.process_num = process_num
        self.thread_num = thread_num
        self.total_supply = total_supply


    # 生成payload的抽象方法，生成不同平台的payload
    def generate_payload(self, *args, **kwargs):
        pass

    @abstractmethod
    def download_media_and_metadata(self) -> None:
        pass

    # 定义单个下载进程的抽象方法
    def single_process_worker(self,  *args, **kwargs) -> None:
        pass

    # 定义解析响应的抽象方法
    @abstractmethod
    def parse_response(self, response) -> dict:
        pass

    # 定义下载media资源的抽象方法，因为不同平台的media资源下载方式不同
    # 并且都是以链接的形式给到
    @abstractmethod
    def media_downloader(self,  *args, **kwargs) -> None:
        pass
    
    # 定义媒体下载器的单个工作线程的方法,不强制要求实现
    def media_downloader_worker(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    # 定义使用资源链接的形式下载metadata的方法
    def metadata_downloader(self, *args, **kwargs) -> None:
        pass

    #使用请求中返回的metadata数据批量保存metadata
    def save_metadata_batch(self, metadata):
        pass
    
    #定义下载metadata的单个工作线程的方法，不强制要求实现
    def metadata_downloader_worker(self, *args, **kwargs) -> None:
        pass

class NFT_Downloader_for_Whole_Collection(NFT_Downloader):
    
    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num: int,
                thread_num: int,
                total_supply: int,
                start_index: int,
                interval_length: int):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply)
        self.start_index = start_index
        self.interval_length = interval_length

    # 本质上还是一个抽象方法
    @abstractmethod
    def download_media_and_metadata(self) -> None:
        pass

    def media_downloader(self, media_source) -> None:
        # 启用多线程下载图片
        with ThreadPoolExecutor(max_workers=self.thread_num) as executor:
            executor.map(self.media_downloader_worker, media_source.items())
            # 等待所有线程完成
            executor.shutdown(wait=True)

    def media_downloader_worker(self, source_item) -> None:
        """
        启用idm下载图片

        Args:
            source_item (dict): 图片的资源字典, key 为 tokenId, value 为 url资源字典
        """

        key, value = source_item
        base_path = self.save_path.joinpath(f"{self.NFT_name}/img")

        download_success = False  # 用于标记是否成功下载

        # 遍历source_list中的所有链接，下载成功一次即退出
        for source_url in value["source_list"]:
            if source_url is not None:
                file_path = base_path.joinpath(f"{key}{value['format']}")
                # 如果是IPFS资源，则使用IPFS专用的下载方法 
                if CID := is_ipfs_cid(source_url):
                    download_success = download_from_IPFS(CID, file_path)
                    if download_success:
                        break
                # 如果是http资源，则使用普通的下载方法
                else:
                    downloader = Downloader()
                    try:
                        downloader.download(url=source_url, path=file_path)
                        print(f"{self.NFT_name} {file_path.name} downloaded successfully.")
                        download_success = True
                        break  # 如果成功，则退出方法
                    except Exception as e:
                        print(f"Error downloading image {key} from {source_url}: {e}")

        if not download_success:
            print(f"None exits valid media source for {file_path.name}.")

    def metadata_downloader(self, metadata_source) -> None:
        # 启用多线程下载metadata
        with ThreadPoolExecutor(max_workers=self.thread_num) as executor:
            executor.map(self.metadata_downloader_worker, metadata_source.items())
            # 等待所有线程完成
            executor.shutdown(wait=True)

    def metadata_downloader_worker(self, source_item) -> None:
        """下载metadata文件

        Args:
            source_item (dict): metadata资源字典, key 为 tokenId, value 为 json文件和 url资源字典

        Returns:
            None:
        """
        key, value = source_item
        base_path = self.save_path.joinpath(f"{self.NFT_name}/metadata")
        file_path = base_path.joinpath(f"{key}.json")

        # 如果raw字段里存在metadata，直接保存
        if metadata := value.get('raw', None):
            # 将数据格式化成json格式保存
            fio.save_json(file_path, metadata)
            print(f"{self.NFT_name} {file_path.name} saved successfully.")

        # 如果tokenUri字段不为空，下载tokenUri指向的json文件
        elif value["tokenUri"] is not None:
            try:
                response = requests.get(value["tokenUri"])
                if response.status_code == 200:
                    fio.save_json(file_path, response.json())
                    print(f"{self.NFT_name} Metadata {file_path.name} saved successfully.")
                else:
                    print(f"Failed to download metadata {key} from {value['tokenUri']}. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error downloading metadata {key} from {value['tokenUri']}: {e}")
        else:
            print(f"None exits valid metadata for {file_path.name}.")


# 基于Alchemy V3 API的NFT下载器类
class NFT_Downloader_for_Whole_Collection_Alchemy(NFT_Downloader_for_Whole_Collection):
    """
    基于Alchemy V3 API的NFT下载器类，完整下载一整个NFT项目
    细节参考链接：https://docs.alchemy.com/reference/getnftsforcontract-v3

    """

    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num = 1,
                thread_num = 1,
                total_supply = 10000,
                start_index = 0,
                interval_length = 3):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply, start_index, interval_length)
        # 生成下载资源payload list
        self.generate_payload(candidate_format = candidate_format,
                            start_index = start_index,
                            total_supply = total_supply)

    def generate_payload(self, *args, **kwargs):
        """
        生成下载资源payload list

        Args:
            *args: 可变参数
            **kwargs: 关键字参数

        """
        # 实例化PayloadFactory
        payloadfactory = PayloadFactory(candidate_format = self.candidate_format,
                                        start = self.start_index,
                                        interval_length = self.interval_length,
                                        total_supply = self.total_supply)

        self.payload_list = payloadfactory.create_interval_tuples_with_start_len()

    # 下载全部的media和metadata资源
    def download_media_and_metadata(self):

        # 创建保存图片和metadata的文件夹
        img_path = self.save_path.joinpath(f"{self.NFT_name}/img")
        metadata_path = self.save_path.joinpath(f"{self.NFT_name}/metadata")
        fio.check_dir(img_path)
        fio.check_dir(metadata_path)

        print(f"\n**********  ## {self.NFT_name} ## Start downloading... **********\n")
        # 启用进程池多进程下载
        try:
            with mp.Pool(processes = self.process_num) as pool:
                pool.map(self.single_process_worker, self.payload_list)
            pool.close()
            pool.join()
        except Exception as e:
            print(f"\nError downloading: {self.NFT_name} Process startup failed: {e}\n")
            return False

        print(f"\n**********  ## {self.NFT_name}## Download successfully! **********\n")
        return True

    # 定义单个下载进程的方法
    def single_process_worker(self, payload):
        # 1. 获取请求参数
        start, interval_length = payload

        time.sleep(random.randint(1, 3))  # 增加请求间隔
        try:
            # 发送请求
            # 随机选择一个api
            api = stb.get_api("Alchemy")

            url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{api}/getNFTsForContract?contractAddress={self.contract_address}&withMetadata=true&startToken={start}&limit={interval_length}"
            headers = stb.get_headers()
            response = requests.get(url, headers=headers)
        except Exception as e:
            print(f" {self.NFT_name} Error encountered: {e}")
        else:
            # 4. 解析数据
            if response.status_code == 200:
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata_source = response_data["metadata_source"]
                media_source = response_data["media_source"]
                self.metadata_downloader(metadata_source = metadata_source)
                self.media_downloader(media_source = media_source)

            else:
                print(f"{self.NFT_name} Error: {response.status_code}")

    def parse_response(self, response):
        """
        从响应中解析数据。

        Args:
            response (Http response): HTTP响应数据

        Returns:
            dict: 返回解析后的数据，包括metadata资源和media资源
        """
        metadata_dict = {}
        metadata_source = {}
        media_source = {}

        NFT_list = response.json()["nfts"]
        for NFT_item in NFT_list:
            try:
                tokenId = NFT_item.get("tokenId")

                # 解析metadata资源
                """
                {
                    "tokenId_1": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    "tokenId_2": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    ……
                }
                
                
                """
                metadata_source[tokenId] = {
                    "raw" : NFT_item["raw"].get("metadata", None),
                    "tokenUri" : NFT_item.get("tokenUri", None)
                    }

                # 解析media资源
                if NFT_item.get("image", None):
                    image = NFT_item.get("image")
                else:
                    # 如果没有image字段，跳过这个NFT
                    continue

                # 将媒体资源统一成一种通用的表达方式
                """
                {
                    "tokenId_1": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                    "tokenId_2": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                ……

                }
                

                """
                source_list = []
                for source_item in ["cachedUrl", "pngUrl", "originalUrl", "thumbnailUrl"]:
                    # 如果字段不为空，添加到source_list中
                    link = image.get(source_item, None)
                    if link:
                        source_list.append(link)
                
                # 解析文件格式
                temp_format = image.get("contentType", None)
                media_format = parse_file_format(temp_format, self.candidate_format)


                media_source[tokenId] = {"source_list": source_list,
                                        "format": media_format}

            except Exception as e:
                # 抛出异常，跳过这个NFT
                print(f"Response parsing exception: {e}. Skipping")
                continue

        metadata_dict["metadata_source"] = metadata_source
        metadata_dict["media_source"] = media_source
        return metadata_dict


# 基于MFTScan API的NFT下载器类
class NFT_Downloader_for_Whole_Collection_NFTScan(NFT_Downloader_for_Whole_Collection):
    """
    基于NFTScan API的NFT下载器类，完整下载一整个NFT项目
    细节参考链接：https://docs.nftscan.com/reference/evm/get-nfts-by-contract

    """
    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num = 1,
                thread_num = 3,
                total_supply = 10000,
                start_index = 0,
                interval_length = 3):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply, start_index, interval_length)

        # 设置请求参数模板
        self.params_template = {
                                'show_attribute': 'true',
                                'sort_field': '',
                                'sort_direction': '',
                                'limit': str(interval_length),
                            }

    def download_media_and_metadata(self):
                # 创建保存图片和metadata的文件夹
        img_path = self.save_path.joinpath(f"{self.NFT_name}/img")
        metadata_path = self.save_path.joinpath(f"{self.NFT_name}/metadata")
        fio.check_dir(img_path)
        fio.check_dir(metadata_path)
        if self.chain_type == "ethereum":
            url = f"https://restapi.nftscan.com/api/v2/assets/{self.contract_address}"
        else:
            url = f"https://{self.chain_type}api.nftscan.com/api/v2/assets/{self.contract_address}"
        
        headers = stb.get_headers()
        headers.update({"X-API-KEY": stb.get_api("NFTScan")})
        print(f"\n**********  ## {self.NFT_name} ## Start downloading... **********\n")

        response = requests.get(url, headers=headers, params=self.params_template)
        # 循环下载，停止的标志是游标不为空
        """
        Python 3.8 中引入的赋值表达式，通常被称为“海象运算符”（:=）。
        这种表达式允许你在表达式内部进行变量赋值，并且可以直接在条件表达式中使用新赋值的变量。
        代码中，next_cursor := response.json()["data"].get("next")
        在 while 循环的条件判断中直接赋值并判断 next_cursor 是否为非空。
        """
        try:
            while(next_cursor := response.json()["data"].get("next")):
                # 解析数据
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata_source = response_data["metadata_source"]
                media_source = response_data["media_source"]
                self.metadata_downloader(metadata_source = metadata_source)
                self.media_downloader(media_source = media_source)

                # 更新游标
                self.params_template.update({"cursor": next_cursor})
                response = requests.get(url, headers=headers, params=self.params_template)

            print(f"\n**********  ## {self.NFT_name} ## Download successfully! **********\n")
            return True

        except Exception as e:
            print(f"Error downloading: {self.NFT_name} Process startup failed: {e}\n")
            return False


    def parse_response(self, response):
        """
        从响应中解析数据。

        Args:
            response (Http response): HTTP响应数据

        Returns:
            dict: 返回解析后的数据，包括metadata资源和media资源
        """
        metadata_dict = {}
        metadata_source = {}
        media_source = {}

        NFT_list = response.json()["data"].get("content", [])
        for NFT_item in NFT_list:
            try:
                tokenId = NFT_item.get("token_id")

                # 解析metadata资源
                """
                {
                    "tokenId_1": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    "tokenId_2": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    ……
                }
                
                
                """
                metadata_source[tokenId] = {
                    "raw" : NFT_item.get("metadata_json", None),
                    "tokenUri" : NFT_item.get("token_uri", None)
                    }

                # 解析media资源
                # 将媒体资源统一成一种通用的表达方式
                """
                {
                    "tokenId_1": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                    "tokenId_2": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                ……

                }
                

                """
                source_list = []
                source_list.append(NFT_item.get("content_uri", None))
                source_list.append(NFT_item.get("image_uri", None))
                source_list.append(NFT_item.get("nftscan_uri", None))
                source_list.append(NFT_item.get("small_nftscan_uri", None))

                # 解析文件格式
                temp_format = NFT_item.get("content_type", None)
                media_format = parse_file_format(temp_format, self.candidate_format)
                media_source[tokenId] = {"source_list": source_list,
                                        "format": media_format}

            except Exception as e:
                # 抛出异常，跳过这个NFT
                print(f"Response parsing exception: {e}. Skipping")
                continue

        metadata_dict["metadata_source"] = metadata_source
        metadata_dict["media_source"] = media_source
        return metadata_dict


class NFT_Downloader_for_Whole_Collection_NFTGo(NFT_Downloader_for_Whole_Collection):
    """
    基于NFTGo API的NFT下载器类，完整下载一整个NFT项目
    详细细节参考：https://docs.nftgo.io/v2.0/reference/get_nfts_by_contract__chain__v1_collection__contract_address__nfts_get
    """

    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num = 1,
                thread_num = 3,
                total_supply = 10000,
                start_index = 0,
                interval_length = 3):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply, start_index, interval_length)

        # 设置请求参数模板
        self.url_template = f"https://data-api.nftgo.io/{chain_type}/v1/collection/{contract_address}/nfts?limit={interval_length}"

    def download_media_and_metadata(self):
        # 创建保存图片和metadata的文件夹
        img_path = self.save_path.joinpath(f"{self.NFT_name}/img")
        metadata_path = self.save_path.joinpath(f"{self.NFT_name}/metadata")
        fio.check_dir(img_path)
        fio.check_dir(metadata_path)

        headers = stb.get_headers()
        headers.update({"X-API-KEY": stb.get_api("NFTGo")})
        print(f"\n**********  ## {self.NFT_name} ## Start downloading... **********\n")

        response = requests.get(self.url_template, headers=headers)
        # 因为openSea的响应数据中不存在文件格式，为了保证opensea数据格式的一致性，需要做文件格式的更新
        demo_img_url = response.json()["nfts"][0].get("image", None)
        if demo_img_url:
            fmt = stb.get_media_format(demo_img_url)
            if fmt:
                self.candidate_format = fmt
        try:
            while(next_cursor := response.json().get("next_cursor")):
                # 解析数据
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata_source = response_data["metadata_source"]
                media_source = response_data["media_source"]
                self.metadata_downloader(metadata_source = metadata_source)
                self.media_downloader(media_source = media_source)

                # 更新游标
                # 在链接模版的“nfts?后面插入cursor参数
                url = re.sub(r"(nfts\?)", r"\1cursor={}&".format(next_cursor), self.url_template)
                response = requests.get(url, headers = headers)

            print(f"\n**********  ## {self.NFT_name} ## Download successfully! **********\n")
            return True

        except Exception as e:
            print(f"Error downloading: {self.NFT_name} Process startup failed: {e}\n")
            return False


    def parse_response(self, response):
        """
        从响应中解析数据。

        Args:
            response (Http response): HTTP响应数据

        Returns:
            dict: 返回解析后的数据，包括metadata资源和media资源
        """
        metadata_dict = {}
        metadata_source = {}
        media_source = {}

        NFT_list = response.json().get("nfts", [])
        for NFT_item in NFT_list:
            # 转换成字典
            try:
                tokenId = NFT_item.get("token_id")

                # 解析metadata资源
                """
                {
                    "tokenId_1": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    "tokenId_2": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    ……
                }
                
                
                """
                # 构造一个人造的metadata资源

                """
                一点学习心得：

                    a = None
                    if b := a:
                        print(b)

                    print(b)
                
                    变量 b 的作用域：在使用赋值表达式时，变量 b 被定义在赋值表达式所在的块级作用域之外。
                    在这种情况下，b 被定义在 if 语句的外部，使得它在 if 块之外也是可见的。
                
                """

                if attributes := NFT_item.get("traits", None):
                        attributes = {"attributes": attributes}
                metadata_source[tokenId] = {
                    "raw" : attributes,
                    "tokenUri" : NFT_item.get("metadata_url", None)
                    }

                # 解析media资源
                # 将媒体资源统一成一种通用的表达方式
                """
                {
                    "tokenId_1": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                    "tokenId_2": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                ……

                }
                

                """
                source_list = [NFT_item.get("image", None)]
                # 解析文件格式
                temp_format = NFT_item.get("content_type", None)
                media_format = parse_file_format(temp_format, self.candidate_format)
                media_source[tokenId] = {"source_list": source_list,
                                        "format": media_format}

            except Exception as e:
                # 抛出异常，跳过这个NFT
                print(f"Response parsing exception: {e}. Skipping")
                continue

        metadata_dict["metadata_source"] = metadata_source
        metadata_dict["media_source"] = media_source
        return metadata_dict


class NFT_Downloader_for_Whole_Collection_OpenSea(NFT_Downloader_for_Whole_Collection):

    """
    基于OpenSea API的NFT下载器类，完整下载一整个NFT项目
    详细细节参考：https://docs.opensea.io/reference/list_nfts_by_contract
    """
    def __init__(self,
                chain_type: str,
                NFT_name: str,
                contract_address: str,
                candidate_format: str,
                save_path: str,
                process_num = 1,
                thread_num = 3,
                total_supply = 10000,
                start_index = 0,
                interval_length = 3):

        super().__init__(chain_type, NFT_name, contract_address, candidate_format, save_path, process_num, thread_num, total_supply, start_index, interval_length)

        # 设置请求参数模板
        self.url_template = f"https://api.opensea.io/api/v2/chain/{self.chain_type}/contract/{contract_address}/nfts?limit={interval_length}"

    def download_media_and_metadata(self):
        # 创建保存图片和metadata的文件夹
        img_path = self.save_path.joinpath(f"{self.NFT_name}/img")
        metadata_path = self.save_path.joinpath(f"{self.NFT_name}/metadata")
        fio.check_dir(img_path)
        fio.check_dir(metadata_path)

        headers = stb.get_headers()
        headers.update({"x-api-key": stb.get_api("OpenSea")})
        print(f"\n**********  ## {self.NFT_name} ## Start downloading... **********\n")

        response = requests.get(self.url_template, headers=headers)
        # 因为openSea的响应数据中不存在文件格式，为了保证opensea数据格式的一致性，需要做文件格式的更新
        demo_img_url = response.json()["nfts"][0].get("image_url", None)
        if demo_img_url:
            fmt = stb.get_media_format(demo_img_url)
            if fmt:
                self.candidate_format = fmt
        try:
            while(next_cursor := response.json().get("next")):
                # 解析数据
                response_data = self.parse_response(response)
                # 启动多进程同时进行两个任务
                metadata_source = response_data["metadata_source"]
                media_source = response_data["media_source"]
                self.metadata_downloader(metadata_source = metadata_source)
                self.media_downloader(media_source = media_source)

                # 更新游标
                # 将 Base64 编码的字符串转换为 URL 编码的字符串
                next_cursor = urllib.parse.quote(next_cursor)
                url = self.url_template + f"&next={next_cursor}"
                response = requests.get(url, headers = headers)

            print(f"\n**********  ## {self.NFT_name} ## Download successfully! **********\n")
            return True

        except Exception as e:
            print(f"Error downloading: {self.NFT_name} Process startup failed: {e}\n")
            return False


    def parse_response(self, response):
        """
        从响应中解析数据。

        Args:
            response (Http response): HTTP响应数据

        Returns:
            dict: 返回解析后的数据，包括metadata资源和media资源
        """
        metadata_dict = {}
        metadata_source = {}
        media_source = {}

        NFT_list = response.json().get("nfts", [])
        for NFT_item in NFT_list:
            # 转换成字典
            try:
                tokenId = NFT_item.get("identifier")

                # 解析metadata资源
                """
                {
                    "tokenId_1": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    "tokenId_2": {
                        "raw": metadata,
                        "tokenUri": tokenUri
                    },
                    ……
                }
                
                
                """
                metadata_source[tokenId] = {
                    "raw" : NFT_item.get("metadata", None),
                    "tokenUri" : NFT_item.get("metadata_url", None)
                    }

                # 解析media资源
                # 将媒体资源统一成一种通用的表达方式
                """
                {
                    "tokenId_1": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                    "tokenId_2": {
                        "source_list": [url1, url2, url3, ...],
                        "format": ".png"
                },
                ……

                }
                

                """
                source_list = []
                source_list.append(NFT_item.get("image_url", None))
                source_list.append(NFT_item.get("display_image_url", None))

                # 解析文件格式
                temp_format = NFT_item.get("content_type", None)
                media_format = parse_file_format(temp_format, self.candidate_format)
                media_source[tokenId] = {"source_list": source_list,
                                        "format": media_format}

            except Exception as e:
                # 抛出异常，跳过这个NFT
                print(f"Response parsing exception: {e}. Skipping")
                continue

        metadata_dict["metadata_source"] = metadata_source
        metadata_dict["media_source"] = media_source
        return metadata_dict



# 解析文件格式
def parse_file_format(temp_format: str, candidate_format) -> str:
    """
    解析文件格式

    Args:
        temp_format (str): 临时文件格式
        candidate_format (str): 候选文件格式

    Returns:
        str: 返回解析后的文件格式
    """
    if temp_format == None or temp_format == 'unknown':
        media_format = candidate_format
    
    # 如果文件类型中出现svg+xml，将其转换为.svg
    elif "svg+xml" in temp_format:
        media_format = ".svg"
    else:
        media_format = f".{temp_format.split('/')[-1]}"
    return media_format


def is_ipfs_cid(uri: str):
    """
    判断一个字符串是否是 IPFS 的 CID。如果是则返回 CID，否则返回 False
    
    :param uri: 待验证的字符串
    :return: 如果字符串是有效的 IPFS CID 返回 CID, 否则返回 False
    """
    CID = False

    # 如果资源链接里包含 "ipfs" 字符串，则提取 CID
    # 示例: https://ipfs.io/ipfs/QmVBAfZia18g1WaHKZVmA14hQQFhANa82WBqbv43WhXUGZ/888.png
    # 示例: ipfs://QmcJYkCKK7QPmYWjp4FD2e3Lv5WCGFuHNUByvGKBaytif4
    if "ipfs" in uri:
        # 提取 CID
        if uri.startswith("ipfs://"):
            CID = uri.split("ipfs://")[1]
        else:
            CID = uri.split("ipfs/")[1]
    else:
        # CID v0 的格式是一个 base58 编码的 SHA-256 hash, 长度是 46 个字符, 以 "Qm" 开头
        cid_v0_pattern = re.compile(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$')
        
        # CID v1 是 base32 编码，前缀是 'b'，通常是 59 个字符
        cid_v1_pattern = re.compile(r'^b[2-7a-z]{58}$')
        
        # CID v1 也可能是 base58 编码，前缀可以是 'z'，'Z'，'m'，'M' 等等，具体长度和前缀依赖于编码
        # 简单的匹配 base58 编码，通常 CID v1 base58 编码的长度在 32 到 59 之间
        cid_v1_base58_pattern = re.compile(r'^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{32,59}$')
    
        # 判断是否是有效的 CID
        if bool(cid_v0_pattern.match(uri) or cid_v1_pattern.match(uri) or cid_v1_base58_pattern.match(uri)):
            CID = uri
    
    return CID

def download_from_IPFS(CID, file_path):

    IPFS_gateways = stb.get_api("IPFS_gateways")
    # 使用IDM下载器下载图片
    # 将CID拼接到IPFS网关上，依次尝试下载，直到成功
    for gateway in IPFS_gateways:
        try:
            url = f"{gateway}{CID}"
            print(f"Downloading from IPFS: {url}")
            downloader = Downloader()
            downloader.download(url=url, path=file_path)
            print(f"{file_path.name} downloaded successfully.")
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    print(f"Failed to download {CID} after trying all URLs.")
    return False


def download_NFT_collection_from_IPFS(metadata_path, img_path, delimiter="/"):
    """
    下载整个 collection 中的所有图片
    
    Args: 
        metadata_path (str): metadata文件夹路径
        img_path (str): 图片文件夹路径
        delimiter (str, optional): 分隔符. Defaults to "/".
    
    Returns:
        None:

    """
    with ipfshttpclient.connect() as client:
        file_list = os.listdir(metadata_path)
        for file in tqdm(file_list, desc="Downloading images", unit="file", ncols=150, leave=False):
            file_path = os.path.join(metadata_path, file)
            metadata = fio.load_json(file_path)
            image_cid = metadata["image"].split(delimiter)[-1]
            image = client.cat(image_cid)
            img_name = file.split(".")[0] + ".png"
            with open(os.path.join(img_path, img_name), "wb") as f:
                f.write(image)
