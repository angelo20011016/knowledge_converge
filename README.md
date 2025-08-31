step2. 對單支影片字幕取得
        1先嘗試用yt_get_cc.py 取得cc

        若有 用正則表達式處理 yt_transcription_re.py

        2若無 則用  download_YTvideo2wav 下載wav 目前會放到 audio_files

        3用該檔案連結 ex: D:\projects\loacl_STT\audio_files\一期视频看懂人形机器人_下一个万亿赛道_专访安克创新CEO阳萌_大咖谈芯第15期.wav  
        執行多進程
        parallel_transcriber.py
        得到字幕(還沒寫整合在一份txt的code)


         transcribe_wav.py 得到轉錄文字 
            單個執行的時間:300s
            2/2 medium/flo16 270s
            3/3 base/int8 127s
            
            更改不要分太細後
            3/3 base/int 123s
            2/2 medium/flo16

        因為影片都不會很長 也許可以把step1的200筆資料 結合在一起 再根據2.5flash lit的上下文 分塊

step1.用兩個方法 取得一個主題的雙語言搜尋(中文/英文)*這邊搜尋主要會用中文 再讓他call一個翻譯API 當作參數，總共會有4組 兩支程式碼 一個取觀看 一個取相關 取前50筆? 總共4x50

step3.把那10篇as input 給gemini 做彙整 看是要 10個API 後 再把彙總的10篇call一個api做總結?