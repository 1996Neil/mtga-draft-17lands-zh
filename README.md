# MTGA 17Lands 简体中文辅助

基于 [unrealities/MTGA_Draft_17Lands](https://github.com/unrealities/MTGA_Draft_17Lands)
的非官方中文显示分支。保留英文计算、统计、推荐与套牌导出，在显示层增加中文牌名和界面。
上游代码采用 MIT 许可，原版权声明保留在 [LICENSE](LICENSE)；
第三方牌名、游戏内容和统计数据的边界见 [DATA-NOTICE.md](DATA-NOTICE.md)。

本分支基于上游 4.23 开始开发，已合入后续功能到 4.32。macOS Apple Silicon
为本地验证环境；不把其他平台或真实完整轮抽体验声明为已验证。

## 能做什么

- 中文/英文显示切换，未知或身份不匹配的译名回退英文。
- 中文牌名启动差量更新：只查一次小版本清单，未更新就结束，不常驻、不自动重试。
- 显示层不把译名、规则文本或外部缓存内容写回评分使用的原始卡牌对象。
- 主窗口与迷你模式切换；macOS Dock 再次打开时恢复当前窗口。
- 继续使用上游的轮抽统计、牌池、构筑和数据集功能。

中文牌名来源为公开的
[mtga-card-names](https://github.com/1996Neil/mtga-card-names) names-only 版本包。
自动更新说明见 [轻量更新契约](docs/localization/LIGHTWEIGHT-UPDATES.md)。

## 从源码运行

需要 Python 3.12+ 和可用的 Tk。项目依赖由 Poetry 锁定：

```sh
git clone https://github.com/1996Neil/mtga-draft-17lands-zh.git
cd mtga-draft-17lands-zh
poetry install
poetry run python candidate_main.py
```

中文候选入口使用独立用户配置目录。不会自动操作游戏、抓牌或打牌。
MTGA 中仍需手动开启 Detailed Logs。配置文件、游戏日志、缓存和个人数据不要提交。

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
