# MTGA 17Lands 简体中文辅助

基于 [unrealities/MTGA_Draft_17Lands](https://github.com/unrealities/MTGA_Draft_17Lands)
的非官方中文显示分支。保留英文计算、统计、推荐与套牌导出，在显示层增加中文牌名和界面。
上游代码采用 MIT 许可，原版权声明保留在 [LICENSE](LICENSE)；
第三方牌名、游戏内容和统计数据的边界见 [DATA-NOTICE.md](DATA-NOTICE.md)。

本分支基于上游 4.23 开始开发，已合入后续功能到 4.32。macOS Apple Silicon
为本地验证环境；不把其他平台或真实完整轮抽体验声明为已验证。

## 原作者与项目来源

本项目是衍生分支，并非从零开发；轮抽辅助的主体功能来自原项目及其贡献者：

- **原始项目作者：**[bstaple1](https://github.com/bstaple1)，
  [MTGA_Draft_17Lands 原始仓库](https://github.com/bstaple1/MTGA_Draft_17Lands)。
- **本分支直接参考和跟进的上游维护者：**[unrealities](https://github.com/unrealities)，
  [上游仓库](https://github.com/unrealities/MTGA_Draft_17Lands)。
- **本分支维护：**[1996Neil](https://github.com/1996Neil)，主要负责中文显示、
  中文牌名差量更新、macOS 窗口兼容和相关修复，不将上游功能归为原创。
- **统计来源：**[17Lands](https://www.17lands.com/)；中文牌名来源为
  [mtga-card-names](https://github.com/1996Neil/mtga-card-names)，其中也包含社区译名。

感谢原作者、上游维护者及所有贡献者。使用和再分发代码时请保留
[原 MIT 版权与许可声明](LICENSE)；第三方统计、译名和游戏内容不因代码开源而自动成为 MIT 数据。
本分支不是原作者、17Lands 或 Wizards of the Coast 的官方中文发行版。

## 能做什么

- 中文/英文显示切换，未知或身份不匹配的译名回退英文。
- 中文牌名启动差量更新：只查一次小版本清单，未更新就结束，不常驻、不自动重试。
- 显示层不把译名、规则文本或外部缓存内容写回评分使用的原始卡牌对象。
- 主窗口与迷你模式切换；macOS Dock 再次打开时恢复当前窗口。
- 继续使用上游的轮抽统计、牌池、构筑和数据集功能。

中文牌名来源为公开的
[mtga-card-names](https://github.com/1996Neil/mtga-card-names) names-only 版本包。
自动更新说明见 [轻量更新契约](docs/localization/LIGHTWEIGHT-UPDATES.md)。

## 使用方法

### 1. 安装并启动

目前本仓库提供源码和手动构建流程，**尚未发布可直接下载的安装包**。
原作者仓库中的安装包属于上游版本，不包含本分支的中文改动。

准备 Python 3.12–3.14、Git、[Poetry](https://python-poetry.org/docs/#installation)
及可用的 Tk。可以先用 `python3 -m tkinter` 检查能否弹出测试窗口，再执行：

```sh
git clone https://github.com/1996Neil/mtga-draft-17lands-zh.git
cd mtga-draft-17lands-zh
poetry install
poetry run python candidate_main.py
```

中文候选入口使用独立用户配置目录。不会自动操作游戏、抓牌或打牌。
以后从同一源码目录执行 `poetry run python candidate_main.py` 即可重开，
无需每次重新安装依赖。若已自行构建 macOS 应用，可双击
`dist/MTGA_17Lands_ZH_Candidate.app` 启动。

### 2. 连接 MTG Arena

1. 在 MTGA 的 **Options → Account** 中开启 **Detailed Logs (Plugin Support)**。
2. 登录游戏，再启动本工具；首次启动会查找 `Player.log`。
3. 如果没有自动找到，在 **文件 → 读取 Player.log…**
   （`File → Read Player.log...`）中手动选择日志。
4. 如果下载数据时找不到本地卡牌库，在 **文件 → 定位 MTGA 数据目录…**
   （`File → Locate MTGA Data Folder...`）中选择游戏的 `MTGA_Data` 目录。
   已汉化过英文数据库的安装，还需要按下方说明准备本地英文索引。

### 3. 选择正确的胜率数据

1. 打开底部 **数据集（Datasets）** 标签。
2. 选择要玩的系列和赛制，例如 Quick Draft 对应 `QuickDraft`，
   不要拿 `PremierDraft` 数据替代；再选玩家组及时间范围。
3. 点击下载所选数据集，等待完成；回到主界面确认当前使用的数据集与赛事一致。

随源码提供的 FRA 数据是历史样例，不代表当前系列或当前赛制的数据。
新系列需要相应 17Lands 统计可用后再下载。数据不足时出现 `—` 或零值，
不表示程序能自动补出可靠胜率。

### 4. 开始轮抽

在 MTGA 进入轮抽并打开牌包，工具会读取日志刷新当前包、已选牌池和建议。
**实际选牌仍由你在游戏中手动完成。**

- 主界面查看牌包、评分、胜率、颜色路线和牌池；底部标签可查看牌池与套牌构筑。
- 顶部颜色筛选选 **全部** 可查看总体统计；**自动** 会按当前牌池颜色筛选，
  部分颜色没有数据时可能显示 `—`。
- 点击 **迷你模式** 显示紧凑窗口；拖动标题区域移动，点击 `⤢` 或系统关闭按钮返回主窗。
- macOS 最小化或隐藏后，再点 Dock 图标可恢复当前窗口。
- 如果日志没有及时刷新，可先确认详细日志已开启、日志路径正确，再点击 **重新载入（Reload）**。

### 5. 中文显示与更新

在 **文件 → 简体中文显示** 中切换中文/英文，也可在 **偏好设置** 中调整。
没有可信匹配的中文牌名会显示英文，不在线猜译。

开启中文显示且未指定自定义中文源时，程序每次启动只在后台检查一次小版本清单。
没有更新就结束，有更新只下载并应用变化的牌名；离线或失败继续使用现有中文，
不常驻轮询、不自动重试，也不重复校验已有全量牌名。
**中文牌名更新与 17Lands 胜率数据更新是两回事**，后者仍在数据集标签操作。

macOS 候选的配置、日志及本地索引位于：

```text
~/Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate/
```

请勿将其中的个人配置、游戏日志、缓存或牌池资料提交到仓库。

## 英文安装与已汉化安装

未修改英文游戏数据的安装可以直接使用本机数据库。应用只在需要建立卡牌索引时
提取牌名、颜色、类型和子类型，在用户配置目录缓存一份小索引；相同版本不重复扫描。

**已修改英文数据库的汉化安装**需要用户从自己已有的、同游戏版本的原始数据库
准备索引。不能从已被替换的中文内容推测英文，也不能把旧版本强行绑定到新版本。

```sh
poetry run python Tools/prepare_english_index.py /path/to/original-card-database.mtga \
  --output "/path/to/app-profile/Names/english-index.json"
```

macOS 中文候选的 app-profile 是
`~/Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate`。
缺少匹配索引时会明确提示并保留已有数据集。公开源码和新构建不附带完整游戏英文文本。

若本地已准备当前版本的 `Names/english-index.json`，应用仍报
`verified English source does not match`，说明启动的还是旧构建。
请使用下方步骤重新构建并启动新应用；更新源码不会更新已经打包的 `.app`。
新读取逻辑会优先使用本地匹配索引，不需要修改游戏或强行重绑旧英文快照。
游戏重启后，工具会从赛事列表中识别未完成的限制赛，不会把前面的普通对局
当作轮抽；后期牌包变小时也不会因此丢弃有效的轮抽缓存。

## 构建与验证

```sh
poetry run pyinstaller candidate.spec --noconfirm
poetry run pytest tests/test_english_index.py tests/test_live_data_fix.py \
  tests/test_names_update.py tests/test_chinese_display.py \
  tests/test_mini_lifecycle.py tests/test_macos_reopen.py -q
```

macOS 输出为 `dist/MTGA_17Lands_ZH_Candidate.app`。本地临时签名不等于 Apple 公证；
不要通过关闭系统安全检查来掩盖签名失败。仓库的手动 macOS 构建工作流只上传短期制品，
不会因普通源码推送而构建或发布安装包。

原生窗口验证使用合成数据及临时配置：

```sh
poetry run python Tools/check_macos_reopen.py /path/to/MTGA_17Lands_ZH_Candidate.app
```

开发环境测试不替代真实游戏和完整轮抽验证。源数据没有胜率时保留缺失值，不伪造评分。

## 维护与贡献

- [通用操作说明](docs/localization/OPERATIONS-ZH.md)
- [公开源码边界](docs/localization/PUBLIC-SOURCE.md)
- [中文差量更新](docs/localization/LIGHTWEIGHT-UPDATES.md)
- [上游架构文档](docs/00-system-overview.md)

欢迎提交最小复现与合成测试。请勿在 Issue、提交、附件或截图中上传账号、游戏日志、
API 凭据、原始游戏数据库、完整本地化表或本机内部运行资料。
