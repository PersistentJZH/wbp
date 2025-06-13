# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import copy
import csv
import os
from datetime import datetime
import concurrent.futures
import requests
from urllib.parse import urlparse

import scrapy
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.project import get_project_settings

settings = get_project_settings()

def download_image(pic_url, image_path, headers):
    try:
        response = requests.get(pic_url, headers=headers)
        if response.status_code == 200:
            with open(image_path, 'wb') as f:
                f.write(response.content)
            return True, image_path
        return False, f"下载图片失败: {pic_url}, 状态码: {response.status_code}"
    except Exception as e:
        return False, f"下载图片失败: {pic_url}, 错误: {str(e)}"

class CsvPipeline(object):
    def __init__(self):
        self.ids_seen = set()
        self.processed_ids_file = 'processed_ids.txt'
        self.file_path = 'results' + os.sep + 'all_results.csv'
        # 从文件加载已处理的ID
        if os.path.exists(self.processed_ids_file):
            with open(self.processed_ids_file, 'r', encoding='utf-8') as f:
                self.ids_seen = set(line.strip() for line in f)
        # 检查结果文件夹
        base_dir = 'results'
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
        # 检查是否需要写表头
        self.is_first_write = not os.path.isfile(self.file_path)
        # 创建图片保存目录
        self.images_dir = os.path.join('results', 'images')
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        # 设置下载线程数
        self.max_workers = 10
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://weibo.com/'
        }

    def wrap_image_url(self, original_url):
        """将原始微博图片链接包装成百度外链格式以绕过防盗链"""
        return f"https://image.baidu.com/search/down?url={original_url}"

    def process_item(self, item, spider):
        # 检查是否已经存在相同的微博ID
        if item['weibo']['id'] in self.ids_seen:
            raise DropItem("过滤重复微博: %s" % item)

        # 将新ID添加到集合和文件中
        self.ids_seen.add(item['weibo']['id'])
        with open(self.processed_ids_file, 'a', encoding='utf-8') as f:
            f.write(f"{item['weibo']['id']}\n")

        # 处理图片链接
        pics = item['weibo'].get('pics', [])
        wrapped_pics = [self.wrap_image_url(pic) for pic in pics]

        # 先写入CSV
        with open(self.file_path, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if self.is_first_write:
                header = [
                    'id', 'bid', 'user_id', '用户昵称', '微博正文', '头条文章url',
                    '发布位置', '艾特用户', '话题', '转发数', '评论数', '点赞数', '发布时间',
                    '发布工具', '微博图片url', '微博视频url', 'retweet_id', 'ip', 'user_authentication',
                    '会员类型', '会员等级', '关键词', 'Process', '写入时间'
                ]
                writer.writerow(header)
                self.is_first_write = False

            writer.writerow([
                item['weibo'].get('id', ''),
                item['weibo'].get('bid', ''),
                item['weibo'].get('user_id', ''),
                item['weibo'].get('screen_name', ''),
                item['weibo'].get('text', ''),
                item['weibo'].get('article_url', ''),
                item['weibo'].get('location', ''),
                item['weibo'].get('at_users', ''),
                item['weibo'].get('topics', ''),
                item['weibo'].get('reposts_count', ''),
                item['weibo'].get('comments_count', ''),
                item['weibo'].get('attitudes_count', ''),
                item['weibo'].get('created_at', ''),
                item['weibo'].get('source', ''),
                ','.join(wrapped_pics),  # 使用处理后的图片链接
                item['weibo'].get('video_url', ''),
                item['weibo'].get('retweet_id', ''),
                item['weibo'].get('ip', ''),
                item['weibo'].get('user_authentication', ''),
                item['weibo'].get('vip_type', ''),
                item['weibo'].get('vip_level', 0),
                item.get('keyword', ''),
                False,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 写入时间
            ])

        # 再下载图片
        if wrapped_pics:
            # 准备下载任务
            download_tasks = []
            for pic_url in wrapped_pics:
                image_name = f"{item['weibo']['id']}_{pic_url.split('/')[-1]}"
                image_path = os.path.join(self.images_dir, image_name)
                download_tasks.append((pic_url, image_path))

            # 使用线程池下载图片
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有下载任务
                future_to_url = {
                    executor.submit(download_image, url, path, self.headers): url 
                    for url, path in download_tasks
                }
                
                # 处理下载结果
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        success, result = future.result()
                        if success:
                            print(f"成功下载图片: {result}")
                        else:
                            print(result)
                    except Exception as e:
                        print(f"下载图片时发生异常: {url}, 错误: {str(e)}")

        return item

class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['weibo']['id'] in self.ids_seen:
            raise DropItem("过滤重复微博: %s" % item)
        else:
            self.ids_seen.add(item['weibo']['id'])
            return item
