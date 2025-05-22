#!/usr/bin/env python3

import argparse
import json
# web-crawler.py
import sys
from typing import List, Dict

from bs4 import BeautifulSoup as bs
from playwright.async_api import async_playwright

parser = argparse.ArgumentParser(description='Web crawler arguments')
parser.add_argument('--url', '-u', type=str, default='', help='Base URL to crawl')
parser.add_argument('--start', '-s', type=int, default=0, help='Starting index')
parser.add_argument('--end', '-e', type=int, default=10, help='Ending index')
parser.add_argument('--out', '-o', type=str, default='output.json', help='Output file name')
args = parser.parse_args()

base_url = args.url
start = args.start
end = args.end
output_file = args.out


def show_help():
    print('Usage: python web-crawler.py --url <base_url> --start <start_index> --end <end_index>')
    print('Example: python web-crawler.py --url https://example.com --start 0 --end 10')


async def crawl(url: str, start: int, end: int) -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        data = []

        for i in range(start, end + 1):
            await page.goto(url.replace('{page}', str(i)), wait_until='networkidle',
                            timeout=100000)  # 60 seconds timeout
            content = await page.content()
            soup = bs(content, 'html.parser')
            # Doctor name
            for element in soup.select('.info_chuyengia'):
                name = element.find('h2').text
                position = ''.join(
                    t for t in element.select_one('.font_helI').strings if t.strip()
                ).strip()
                data.append({
                    'name': name,
                    'position': position,
                    'page': i,
                })
            # Doctor image
            for element in soup.select('.thumb_cgia'):
                img_src = element.find('img')['src']
                mapping_name = element.find('img')['alt']
                next(filter(lambda item: item['name'] == mapping_name, data), {}).update({'img_src': img_src})
            await crawl_each_page(page, browser)

        print(data)

        await browser.close()
        return data


async def crawl_each_page(_page, _browser):
    # TODO: Implement the logic to crawl each page
    pass


def write_to_file(data: List[Dict]):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def main():
    doctor_data = await crawl(base_url, start, end)
    write_to_file(doctor_data)
    sys.exit(0)


import asyncio

asyncio.run(main())
