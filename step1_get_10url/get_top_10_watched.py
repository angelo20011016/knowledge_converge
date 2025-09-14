import os
from googleapiclient.discovery import build
from isodate import parse_duration

def get_videos_by_api(query: str, max_results: int = 10, lang: str = None):
    """
    使用 Google YouTube API 搜尋影片，並按觀看次數排序。
    需要設定 'YOUTUBE_API_KEY' 環境變數。
    新增 lang 參數以指定搜尋語言。
    """
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("請設定 'YOUTUBE_API_KEY' 環境變數")

    youtube = build("youtube", "v3", developerKey=api_key)

    search_request = youtube.search().list(
        q=query,
        part="id,snippet",
        type="video",
        maxResults=max_results,
        relevanceLanguage=lang, # 根據指定的語言搜尋
        order="viewCount" # 直接請 API 按觀看數排序
    )
    
    # 只有在 lang 被指定時才加入
    if lang:
        search_request.relevanceLanguage = lang

    search_response = search_request.execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return []

    video_response = youtube.videos().list(
        part="statistics,snippet,contentDetails",
        id=",".join(video_ids)
    ).execute()

    def is_not_shorts(video):
        duration = parse_duration(video["contentDetails"]["duration"]).total_seconds()
        return duration >= 60

    videos_filtered = [v for v in video_response.get("items", []) if is_not_shorts(v)]
    
    # API 的 order="viewCount" 排序有時不完全準確，客戶端再次排序以確保
    videos_sorted = sorted(videos_filtered, key=lambda x: int(x.get("statistics", {}).get("viewCount", 0)), reverse=True)

    results = []
    for v in videos_sorted:
        title = v["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={v['id']}"
        results.append({"title": title, "url": url, "video_id": v['id']})
        
    return results

if __name__ == '__main__':
    try:
        print("請選擇搜索模式：")
        print("1. 專注搜尋 (在指定語言中找 10 個結果)")
        print("2. 發散搜尋 (自動尋找 5 個中文和 5 個英文結果)")
        mode = input("請輸入模式編號 (1 或 2): ")

        query = input("請輸入您想搜尋的主題: ")

        all_videos = []
        if mode == '1':
            lang_choice = input("請輸入語言代碼 (例如: 'zh-TW' 代表繁體中文, 'en' 代表英文): ")
            print(f"\n正在以 '{lang_choice}' 語言進行專注搜尋...")
            all_videos = get_videos_by_api(query, max_results=10, lang=lang_choice)
        elif mode == '2':
            print("\n正在進行發散搜尋 (5 中文 + 5 英文)...")
            print("正在搜尋中文結果...")
            zh_videos = get_videos_by_api(query, max_results=5, lang='zh-TW')
            print(f"找到 {len(zh_videos)} 個中文影片。")

            print("\n正在搜尋英文結果...")
            en_videos = get_videos_by_api(query, max_results=5, lang='en')
            print(f"找到 {len(en_videos)} 個英文影片。")
            
            all_videos = zh_videos + en_videos
        else:
            print("錯誤的模式選擇。請重新執行程式並輸入 1 或 2。")

        if all_videos:
            print(f"\n--- 總共找到 {len(all_videos)} 個影片結果 ---")
            for video in all_videos:
                print(f"{video['title']} | {video['url']}")
        else:
            print("找不到任何相關影片。")

    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"發生未預期的錯誤: {e}")