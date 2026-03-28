#!/usr/bin/env python3
"""
同业存单查询脚本（通用版本）
用法: python3 query_cd.py [银行简称]
示例: python3 query_cd.py 民生
       python3 query_cd.py 工商
       python3 query_cd.py 建设
"""
from playwright.sync_api import sync_playwright
import time
import sys
import re

# 银行名称映射表（简称 -> 完整名称）
BANK_MAPPING = {
    # 国有大行
    "工商": "中国工商银行",
    "工行": "中国工商银行",
    "农业": "中国农业银行",
    "农行": "中国农业银行",
    "中国": "中国银行",
    "中行": "中国银行",
    "建设": "中国建设银行",
    "建行": "中国建设银行",
    "交通": "交通银行",
    "交行": "交通银行",
    "邮储": "中国邮政储蓄银行",
    "邮政": "中国邮政储蓄银行",
    
    # 股份制银行
    "招商": "招商银行",
    "招行": "招商银行",
    "民生": "中国民生银行",
    "光大": "中国光大银行",
    "中信": "中信银行",
    "兴业": "兴业银行",
    "浦发": "上海浦东发展银行",
    "浦东": "上海浦东发展银行",
    "平安": "平安银行",
    "华夏": "华夏银行",
    "广发": "广发银行",
    "浙商": "浙商银行",
    "渤海": "渤海银行",
    "恒丰": "恒丰银行",
    "平安": "平安银行",
    
    # 城商行
    "北京": "北京银行",
    "上海": "上海银行",
    "江苏": "江苏银行",
    "南京": "南京银行",
    "杭州": "杭州银行",
    "宁波": "宁波银行",
    "苏州": "苏州银行",
    "徽商": "徽商银行",
    "长沙": "长沙银行",
    "成都": "成都银行",
    "重庆": "重庆银行",
    "青岛": "青岛银行",
    "厦门": "厦门银行",
    "西安": "西安银行",
    "济南": "齐鲁银行",
    "齐鲁": "齐鲁银行",
    "郑州": "郑州银行",
    "天津": "天津银行",
    "贵阳": "贵阳银行",
    "兰州": "兰州银行",
    "乌鲁木齐": "乌鲁木齐银行",
    
    # 农商行
    "重庆农商": "重庆农村商业银行",
    "上海农商": "上海农村商业银行",
    "北京农商": "北京农村商业银行",
    "深圳农商": "深圳农村商业银行",
    "成都农商": "成都农村商业银行",
    "广州农商": "广州农村商业银行",
    "东莞农商": "东莞农村商业银行",
    
    # 外资行
    "汇丰": "汇丰银行",
    "渣打": "渣打银行",
    "花旗": "花旗银行",
    "东亚": "东亚银行",
    "恒生": "恒生银行",
    "星展": "星展银行",
    "大华": "大华银行",
    "华侨": "华侨银行",
    
    # 政策性银行
    "国开": "国家开发银行",
    "国开行": "国家开发银行",
    "进出口": "中国进出口银行",
    "进出口行": "中国进出口银行",
    "农发": "中国农业发展银行",
    "农发行": "中国农业发展银行",
}

def get_bank_full_name(bank_input):
    """根据用户输入获取银行完整名称"""
    if bank_input in BANK_MAPPING:
        return BANK_MAPPING[bank_input]
    
    for key, value in BANK_MAPPING.items():
        if key in bank_input or bank_input in key:
            return value
    
    return bank_input

def query_cd(bank_input="民生"):
    """查询指定银行的同业存单发行信息"""
    bank_full_name = get_bank_full_name(bank_input)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 使用更宽的视口以显示更多列
        page = browser.new_page(viewport={"width": 2560, "height": 1080})
        
        page.goto("https://www.chinamoney.com.cn/chinese/tycdfxxx/?issueStType=1")
        time.sleep(5)
        
        page.fill("#ENTY", bank_full_name)
        time.sleep(1)
        page.click("#queryInterbankInfo")
        time.sleep(5)
        
        screenshot_path = f"/tmp/cd_result_{bank_input}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        
        result_text = page.inner_text("body")
        match = re.search(r'共\s*(\d+)\s*条', result_text)
        
        records = []
        if match:
            count = int(match.group(1))
            print(f"查询结果: 共 {count} 条记录")
            
            if count > 0:
                tables = page.query_selector_all("table")
                for table in tables:
                    rows = table.query_selector_all("tbody tr")
                    if len(rows) > 0:
                        for row in rows:
                            cells = row.query_selector_all("td")
                            if len(cells) >= 5:
                                data = [cell.inner_text().strip() for cell in cells]
                                if data[0]:
                                    if bank_full_name in data[1] or bank_input in data[1]:
                                        record = {}
                                        # 根据表格实际列数映射
                                        record["code"] = data[0] if len(data) > 0 else ""      # 存单代码
                                        record["name"] = data[1] if len(data) > 1 else ""      # 存单简称
                                        record["date"] = data[2] if len(data) > 2 else ""      # 发行日期
                                        record["method"] = data[3] if len(data) > 3 else ""    # 发行方式
                                        record["term"] = data[4] if len(data) > 4 else ""      # 期限
                                        record["coupon"] = data[5] if len(data) > 5 else ""    # 息票类型
                                        record["face_rate"] = data[6] if len(data) > 6 else "" # 票面利率
                                        record["ref_rate"] = data[7] if len(data) > 7 else ""  # 参考收益率
                                        record["amount"] = data[8] if len(data) > 8 else ""    # 计划发行量
                                        record["rating"] = data[9] if len(data) > 9 else ""    # 主体评级
                                        
                                        records.append(record)
                        break
        else:
            print("未能获取结果数量")
        
        browser.close()
        return screenshot_path, records, bank_full_name

if __name__ == "__main__":
    bank_input = sys.argv[1] if len(sys.argv) > 1 else "民生"
    
    print(f"正在查询 [{bank_input}] 的同业存单信息...")
    screenshot_path, records, bank_full_name = query_cd(bank_input)
    
    print(f"\n截图已保存: {screenshot_path}")
    
    if records:
        print(f"\n{bank_full_name}同业存单发行计划:")
        print(f"\n找到 {len(records)} 条记录:")
        for i, record in enumerate(records, 1):
            print(f"\n[{i}] {record['name']}")
            print(f"    代码: {record['code']}")
            print(f"    发行日期: {record['date']}")
            print(f"    发行方式: {record['method']}")
            print(f"    期限: {record['term']}")
            if record['amount'] and record['amount'] not in ['', '--']:
                print(f"    计划发行量(亿元): {record['amount']}")
            if record['ref_rate'] and record['ref_rate'] not in ['', '--']:
                print(f"    参考收益率(%): {record['ref_rate']}")
            if record['face_rate'] and record['face_rate'] not in ['', '--']:
                print(f"    票面利率: {record['face_rate']}")
            if record['rating'] and record['rating'] not in ['', '--']:
                print(f"    主体评级: {record['rating']}")
            if record['coupon'] and record['coupon'] not in ['', '--']:
                print(f"    息票类型: {record['coupon']}")
    else:
        print(f"\n今日{bank_full_name}无存单发行计划")
