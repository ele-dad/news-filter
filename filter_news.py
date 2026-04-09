import feedparser
from feedgen.feed import FeedGenerator
import google.generativeai as genai
import os
import time
import json

# --- 1. 配置区 ---
# 在这里填入你想要去重的原始 RSS 链接（比如 Bloomberg, Reuters 等）
RSS_SOURCES = [
    "https://www.bloomberg.com/politics/feeds/site.xml", # 彭博社政治
    "https://www.reutersagency.com/feed/", # 路透社
    "https://www.theguardian.com/world/rss", # 集邦咨询
    "https://www.zaobao.com.sg/rss/realtime/china", # 联合早报
    "https://www.eurointegration.com.ua/rss/", # 欧洲真相
    "https://china.kyodonews.net/rss/news.xml", # 共同社
    "https://clashreport.com/rss.xml", # 联合早报
    "https://feeds.bloomberg.com/markets/news.rss", # 彭博社市场
    "https://clashreport.com/rss.xml", # 冲突报告
    "https://fortune.com/feed/", # 财富
    "https://www.aljazeera.com/xml/rss/all.xml", # 半岛电视台
    "https://feeds.npr.org/1001/rss.xml", # NPR
]

# 配置 Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-lite')

HISTORY_FILE = 'history.json'
OUTPUT_RSS = 'clean_news.xml'

# --- 2. 核心功能 ---
def get_semantic_slug(title):
    """让 AI 提取语义指纹"""
    prompt = f"Extract 2-3 core English keywords as a semantic slug for this news title. Same events must have the same slug. Title: {title}. Output only the slug."
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower()
    except Exception as e:
        print(f"AI Error: {e}")
        return title

def main():
    # 加载历史指纹记录
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    else:
        history = []

    # 初始化新 RSS 生成器
    fg = FeedGenerator()
    fg.title('My AI Filtered News')
    fg.link(href='https://github.com', rel='alternate')
    fg.description('Cleaned news feed via Gemini AI')

    new_history = []
    processed_count = 0
    
    for url in RSS_SOURCES:
        print(f"Processing: {url}")
        feed = feedparser.parse(url)
        for entry in feed.entries:
            # 提取指纹
            slug = get_semantic_slug(entry.title)
            
            # 如果指纹不在历史记录中，说明是新新闻
            if slug not in history and slug not in new_history:
                fe = fg.add_entry()
                fe.title(entry.title)
                fe.link(href=entry.link)
                fe.description(entry.get('summary', ''))
                new_history.append(slug)
                processed_count += 1
            
            # 遵守 Gemini 免费版频率限制（每分钟15次，所以每条歇4秒）
            time.sleep(4) 

    print(f"Added {processed_count} new unique stories.")

    # 更新历史记录（保留最近 2000 条，防止文件过大）
    updated_history = (new_history + history)[:2000]
    with open(HISTORY_FILE, 'w') as f:
        json.dump(updated_history, f)

    # 生成 RSS 文件
    fg.rss_file(OUTPUT_RSS)

if __name__ == "__main__":
    main()
