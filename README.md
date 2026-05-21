# Legal Video Finder

Legal Video Finder 是一个 Python 桌面软件，用于搜索合法影视、动漫、公开视频档案、官方入口、预告片和用户自定义授权来源。

项目地址：https://github.com/qqemail0/legal-video-finder

## 重要边界

本项目不提供盗版影视搜索、破解播放源、绕过付费墙、提取隐藏流媒体地址或规避版权限制的能力。所有结果都会展示来源、匹配度、合法性标记和说明。

## 功能

- 多来源并行搜索：内置合法片库、Internet Archive、Jikan Anime、TVmaze、自定义 JSON 合法源。
- 精准排序：标题规范化、相似度评分、完全匹配加权、重复结果去重。
- 桌面 UI：搜索、结果详情、打开观看入口、打开来源页。
- 本地收藏：SQLite 保存收藏，不依赖服务器。
- 最近搜索：本地保存查询历史。
- 可扩展 Provider：后续可接 TMDb、官方平台 API、企业内部授权片库。
- 零第三方依赖：首版只使用 Python 标准库，便于运行和打包。

## 运行

要求 Python 3.10 或更高版本。

```powershell
$env:PYTHONPATH = "src"
python -m legal_video_finder
```

也可以运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_app.ps1
```

## 自定义合法源

复制示例文件：

```powershell
Copy-Item data\custom_sources.example.json data\custom_sources.json
```

然后把你拥有授权、公共版权或官方允许公开访问的视频链接写入 `data/custom_sources.json`。

## 验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1
```

## 数据源说明

- Internet Archive Advanced Search 可输出 JSON、XML、HTML、CSV 和 RSS。
- Jikan 提供 MyAnimeList 动漫元数据搜索。
- TVmaze 提供剧集搜索 API，结果按相关性返回。

## 后续路线

- 增加 TMDb/OMDb 等需要用户 API Key 的可选 Provider。
- 增加平台可用性确认模块，只检查官方站点。
- 增加 PyInstaller 打包脚本。
- 增加更精细的筛选：年份、类型、语言、地区、授权类型。

## License

MIT

