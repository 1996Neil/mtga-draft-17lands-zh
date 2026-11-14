# 日常使用与维护

## 启动、窗口与迷你模式

从源码运行 `python candidate_main.py`，或打开本地构建的
`MTGA_17Lands_ZH_Candidate.app`。macOS 再次点击 Dock 图标会恢复当前主窗或迷你窗。
迷你窗的系统关闭按钮和 `⤢` 都返回主窗口，之后可以再次进入迷你模式。

数据集中的 `全部` 和 `自动` 色组筛选含义不同；牌表的 `—` 不等于中文资源缺失。
胜率数据仍需在数据集标签内按正确系列和赛制更新，中文牌名更新不代替它。

## 中文更新

中文显示开启且未指定自定义中文源时，应用每次启动在后台检查一次版本。
当前初始清单正文为 64 字节；以后会随保留版本链增长，上限 32 KiB。
相同版本不扫描已有牌名、不下载全包、不再次重建显示索引，更新线程完成后退出。

新版本只下载新增、修正、删除记录，验证新差量后在一个事务内提交。
失败、离线或版本链缺失时继续使用已有数据；不轮询，不自动重试，不静默全量下载。
只保留当前牌名库，无历史副本。第一次从本地内置基线初始化，不下载全量包。

`settings.auto_update_chinese_names=false` 只关闭联网，已安装牌名仍可用。
配置自定义 `chinese_source_path` 时尊重该来源，不被自动更新覆盖。

## 本地英文兼容

正常英文安装从本机数据库读取所需身份，按游戏版本在
`Names/english-index.json` 缓存。没有英文输入需求时不会为此扫描数据库。
相同版本、相同文件重复读取只查版本元数据，索引校验在进程内复用。

对已汉化的英文数据库，请在汉化前或使用本人已有的同版本原始数据库运行：

```sh
python Tools/prepare_english_index.py /path/to/original-card-database.mtga \
  --output "/path/to/app-profile/Names/english-index.json"
```

该命令只读源文件，只导出牌名、颜色、类型、子类型。规则、背景、提示文本不导出。
游戏版本变化后，旧索引不会被强行重绑；请重新从对应版本的原始数据准备。
无法提供原始英文数据时，保留已有数据集并提示缺失，不凭空还原英文。

公开包不携带完整英文表，也不把个人索引嵌入 `.app`。本地正在使用的旧应用与
本机原始资料不会因仓库公开自动删除或替换。

## 维护内置中文基线

维护者更新 `resources/localization/RELEASE.json` 的版本和校验值，再执行：

```sh
python Tools/sync_card_names.py --apply
python Tools/sync_card_names.py --check
python -m pytest tests/test_card_names_release.py tests/test_chinese_display.py -q
```

这只维护源码内置基线；日常使用走版本差量，不要求用户反复打包。
完整发布流程和更新器边界见 `LIGHTWEIGHT-UPDATES.md`。

## 构建和测试

```sh
poetry run pyinstaller candidate.spec --noconfirm
poetry run pytest tests/test_english_index.py tests/test_live_data_fix.py \
  tests/test_names_update.py tests/test_chinese_display.py -q
```

原生窗口测试只用合成数据和临时配置，不需要辅助功能或屏幕录制权限：

```sh
poetry run python Tools/check_macos_reopen.py /path/to/candidate.app
```

不要提交个人配置、日志、游戏数据库、内部验收资料或本机索引。
