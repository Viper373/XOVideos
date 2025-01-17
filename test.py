import subprocess


def download_video(m3u8_url, output_file):
    # 使用 streamlink 下载并保存视频
    command = [
        "streamlink",
        m3u8_url,
        "best",  # 选择最高画质，可以根据需要选择 'worst', 'best' 或具体画质
        "-o",
        output_file  # 指定保存的文件路径和文件名
    ]
    subprocess.run(command)


# 使用示例
m3u8_url = "https://hv-h.phncdn.com/hls/videos/202501/06/462786681/720P_4000K_462786681.mp4/master.m3u8?h=+p37kMzasd8aYX8WgkxERBjWsuo=&e=1737152271&f=1"
output_file = "output_video.mp4"
download_video(m3u8_url, output_file)
