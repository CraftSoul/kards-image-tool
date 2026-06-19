import json
import time
import requests


HEADERS = {
    "accept": "*/*",
    "accept-language": "en-GB,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "origin": "https://www.kards.com",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.kards.com/",
    "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
}

CARDS_QUERY = """\
query getCards($language: String, $offset: Int, $nationIds: [Int], \
$kredits: [Int], $q: String, $type: [String], $rarity: [String], \
$set: [String], $showSpawnables: Boolean, $showExiles: Boolean, $showReserved: Boolean) {
  cards(
    language: $language
    first: 20
    offset: $offset
    nationIds: $nationIds
    kredits: $kredits
    q: $q
    type: $type
    set: $set
    rarity: $rarity
    showSpawnables: $showSpawnables
    showExiles: $showExiles
    showReserved: $showReserved
  ) {
    pageInfo {
      count
      hasNextPage
      __typename
    }
    edges {
      node {
        id
        cardId
        importId
        json
        reserved
        imageUrl: image(language: $language)
        thumbUrl: image(type: thumb, language: $language)
        __typename
      }
      __typename
    }
    __typename
  }
}"""

def fetch_all_cards():
    all_cards = []
    total_count = 0
    offset = 0
    first = 20  # 每页数量，与查询一致

    while True:
        variables = {
            "language": "zh",
            "showSpawnables": True,
            "showExiles": True,
            "showReserved": True,
            "offset": offset
        }

        payload = {
            "operationName": "getCards",
            "variables": variables,
            "query": CARDS_QUERY,
        }

        print(f"正在请求 offset={offset} ...")
        try:
            resp = requests.post("https://herokuapi.kards.com/graphql", headers=HEADERS, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"请求失败: {e}")
            break

        # 检查响应结构
        if "data" not in data or "cards" not in data["data"]:
            print("响应中没有 data.cards，可能请求有误")
            print("响应内容:", json.dumps(data, indent=2, ensure_ascii=False))
            break

        cards_data = data["data"]["cards"]
        page_info = cards_data.get("pageInfo", {})
        edges = cards_data.get("edges", [])

        # 记录总数量（第一页获取）
        if offset == 0:
            total_count = page_info.get("count", 0)

        # 提取 node 数据并转换为目标格式
        for edge in edges:
            node = edge.get("node", {})
            # 解析 json 字段
            json_field = node.get("json")
            if isinstance(json_field, str):
                try:
                    json_field = json.loads(json_field)
                except json.JSONDecodeError:
                    json_field = {}
            
            # 构建目标格式
            card = {
                "id": node.get("id"),
                "cardId": node.get("cardId"),
                "importId": node.get("importId"),
                "json": json_field if json_field else {},
                "reserved": node.get("reserved", False),
                "imageUrl": node.get("imageUrl"),
                "thumbUrl": node.get("thumbUrl"),
                "__typename": node.get("__typename", "Card")
            }
            all_cards.append(card)

        print(f"  本页获取 {len(edges)} 条，累计 {len(all_cards)} 条")

        # 检查是否有下一页
        has_next = page_info.get("hasNextPage", False)
        if not has_next:
            break

        offset += first
        time.sleep(0.5)  # 礼貌性延迟

    # 构建最终数据结构
    result = {"cards": all_cards}

    return result

def main():
    print("开始获取所有卡牌 JSON ...")
    data = fetch_all_cards()

    # 打印统计信息
    print(f"\n===== 爬取完成 =====")
    print(f"共获取 {len(data['cards'])} 张卡牌")

    # 保存到文件
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\n已保存到 data.json")

if __name__ == "__main__":
    main()