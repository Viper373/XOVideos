![XOVideos](https://socialify.git.ci/Viper373/XOVideos/image?description=1&font=Inter&forks=1&issues=1&logo=https%3A%2F%2Fimg.viper3.top%2FXOVideos%2Flogo.png&name=1&owner=1&pattern=Circuit+Board&pulls=1&stargazers=1&theme=Light)
# XOVideos 📥

XOVideos 是一个为用户打造的个性化视频下载工具，专注于提供“关注、订阅、喜爱”等功能，帮助用户轻松下载自己喜欢的内容。 目前，项目仅支持 **Pornhub**站，后续会逐步兼容其他平台，如 **Telegram** 等。

## 功能 ✨

- **订阅视频作者**：自动获取并更新你订阅的作者视频信息。
- **喜爱视频下载**：下载你喜爱的影片，支持自定义下载路径。
- **自动更新**：监控作者视频更新，自动下载最新内容。
- **Github Actions 支持**：支持 Github Actions 自动化部署，欢迎 Fork 本项目。
- **多平台支持（未来计划）**：目前支持 **Pornhub**，未来会逐步添加对 **Telegram** 等平台的支持。

## 特性 🛠️

- 使用 **Python 3.10.11** 版本。
- 利用 **MongoDB** 存储视频信息和下载状态。
- 自动下载支持的视频，使用 `streamlink` 工具。
- 配置 **Cookies** 和 **请求头**。
- 自动记录日志，帮助调试和监控任务进度。

## 项目结构 📂

```plaintext
XOVideos/
│
├── config/                  # 配置文件目录
│   ├── download.cfg         # 下载工具配置
│   ├── pornhub.cfg          # Pornhub 站点配置
│   └── telegram.cfg         # 未来的 Telegram 配置
│
├── logs/                    # 日志文件目录
│
├── run_task/                # 主任务脚本
│   └── run.py               # 运行脚本
│
├── tool_utils/              # 工具库
│   ├── api_utils.py         # API 请求工具
│   ├── file_utils.py        # 文件工具
│   ├── log_utils.py         # 日志工具
│   ├── mongo_utils.py       # MongoDB 操作工具
│   ├── proxy_utils.py       # 代理工具
│   ├── redis_utils.py       # Redis 工具（暂未使用）
│   └── string_utils.py      # 字符串处理工具
│
├── videos/                  # 下载的视频文件夹
│   └── pornhub/             # Pornhub 视频文件夹
│
├── website/                 # 站点抓取文件夹
│   └── pornhub.py           # Pornhub 抓取脚本
│
├── main.py                  # 主程序
└── test.py                  # 测试脚本
```

## Github Actions 部署 🚀
- **Fork** 本项目
- 添加环境变量（**GitHub Secrets**）

| 变量名           | 值类型  | 说明              |
|---------------|------|-----------------|
| Cookies       | Text | pornhub的Cookies |
| MONGO_URI     | Text | MongoDB的连接URI   |
| S3_ENDPOINT   | Text | S3的Endpoint     |
| S3_REGION     | Text | S3的Region       |
| S3_ACCESS_KEY | Text | S3的Access Key   |
| S3_SECRET_KEY | Text | S3的Secret Key   |
| S3_BUCKET     | Text | S3的Bucket       |
- 在仓库页面，点击 **Settings（设置）**按钮。 
- 在左侧菜单中，找到 **Secrets and variables**，然后选择 **Actions**。 
- 点击 **New repository secret** 按钮，添加新的密钥： 

- 点击 **Add secret** 完成添加。

## 安装与使用 🚀

### 环境要求

- `Python 3.10.11`
- `MongoDB`丨MongoDB的免费云服务：[MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
  - **注意**：确保MongoDB服务IP地址在白名单中，或者关闭IP白名单功能（添加0.0.0.0/0到白名单）。
- `streamlink`

### 安装依赖

1. 克隆本项目：

    ```bash
    git clone https://github.com/Viper373/XOVideos.git
    cd XOVideos
    ```

2. 安装 Python 依赖：

    ```bash
    pip install -r requirements.txt
    ```

3. 安装并配置 `streamlink`：

    请参考 [streamlink 官方文档](https://streamlink.github.io/) 安装并配置 `streamlink`。

### 配置

1. 配置 `config/pornhub.cfg` 和 `config/download.cfg`，具体可以参考注释。
2. 配置你的 **Cookies**（从浏览器中提取）到 `pornhub.cfg` 文件中。

### 运行项目

执行以下命令来启动项目：

```bash
python main.py
```

## 许可证 📄

本项目采用 [MIT 许可证](LINCENSE) 。