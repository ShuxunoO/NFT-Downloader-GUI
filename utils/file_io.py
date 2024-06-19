import json
import os
from pathlib import Path


def check_dir(dir_path):
    """
    检查文件夹路径是否存在，不存在则创建

    Args:
        dir_path (Path obj): 待检查的文件夹路径
    """
    if not Path(dir_path).exists():
        Path(dir_path).mkdir(parents=True, exist_ok=True)



def save_json(file_path, data):
    """
    Saves the data to a file with the given filename in the given path

    Args:
        :param file_path: The path to the file where you want to save the data
        :param data: The data to be saved

    """
    # 如果data是字符串，转换为字典
    if isinstance(data, str):
        data = json.loads(data)
    with open(file_path, 'w', encoding='UTF-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4, separators=(',', ': '))


def load_json(json_path):
    """
    以只读的方式打开json文件

    Args:
        config_path: json文件路径

    Returns:
        A dictionary

    """
    try:

        with open(json_path, 'r', encoding='UTF-8') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading json file: {}".format(json_path))
        print(e)
        return None
    


def append_dict_to_json_file(file_path, new_data):
    """
    将一个字典以追加方式写入 JSON 文件。

    :param file_path: str, JSON 文件路径
    :param new_data: dict, 要追加的字典
    """
    if not isinstance(new_data, dict):
        print("无法追加数据。JSON 文件顶级对象不是字典。")
        return
    # 如果文件不存在，则创建一个空文件
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(new_data, json_file, ensure_ascii=False, indent=4)
            print("更新成功！")
            json_file.truncate()
            return

    try:
        with open(file_path, 'r+', encoding='utf-8') as json_file:
            data = json.load(json_file)
            data.update(new_data)
            print(f"{new_data.keys()}更新成功！")
            json_file.seek(0)
            json.dump(data, json_file, ensure_ascii=False, indent=4)
            json_file.truncate()
    except FileNotFoundError:
        print("文件未找到。请确保文件路径正确。")
    except json.JSONDecodeError as e:
        print(f"解析 JSON 文件时出错：{e}")


def save_txt(save_path, data):
    """
    保存字符串到txt文件

    Args:
        save_path (str): 保存路径
        data (str): 字符串
    """
    with open(save_path, 'w', encoding='UTF-8') as file:
        file.write(data)