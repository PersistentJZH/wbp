# -*- coding: utf-8 -*-
import schedule
import time
import subprocess
import logging
import random
from datetime import datetime, timedelta
import os
import signal
import select

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

# Global variable to store the Scrapy process
scrapy_process = None

def start_scrapy_process():
    """Start the Scrapy process if it's not already running"""
    global scrapy_process
    if scrapy_process is None or scrapy_process.poll() is not None:
        try:
            # 使用 Popen 启动 Scrapy，但不使用管道
            scrapy_process = subprocess.Popen(
                ['scrapy', 'crawl', 'search'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            logging.info("Started new Scrapy process")
            return True
        except Exception as e:
            logging.error(f"Error starting Scrapy process: {str(e)}")
            return False
    return True

def stop_scrapy_process():
    """Stop the Scrapy process if it's running"""
    global scrapy_process
    if scrapy_process is not None:
        try:
            scrapy_process.terminate()
            scrapy_process.wait(timeout=5)
            logging.info("Stopped Scrapy process")
        except Exception as e:
            logging.error(f"Error stopping Scrapy process: {str(e)}")
            try:
                os.kill(scrapy_process.pid, signal.SIGKILL)
            except:
                pass
    scrapy_process = None

def run_crawler():
    """Run the crawler using the existing Scrapy process"""
    try:
        start_time = datetime.now()
        logging.info(f"Crawler started at {start_time}")
        
        # 每次运行都重新启动 Scrapy 进程
        stop_scrapy_process()
        if not start_scrapy_process():
            logging.error("Failed to start Scrapy process")
            return
            
        # 等待进程完成
        stdout, stderr = scrapy_process.communicate()
        
        if stdout:
            logging.info(f"Process output: {stdout}")
        if stderr:
            logging.error(f"Process error: {stderr}")
            
    except Exception as e:
        logging.error(f"Error running crawler: {str(e)}")
        stop_scrapy_process()

def main():
    """Main function"""
    logging.info("Starting periodic crawler program")
    
    try:
        while True:
            try:
                start_time = datetime.now()
                run_crawler()
                end_time = datetime.now()
                duration = end_time - start_time
                logging.info(f"Crawl duration: {duration}")
                
                # 随机等待1到3秒
                sleep_time = random.uniform(2, 5)
                logging.info(f"Sleeping for {sleep_time:.2f} seconds before next crawl")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logging.info("Program interrupted by user")
                break
            except Exception as e:
                logging.error(f"Error during crawler execution: {str(e)}")
                time.sleep(1)  # Wait 1 second after error before continuing
    finally:
        stop_scrapy_process()

if __name__ == "__main__":
    main() 