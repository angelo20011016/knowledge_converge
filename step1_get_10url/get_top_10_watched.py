import os
from googleapiclient.discovery import build
from isodate import parse_duration

def get_videos_by_api(query: str, max_results: int = 50):
    """
    使用 Google YouTube API 搜尋影片，並按觀看次數排序。
    需要設定 'YOUTUBE_API_KEY' 環境變數。
    """
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("請設定 'YOUTUBE_API_KEY' 環境變數")

    youtube = build("youtube", "v3", developerKey=api_key)

    # 搜尋影片
    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        type="video",
        maxResults=max_results
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
    if not video_ids:
        return []

    # 取得影片詳細資訊
    video_response = youtube.videos().list(
        part="statistics,snippet,contentDetails",
        id=",".join(video_ids)
    ).execute()

    # 過濾掉 Shorts (長度小於 60 秒)
    def is_not_shorts(video):
        duration = parse_duration(video["contentDetails"]["duration"]).total_seconds()
        return duration >= 60

    videos_filtered = [v for v in video_response.get("items", []) if is_not_shorts(v)]

    # 按觀看數排序
    videos_sorted = sorted(videos_filtered, key=lambda x: int(x.get("statistics", {}).get("viewCount", 0)), reverse=True)

    # 整理結果
    results = []
    for v in videos_sorted:
        title = v["snippet"]["title"]
        url = f"https://www.youtube.com/watch?v={v['id']}"
        results.append({"title": title, "url": url, "video_id": v['id']})
        
    return results

if __name__ == '__main__':
    # 這是一個使用範例
    # 在執行前，請確保您已經設定了 YOUTUBE_API_KEY 環境變數
    # export YOUTUBE_API_KEY="YOUR_API_KEY"
    try:
        top_videos = get_videos_by_api("RAG LLM", max_results=10)
        for video in top_videos:
            print(f"{video['title']} | {video['url']}")
    except ValueError as e:
        print(e)