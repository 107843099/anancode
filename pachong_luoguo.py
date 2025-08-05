import csv
import json
import time
import re
import urllib.parse
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

def parse_practice_html_source(html):
    # 用正则匹配 window._feInjection
    match = re.search(r'window\._feInjection = JSON\.parse\(decodeURIComponent\("(.+?)"\)\);', html)
    if not match:
        print("没有 window._feInjection，页面异常或未完全加载！")
        return None
    json_raw = urllib.parse.unquote(match.group(1))
    data = json.loads(json_raw)
    problems = data.get('currentData', {}).get('passedProblems', [])

    # 难度映射
    diff_map = {
        1: '入门', 2: '普及-', 3: '普及/提高-', 4: '提高+/省选-', 5: '省选/NOI-', 6: 'NOI/NOI+/CTSC'
    }
    res = {}
    all_pids = []
    for prob in problems:
        diff = diff_map.get(prob['difficulty'], '未知')
        res.setdefault(diff, []).append(prob['pid'])
        all_pids.append(prob['pid'])

    result = {
        "难度统计": {},
        "所有题号": sorted(list(set(all_pids))),
        "总题数": len(set(all_pids))
    }
    for diff, pids in res.items():
        result["难度统计"][diff] = {
            "数量": len(pids),
            "题号": pids
        }
    return result

# 读取CSV成员列表
members = []
with open("members_info.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        uid = str(row["UID"]).strip()
        if uid:
            members.append({
                "uid": uid,
                "昵称": row.get("昵称", ""),
                "备注": row.get("备注", "")
            })

driver = webdriver.Chrome()
driver.get("https://www.luogu.com.cn/auth/login")
input("请手动登录洛谷账号，登录后回车继续...")

results = {}

for i, member in enumerate(members):
    uid = member["uid"]
    nickname = member["昵称"]
    remark = member["备注"]
    url = f"https://www.luogu.com.cn/user/{uid}#practice"
    driver.get(url)
    print(f"\n[{i+1}/{len(members)}] 抓取UID: {uid}，{nickname}")
    time.sleep(3.5)
    # 滚动让JS全部加载
    for _ in range(7):
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(0.45)

    # 获取完整HTML
    html = driver.page_source
    user_stat = parse_practice_html_source(html)
    if not user_stat:
        user_stat = {
            "难度统计": {},
            "所有题号": [],
            "总题数": 0
        }

    results[uid] = {
        "昵称": nickname,
        "备注": remark,
        **user_stat
    }
    time.sleep(1.1)

# 自动用日期命名文件
date_str = datetime.datetime.now().strftime("%Y-%m-%d")
filename = f"data_{date_str}.json"
with open(filename, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"已保存 {filename}")
driver.quit()
