# -*- coding: utf-8 -*-

import requests
import json
import csv
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import random
from weibo.utils.util import convert_weibo_type, convert_contain_type
from parsel import Selector
import re
from urllib.parse import unquote
import weibo.utils.util as util

class WeiboCrawler:
    def __init__(self, weibo_type='', contain_type=''):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
            'cookie': 'SCF=AglNHFR3KN0mFYkn3ObKAtXKW4WsGREYWLO2FhbZiMdog340aAC2svceQoEb1HPVZQTgSFAAbeQDzpb80ZI2PW8.; SUB=_2A25FQ5hADeRhGeFH41oW9y7Ezj-IHXVmIJWIrDV6PUJbktAbLVnDkW1NejGpZl56LBnvDGplIqgptPGVsXSp7neg; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFMNFdjmN4xPB-4LwUuZYN45NHD95QN1KnRS0M71h-0Ws4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0.R1hMNehnfe7tt; SSOLoginState=1749542928; ALF=1752134928; _T_WM=4a33f5cf83d511995b965b7067889d87',
        }
        self.base_url = 'https://s.weibo.com/weibo'
        self.processed_ids = set()
        self.processed_ids_file = 'processed_ids.txt'
        self.load_processed_ids()
        self.weibo_type = weibo_type
        self.contain_type = contain_type

    def load_processed_ids(self):
        """加载已处理的微博ID"""
        if os.path.exists(self.processed_ids_file):
            with open(self.processed_ids_file, 'r', encoding='utf-8') as f:
                self.processed_ids = set(line.strip() for line in f)

    def save_processed_id(self, weibo_id):
        """保存已处理的微博ID"""
        self.processed_ids.add(weibo_id)
        with open(self.processed_ids_file, 'a', encoding='utf-8') as f:
            f.write("{}\n".format(weibo_id))

    def wrap_image_url(self, original_url):
        """将原始微博图片链接包装成百度外链格式"""
        return "https://image.baidu.com/search/down?url={}".format(original_url)

    def get_weibo_info(self, bid):
        """获取微博详细信息"""
        url = "https://weibo.com/ajax/statuses/show?id={}&locale=zh-CN".format(bid)
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("region_name", "").split()[-1] if data.get("region_name") else ""
        except:
            pass
        return ""

    def get_article_url(self, selector):
        article_url = ''
        text = selector.xpath('string(.)').get('').replace('\u200b', '').replace('\ue627', '').replace('\n', '').replace(' ', '')
        if text.startswith('发布了头条文章'):
            urls = selector.xpath('.//a')
            for url in urls:
                if url.xpath('i[@class="wbicon"]/text()').get('') == 'O':
                    href = url.xpath('@href').get('')
                    if href and href.startswith('http://t.cn'):
                        article_url = href
                    break
        return article_url

    def get_location(self, selector):
        a_list = selector.xpath('.//a')
        location = ''
        for a in a_list:
            if a.xpath('./i[@class="wbicon"]') and a.xpath('./i[@class="wbicon"]/text()').get('') == '2':
                location = a.xpath('string(.)').get('')[1:]
                break
        return location

    def get_at_users(self, selector):
        a_list = selector.xpath('.//a')
        at_list = []
        for a in a_list:
            href = a.xpath('@href').get('')
            text = a.xpath('string(.)').get('')
            if len(unquote(href)) > 14 and len(text) > 1:
                if unquote(href)[14:] == text[1:]:
                    at_user = text[1:]
                    if at_user not in at_list:
                        at_list.append(at_user)
        return ','.join(at_list) if at_list else ''

    def get_topics(self, selector):
        a_list = selector.xpath('.//a')
        topic_list = []
        for a in a_list:
            text = a.xpath('string(.)').get('')
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                if text[1:-1] not in topic_list:
                    topic_list.append(text[1:-1])
        return ','.join(topic_list) if topic_list else ''

    def get_vip(self, selector):
        vip_type = "非会员"
        vip_level = 0
        vip_container = selector.xpath('.//div[@class="user_vip_icon_container"]')
        if vip_container:
            svvip_img = vip_container.xpath('.//img[contains(@src, "svvip_")]')
            if svvip_img:
                vip_type = "超级会员"
                src = svvip_img.xpath('@src').get('')
                level_match = re.search(r'svvip_(\d+)\.png', src)
                if level_match:
                    vip_level = int(level_match.group(1))
            else:
                vip_img = vip_container.xpath('.//img[contains(@src, "vip_")]')
                if vip_img:
                    vip_type = "会员"
                    src = vip_img.xpath('@src').get('')
                    level_match = re.search(r'vip_(\d+)\.png', src)
                    if level_match:
                        vip_level = int(level_match.group(1))
        return vip_type, vip_level

    def parse_weibo(self, html, keyword):
        selector = Selector(text=html)
        weibo_list = []
        for sel in selector.xpath("//div[@class='card-wrap']"):
            info = sel.xpath("div[@class='card']/div[@class='card-feed']/div[@class='content']/div[@class='info']")
            if info:
                weibo = {}
                weibo['id'] = sel.xpath('@mid').get('')
                bid = sel.xpath('.//div[@class="from"]/a[1]/@href').get('').split('/')[-1].split('?')[0]
                weibo['bid'] = bid
                weibo['user_id'] = info[0].xpath('div[2]/a/@href').get('').split('?')[0].split('/')[-1]
                weibo['screen_name'] = info[0].xpath('div[2]/a/@nick-name').get('')
                weibo['vip_type'], weibo['vip_level'] = self.get_vip(info[0])
                txt_sel = sel.xpath('.//p[@class="txt"]')[0]
                retweet_sel = sel.xpath('.//div[@class="card-comment"]')
                retweet_txt_sel = ''
                if retweet_sel and retweet_sel[0].xpath('.//p[@class="txt"]'):
                    retweet_txt_sel = retweet_sel[0].xpath('.//p[@class="txt"]')[0]
                content_full = sel.xpath('.//p[@node-type="feed_list_content_full"]')
                is_long_weibo = False
                is_long_retweet = False
                if content_full:
                    if not retweet_sel:
                        txt_sel = content_full[0]
                        is_long_weibo = True
                    elif len(content_full) == 2:
                        txt_sel = content_full[0]
                        retweet_txt_sel = content_full[1]
                        is_long_weibo = True
                        is_long_retweet = True
                    elif retweet_sel[0].xpath('.//p[@node-type="feed_list_content_full"]'):
                        retweet_txt_sel = retweet_sel[0].xpath('.//p[@node-type="feed_list_content_full"]')[0]
                        is_long_retweet = True
                    else:
                        txt_sel = content_full[0]
                        is_long_weibo = True
                weibo['text'] = txt_sel.xpath('string(.)').get('').replace('\u200b', '').replace('\ue627', '')
                weibo['article_url'] = self.get_article_url(txt_sel)
                weibo['location'] = self.get_location(txt_sel)
                if weibo['location']:
                    weibo['text'] = weibo['text'].replace('2' + weibo['location'], '')
                weibo['text'] = weibo['text'][2:].replace(' ', '')
                if is_long_weibo:
                    weibo['text'] = weibo['text'][:-4]
                weibo['at_users'] = self.get_at_users(txt_sel)
                weibo['topics'] = self.get_topics(txt_sel)
                reposts_count = sel.xpath('.//a[@action-type="feed_list_forward"]/text()').getall()
                reposts_count = "".join(reposts_count)
                try:
                    reposts_count = re.findall(r'\d+.*', reposts_count)
                except TypeError:
                    reposts_count = []
                weibo['reposts_count'] = reposts_count[0] if reposts_count else '0'
                comments_count = sel.xpath('.//a[@action-type="feed_list_comment"]/text()').get('')
                comments_count = re.findall(r'\d+.*', comments_count)
                weibo['comments_count'] = comments_count[0] if comments_count else '0'
                attitudes_count = sel.xpath('.//a[@action-type="feed_list_like"]/button/span[2]/text()').get('')
                attitudes_count = re.findall(r'\d+.*', attitudes_count)
                weibo['attitudes_count'] = attitudes_count[0] if attitudes_count else '0'
                created_at = sel.xpath('.//div[@class="from"]/a[1]/text()').get('').replace(' ', '').replace('\n', '').split('前')[0]
                weibo['created_at'] = util.standardize_date(created_at)
                source = sel.xpath('.//div[@class="from"]/a[2]/text()').get('')
                weibo['source'] = source if source else ''
                pics = ''
                is_exist_pic = sel.xpath('.//div[@class="media media-piclist"]')
                if is_exist_pic:
                    pics = is_exist_pic[0].xpath('ul[1]/li/img/@src').getall()
                    pics = [pic[8:] for pic in pics]
                    pics = [re.sub(r'/.*?/', '/large/', pic, 1) for pic in pics]
                    pics = ['https://' + pic for pic in pics]
                video_url = ''
                is_exist_video = sel.xpath('.//div[@class="thumbnail"]//video-player').get('')
                if is_exist_video:
                    video_url = re.findall(r"src:'(.*?)'", is_exist_video)
                    if video_url:
                        video_url = video_url[0].replace('&amp;', '&')
                        video_url = 'http:' + video_url
                    else:
                        video_url = ''
                if not retweet_sel:
                    weibo['pics'] = pics
                    weibo['video_url'] = video_url
                else:
                    weibo['pics'] = ''
                    weibo['video_url'] = ''
                weibo['retweet_id'] = ''
                weibo['ip'] = self.get_weibo_info(bid)
                avator = sel.xpath("div[@class='card']/div[@class='card-feed']/div[@class='avator']")
                if avator:
                    user_auth = avator.xpath('.//svg/@id').get('')
                    if user_auth == 'woo_svg_vblue':
                        weibo['user_authentication'] = '蓝V'
                    elif user_auth == 'woo_svg_vyellow':
                        weibo['user_authentication'] = '黄V'
                    elif user_auth == 'woo_svg_vorange':
                        weibo['user_authentication'] = '红V'
                    elif user_auth == 'woo_svg_vgold':
                        weibo['user_authentication'] = '金V'
                    else:
                        weibo['user_authentication'] = '普通用户'
                else:
                    weibo['user_authentication'] = '普通用户'
                weibo_list.append({'weibo': weibo, 'keyword': keyword})
        return weibo_list

    def save_to_csv(self, weibo_list, keyword):
        """保存微博数据到CSV文件"""
        if not weibo_list:
            return

        base_dir = '结果文件' + os.sep + keyword
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)

        file_path = base_dir + os.sep + keyword + '.csv'
        is_first_write = not os.path.exists(file_path)

        with open(file_path, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if is_first_write:
                header = [
                    'id', 'bid', 'user_id', '用户昵称', '微博正文', '转发数', 
                    '评论数', '点赞数', '发布时间', '微博图片url', '微博视频url', 'ip'
                ]
                writer.writerow(header)

            for weibo in weibo_list:
                writer.writerow([
                    weibo['weibo']['id'],
                    weibo['weibo']['bid'],
                    weibo['weibo']['user_id'],
                    weibo['weibo']['screen_name'],
                    weibo['weibo']['text'],
                    weibo['weibo']['reposts_count'],
                    weibo['weibo']['comments_count'],
                    weibo['weibo']['attitudes_count'],
                    weibo['weibo']['created_at'],
                    ','.join(weibo['weibo']['pics']),
                    weibo['weibo']['video_url'],
                    weibo['weibo']['ip']
                ])

    def crawl(self, keyword, start_date=None, end_date=None):
        """爬取指定关键词的微博，支持自动翻页，并打印详细debug信息"""
        if not start_date:
            start_date = (datetime.now() - timedelta(minutes=30)).strftime('%Y-%m-%d-%H')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d-%H')

        page = 1
        total_weibo_list = []
        while True:
            params = {
                'q': keyword,
                'timescope': 'custom:{}:{}'.format(start_date, end_date),
                'Refer': 'weibo_search'
            }
            url = self.base_url + self.weibo_type + self.contain_type + f'&page={page}'
            # Debug: 打印请求参数和完整url
            print(f"\n[DEBUG] 请求第{page}页:")
            print(f"[DEBUG] url: {url}")
            print(f"[DEBUG] params: {params}")
            try:
                response = requests.get(url, params=params, headers=self.headers)
                print(f"[DEBUG] response.url: {response.url}")
                print(f"[DEBUG] response.status_code: {response.status_code}")
                print(f"[DEBUG] response.text前500: {response.text[:500]}")
                if response.status_code == 200:
                    # 检查是否被反爬
                    if ('请输入验证码' in response.text or 
                        '访问过于频繁' in response.text or 
                        '抱歉，未找到相关结果。' in response.text or
                        'card-no-result' in response.text):
                        print(f'第{page}页遇到反爬或无数据，停止。')
                        break
                    weibo_list = self.parse_weibo(response.text, keyword)
                    if not weibo_list:
                        print(f'第{page}页无新微博，停止。')
                        break
                    self.save_to_csv(weibo_list, keyword)
                    total_weibo_list.extend(weibo_list)
                    print(f'第{page}页，爬取 {len(weibo_list)} 条微博')
                    page += 1
                    time.sleep(random.uniform(1, 2))
                else:
                    print(f'请求失败: {response.status_code}')
                    break
            except Exception as e:
                print(f'爬取出错: {e}')
                break
        print(f'总共爬取 {len(total_weibo_list)} 条微博')

def main():
    weibo_type = convert_weibo_type(3)
    contain_type = convert_contain_type(1)
    crawler = WeiboCrawler(weibo_type=weibo_type, contain_type=contain_type)
    keywords = ['你好']  # 可以添加多个关键词

    while True:
        
        for keyword in keywords:
            print("开始爬取关键词: {}".format(keyword))
            crawler.crawl(keyword)
            # 随机等待1-3秒
        time.sleep(random.uniform(1, 3))

if __name__ == '__main__':
    main() 