# -*- coding: utf-8 -*-
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import unquote, quote

import requests
import scrapy

import weibo.utils.util as util
from scrapy.exceptions import CloseSpider
from scrapy.utils.project import get_project_settings
from weibo.items import WeiboItem


class SearchSpider(scrapy.Spider):
    name = 'search'
    allowed_domains = ['weibo.com']
    settings = get_project_settings()
    keyword_list = settings.get('KEYWORD_LIST')
    if not isinstance(keyword_list, list):
        if not os.path.isabs(keyword_list):
            keyword_list = os.getcwd() + os.sep + keyword_list
        if not os.path.isfile(keyword_list):
            sys.exit('不存在%s文件' % keyword_list)
        keyword_list = util.get_keyword_list(keyword_list)

    for i, keyword in enumerate(keyword_list):
        if len(keyword) > 2 and keyword[0] == '#' and keyword[-1] == '#':
            keyword_list[i] = '%23' + keyword[1:-1] + '%23'
    weibo_type = util.convert_weibo_type(settings.get('WEIBO_TYPE'))
    contain_type = util.convert_contain_type(settings.get('CONTAIN_TYPE'))
    regions = util.get_regions(settings.get('REGION'))
    base_url = 'https://s.weibo.com'
    start_date = settings.get('START_DATE',
                              datetime.now().strftime('%Y-%m-%d'))
    end_date = settings.get('END_DATE', datetime.now().strftime('%Y-%m-%d'))
    if util.str_to_time(start_date) > util.str_to_time(end_date):
        sys.exit('settings.py配置错误，START_DATE值应早于或等于END_DATE值，请重新配置settings.py')
    further_threshold = settings.get('FURTHER_THRESHOLD', 46)
    limit_result = settings.get('LIMIT_RESULT', 0)
    result_count = {}
    mongo_error = False
    pymongo_error = False
    mysql_error = False
    pymysql_error = False
    sqlite3_error = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result_count = {}

    def check_limit(self, keyword):
        """检查是否达到爬取结果数量限制（按关键词）"""
        if self.limit_result > 0 and self.result_count.get(keyword, 0) >= self.limit_result:
            print(f'关键词【{keyword}】已达到爬取结果数量限制：{self.limit_result}条，停止爬取')
            return True
        return False

    def start_requests(self):
        """生成初始请求"""
        from datetime import datetime
        
        print("\n开始生成初始请求")
        for keyword in self.keyword_list:
            print(f"处理关键词: {keyword}")
            # 对关键词进行URL编码
            encoded_keyword = quote(keyword)
            # 构造基础URL，添加必要的参数
            base_url = f'https://s.weibo.com/weibo?q=%27%27&scope=ori&atten=1&haspic=1'
            
            # 记录请求时间
            request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{request_time}] [请求] 发送初始请求: {base_url}")
            
            # 设置请求元数据
            meta = {
                'keyword': keyword,
                'base_url': base_url,
                'page_count': 10,  # 默认页面数量
            }
            
            # 生成请求
            yield scrapy.Request(
                url=base_url,
                callback=self.parse,
                meta=meta,
                dont_filter=True  # 允许重复请求
            )

    def check_environment(self):
        """判断配置要求的软件是否已安装"""
        if self.pymongo_error:
            print('系统中可能没有安装pymongo库，请先运行 pip install pymongo ，再运行程序')
            raise CloseSpider()
        if self.mongo_error:
            print('系统中可能没有安装或启动MongoDB数据库，请先根据系统环境安装或启动MongoDB，再运行程序')
            raise CloseSpider()
        if self.pymysql_error:
            print('系统中可能没有安装pymysql库，请先运行 pip install pymysql ，再运行程序')
            raise CloseSpider()
        if self.mysql_error:
            print('系统中可能没有安装或正确配置MySQL数据库，请先根据系统环境安装或配置MySQL，再运行程序')
            raise CloseSpider()
        if self.sqlite3_error:
            print(
                '系统中可能没有安装或正确配置SQLite3数据库，请先根据系统环境安装或配置SQLite3，尝试 pip install sqlite，再运行程序')
            raise CloseSpider()

    def parse(self, response):
        """解析搜索结果页面"""
        from datetime import datetime
        
        print("\n" + "="*50)
        print("[响应] 收到页面响应")
        print(f"URL: {response.url}")
        print(f"状态码: {response.status}")
        print(f"关键词: {response.meta['keyword']}")
        print(f"基础URL: {response.meta['base_url']}")
        print(f"页面数量: {response.meta['page_count']}")
        print(f"是否为空: {not response.body}")
        print("="*50 + "\n")
        
        # 检查页面是否为空
        if not response.body:
            print(f"页面为空，跳过解析: {response.url}")
            return
            
        # 解析微博内容
        yield from self.parse_weibo(response)
        print("[信息] 已完成第一页数据爬取")

    def parse_by_day(self, response):
        """以天为单位筛选"""
        base_url = response.meta.get('base_url')
        keyword = response.meta.get('keyword')
        province = response.meta.get('province')
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')
        date = response.meta.get('date')
        page_count = len(response.xpath('//ul[@class="s-scroll"]/li'))
        if is_empty:
            print('当前页面搜索结果为空')
        elif page_count < self.further_threshold:
            # 解析当前页面
            for weibo in self.parse_weibo(response):
                self.check_environment()
                # 检查是否达到爬取结果数量限制
                if self.check_limit(keyword):
                    return
                yield weibo
            next_url = response.xpath(
                '//a[@class="next"]/@href').extract_first()
            if next_url:
                # 检查是否达到爬取结果数量限制
                if self.check_limit(keyword):
                    return
                next_url = self.base_url + next_url
                yield scrapy.Request(url=next_url,
                                     callback=self.parse_page,
                                     meta={'keyword': keyword})
        else:
            start_date_str = date + '-0'
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d-%H')
            for i in range(1, 25):
                start_str = start_date.strftime('%Y-%m-%d-X%H').replace(
                    'X0', 'X').replace('X', '')
                start_date = start_date + timedelta(hours=1)
                end_str = start_date.strftime('%Y-%m-%d-X%H').replace(
                    'X0', 'X').replace('X', '')
                url = base_url + self.weibo_type
                url += self.contain_type
                #url += '&timescope=custom:{}:{}&page=1'.format(
                #    start_str, end_str)
                # 获取一小时的搜索结果
                yield scrapy.Request(url=url,
                                     callback=self.parse_by_hour_province
                                     if province else self.parse_by_hour,
                                     meta={
                                         'base_url': base_url,
                                         'keyword': keyword,
                                         'province': province,
                                         'start_time': start_str,
                                         'end_time': end_str
                                     })

    def parse_by_hour(self, response):
        """以小时为单位筛选"""
        keyword = response.meta.get('keyword')
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')
        start_time = response.meta.get('start_time')
        end_time = response.meta.get('end_time')
        page_count = len(response.xpath('//ul[@class="s-scroll"]/li'))
        if is_empty:
            print('当前页面搜索结果为空')
        elif page_count < self.further_threshold:
            # 解析当前页面
            for weibo in self.parse_weibo(response):
                self.check_environment()
                yield weibo
            next_url = response.xpath(
                '//a[@class="next"]/@href').extract_first()
            if next_url:
                next_url = self.base_url + next_url
                yield scrapy.Request(url=next_url,
                                     callback=self.parse_page,
                                     meta={'keyword': keyword})
        else:
            for region in self.regions.values():
                url = ('https://s.weibo.com/weibo?q={}&region=custom:{}:1000'
                       ).format(keyword, region['code'])
                url += self.weibo_type
                url += self.contain_type
                #url += '&timescope=custom:{}:{}&page=1'.format(
                #    start_time, end_time)
                # 获取一小时一个省的搜索结果
                yield scrapy.Request(url=url,
                                     callback=self.parse_by_hour_province,
                                     meta={
                                         'keyword': keyword,
                                         'start_time': start_time,
                                         'end_time': end_time,
                                         'province': region
                                     })

    def parse_by_hour_province(self, response):
        """以小时和直辖市/省为单位筛选"""
        keyword = response.meta.get('keyword')
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')
        start_time = response.meta.get('start_time')
        end_time = response.meta.get('end_time')
        province = response.meta.get('province')
        page_count = len(response.xpath('//ul[@class="s-scroll"]/li'))
        if is_empty:
            print('当前页面搜索结果为空')
        elif page_count < self.further_threshold:
            # 解析当前页面
            for weibo in self.parse_weibo(response):
                self.check_environment()
                yield weibo
            next_url = response.xpath(
                '//a[@class="next"]/@href').extract_first()
            if next_url:
                next_url = self.base_url + next_url
                yield scrapy.Request(url=next_url,
                                     callback=self.parse_page,
                                     meta={'keyword': keyword})
        else:
            for city in province['city'].values():
                url = ('https://s.weibo.com/weibo?q={}&region=custom:{}:{}'
                       ).format(keyword, province['code'], city)
                url += self.weibo_type
                url += self.contain_type
                #url += '&timescope=custom:{}:{}&page=1'.format(
                #    start_time, end_time)
                # 获取一小时一个城市的搜索结果
                yield scrapy.Request(url=url,
                                     callback=self.parse_page,
                                     meta={
                                         'keyword': keyword,
                                         'start_time': start_time,
                                         'end_time': end_time,
                                         'province': province,
                                         'city': city
                                     })

    def parse_page(self, response):
        """解析一页搜索结果的信息"""
        keyword = response.meta.get('keyword')
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')
        if is_empty:
            print('当前页面搜索结果为空')
        else:
            for weibo in self.parse_weibo(response):
                self.check_environment()
                # 检查是否达到爬取结果数量限制
                if self.check_limit(keyword):
                    return
                yield weibo
            next_url = response.xpath(
                '//a[@class="next"]/@href').extract_first()
            if next_url:
                # 检查是否达到爬取结果数量限制
                if self.check_limit(keyword):
                    return
                next_url = self.base_url + next_url
                yield scrapy.Request(url=next_url,
                                     callback=self.parse_page,
                                     meta={'keyword': keyword})

    def get_ip(self, bid):
        url = f"https://weibo.com/ajax/statuses/show?id={bid}&locale=zh-CN"
        try:
            response = requests.get(url, headers=self.settings.get('DEFAULT_REQUEST_HEADERS'))
            if response.status_code != 200:
                print(f"获取IP请求失败! URL: {url}")
                print(f"状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                return ""
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError as e:
                print(f"JSON解析失败! URL: {url}")
                print(f"错误信息: {str(e)}")
                return ""
            ip_str = data.get("region_name", "")
            if ip_str:
                ip_str = ip_str.split()[-1]
            return ip_str
        except requests.exceptions.RequestException as e:
            print(f"请求异常! URL: {url}")
            print(f"错误信息: {str(e)}")
            return ""

    def get_article_url(self, selector):
        """获取微博头条文章url"""
        article_url = ''
        text = selector.xpath('string(.)').extract_first().replace(
            '\u200b', '').replace('\ue627', '').replace('\n',
                                                        '').replace(' ', '')
        if text.startswith('发布了头条文章'):
            urls = selector.xpath('.//a')
            for url in urls:
                if url.xpath(
                        'i[@class="wbicon"]/text()').extract_first() == 'O':
                    if url.xpath('@href').extract_first() and url.xpath(
                            '@href').extract_first().startswith('http://t.cn'):
                        article_url = url.xpath('@href').extract_first()
                    break
        return article_url

    def get_location(self, selector):
        """获取微博发布位置"""
        a_list = selector.xpath('.//a')
        location = ''
        for a in a_list:
            if a.xpath('./i[@class="wbicon"]') and a.xpath(
                    './i[@class="wbicon"]/text()').extract_first() == '2':
                location = a.xpath('string(.)').extract_first()[1:]
                break
        return location

    def get_at_users(self, selector):
        """获取微博中@的用户昵称"""
        a_list = selector.xpath('.//a')
        at_users = ''
        at_list = []
        for a in a_list:
            if len(unquote(a.xpath('@href').extract_first())) > 14 and len(
                    a.xpath('string(.)').extract_first()) > 1:
                if unquote(a.xpath('@href').extract_first())[14:] == a.xpath(
                        'string(.)').extract_first()[1:]:
                    at_user = a.xpath('string(.)').extract_first()[1:]
                    if at_user not in at_list:
                        at_list.append(at_user)
        if at_list:
            at_users = ','.join(at_list)
        return at_users

    def get_topics(self, selector):
        """获取参与的微博话题"""
        a_list = selector.xpath('.//a')
        topics = ''
        topic_list = []
        for a in a_list:
            text = a.xpath('string(.)').extract_first()
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                if text[1:-1] not in topic_list:
                    topic_list.append(text[1:-1])
        if topic_list:
            topics = ','.join(topic_list)
        return topics

    def get_vip(self, selector):
        """获取用户的VIP类型和等级信息"""
        vip_type = "非会员"
        vip_level = 0

        vip_container = selector.xpath('.//div[@class="user_vip_icon_container"]')
        if vip_container:
            svvip_img = vip_container.xpath('.//img[contains(@src, "svvip_")]')
            if svvip_img:
                vip_type = "超级会员"
                src = svvip_img.xpath('@src').extract_first()
                level_match = re.search(r'svvip_(\d+)\.png', src)
                if level_match:
                    vip_level = int(level_match.group(1))
            else:
                vip_img = vip_container.xpath('.//img[contains(@src, "vip_")]')
                if vip_img:
                    vip_type = "会员"
                    src = vip_img.xpath('@src').extract_first()
                    level_match = re.search(r'vip_(\d+)\.png', src)
                    if level_match:
                        vip_level = int(level_match.group(1))

        return vip_type, vip_level

    def parse_weibo(self, response):
        """解析微博内容"""
        print("\n开始解析微博内容 - 关键词:", response.meta['keyword'])
        weibo_items = response.xpath('//div[contains(@class, "card-wrap") and @action-type="feed_list_item"]')
        print(f"找到 {len(weibo_items)} 条微博")
        
        for item in weibo_items:
            try:
                # 获取微博ID
                weibo_id = item.xpath('.//@mid').get()
                if not weibo_id:
                    continue
                
                # 获取用户信息
                user_info = item.xpath('.//div[@class="info"]//a[@class="name"]')
                user_id = user_info.xpath('./@href').get()
                if user_id:
                    user_id = user_id.split('/')[-1]
                screen_name = user_info.xpath('./text()').get()
                
                # 获取微博内容
                text = item.xpath('.//p[@class="txt"]/text()').getall()
                text = ''.join(text).strip()
                
                # 获取发布时间
                created_at = item.xpath('.//div[@class="from"]//text()').getall()
                created_at = ''.join(created_at).strip()
                # 清理发布时间格式
                if created_at:
                    # 提取月份、日期和时间
                    import re
                    match = re.search(r'(\d{2})月(\d{2})日\s*(\d{2}:\d{2})', created_at)
                    if match:
                        month, day, time = match.groups()
                        # 假设年份是当前年份
                        from datetime import datetime
                        year = datetime.now().year
                        created_at = f"{year}-{month}-{day} {time}"
                
                # 获取来源
                source = item.xpath('.//div[@class="from"]//a[2]/text()').get()
                
                # 获取转发、评论、点赞数
                reposts_count = item.xpath('.//div[@class="card-act"]//li[1]//text()').get()
                comments_count = item.xpath('.//div[@class="card-act"]//li[2]//text()').get()
                attitudes_count = item.xpath('.//div[@class="card-act"]//li[3]//text()').get()
                
                # 清理数字
                reposts_count = int(reposts_count.strip()) if reposts_count and reposts_count.strip().isdigit() else 0
                comments_count = int(comments_count.strip()) if comments_count and comments_count.strip().isdigit() else 0
                attitudes_count = int(attitudes_count.strip()) if attitudes_count and attitudes_count.strip().isdigit() else 0
                
                # 获取图片URL
                pics = []
                img_list = item.xpath('.//div[contains(@class, "media-piclist")]//img/@src').getall()
                for img_url in img_list:
                    if img_url and not img_url.endswith('gif'):
                        img_url = img_url.replace('/thumb150/', '/large/')
                        pics.append(img_url)
                
                # 构建微博数据
                weibo_data = {
                    'id': weibo_id,
                    'bid': weibo_id,
                    'user_id': user_id,
                    'screen_name': screen_name,
                    'text': text,
                    'pics': pics,
                    'created_at': created_at,
                    'source': source,
                    'reposts_count': reposts_count,
                    'comments_count': comments_count,
                    'attitudes_count': attitudes_count,
                    'article_url': '',
                    'location': '',
                    'at_users': '',
                    'topics': '',
                    'video_url': '',
                    'retweet_id': '',
                    'ip': '',
                    'vip_type': '',
                    'vip_level': 0
                }
                
                print(f"解析到微博: ID={weibo_id}, 用户={screen_name}, 内容长度={len(text)}")
                
                yield {
                    'weibo': weibo_data,
                    'keyword': response.meta['keyword']
                }
                
            except Exception as e:
                print(f"解析微博时出错: {e}")
                continue