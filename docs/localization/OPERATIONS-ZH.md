# MTGA 轮抓辅助 · 操作说明

最后更新：2026-10-29　对应包：`Mac-Candidate-DataFix-20261029`　（本文件纳入版本控制：`docs/localization/OPERATIONS-ZH.md`）

---

## 一、日常使用

### 启动

双击 `deliverables/Mac-Candidate-DataFix-20261029/MTGA_17Lands_ZH_Candidate.app`。

- 没有装进 `/Applications`，就放在工程目录里跑
- 启动会自动恢复上一次的轮抓进度（从 `Player.log` 读）
- 首次启动会联网刷新系列列表，几秒钟

### 界面三个区域

| 区域 | 作用 |
|---|---|
| 顶部两个下拉 | 左边是赛事（快速轮抓/ Premier…），中间是**色组筛选** |
| 中间牌包表 | 当前牌包，`评分` / `GIH WR` 两列随色组筛选变化 |
| 右侧抓牌建议 | 按评分排序的推荐，下面是颜色路线、费用曲线、牌池平衡 |

**色组筛选是最容易误会的地方**：

- `全部` = 所有对局统计，数字最全
- `自动` = 按你已选牌的颜色过滤，**没选到的颜色会显示「—」**，不是缺数据

### 卡牌浮窗

鼠标移到牌表某一行会弹出详情（胜率、原型使用比例、卡牌定位）。

- **单击**（不拖动）关闭
- **右键 / Control+单击** 关闭
- **Esc** 关闭
- **按住可以拖动**它

### 迷你模式

主窗口右上角 `迷你模式` 按钮进入，是个无边框小窗：

- 整条标题栏（包括上面的字）都能按住拖动
- 右下角 `⇲` 拖拽缩放
- 标题栏右上 `⤢` 回到主窗口

### 最小化后恢复窗口（2026-11-14 修复）

点击 Dock 中的程序图标会恢复并前置当前窗口：普通模式恢复主窗口，
迷你模式恢复迷你窗口，不同时打开两个界面。重复点击不会新建窗口。
此处理只在 macOS 的 Aqua 窗口系统注册，界面初始化完成之前不会提前显示主窗口。
不更改配置、数据集、牌包、评分和轮抽记录。

迷你窗口的系统关闭按钮与 `⤢` 使用同一条返回主窗口的路径。再次进入时会
检查旧窗口是否仍存在，避免窗口已销毁却一直被当作“已打开”；创建失败时不隐藏主窗口。

原生回归检查（使用临时配置和合成牌包，不读取真实轮抽数据）：

```bash
/path/to/user/Documents/harness_newstart/draft17lands-fix/build-venv2/bin/python \
  Tools/check_macos_reopen.py \
  deliverables/Mac-Candidate-DataFix-20261029/MTGA_17Lands_ZH_Candidate.app
```

检查向指定测试进程发送真实 macOS reopen 事件，覆盖 `iconic`、`withdrawn`、
重复恢复、迷你窗口保持独立、系统关闭、自带返回按钮和直接销毁后的再次进入；
不需要辅助功能或屏幕录制权限。本次窗口生命周期与中文显示相关自动测试 60 项通过。
窗口修复时保留已安装包的中文牌名资源，并确认英文快照相同，避免意外覆盖本地资源。
自动中文更新的新包则明确升级到固定的内置基线 `2026.65.0-r1`。

---

## 二、数据维护

### 什么时候要刷新数据集

- 新系列上线后
- 打了一两周，发现很多牌还是「—」（样本不够 500）
- 官方数据有更新（17Lands 每天在涨）

### 怎么刷新

1. 底部切到 **数据集** 标签
2. 确认：系列 `Reality Fracture`、赛事 `QuickDraft`、用户 `All`、时间范围 `All Time`、最低对局数 `500`
3. 点 **下载所选数据集**，等界面底部状态跑完
4. **退出程序再打开**，新数据集才会完整加载

刷新后覆盖率一般会明显上升（FRA 从 28% 涨到 80% 以上）。

### 数据集相关的坑

| 操作 | 后果 |
|---|---|
| **重置数据集缓存** | ⚠️ 删光 `Sets/` 里所有数据集，别点 |
| 清理非当前数据集 | 只保留当前那份，其余进排除列表 |
| 恢复被排除数据集 | 把排除列表清掉，允许重新下载 |
| 删除单个数据集 | 右下角删除按钮，删掉的那份会进排除列表 |

数据集文件在：

```
~/Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate/Sets/
```

### 自动更新中文牌名（2026-11-14 起）

日常不用运行命令或重打包。开启中文显示且未指定自定义中文源时，程序启动后
在后台只检查一次公开版本文件（当前 64 字节）。相同版本立即结束，不校验
已有全量数据，不常驻、不轮询、不自动重试，也没有新增第三方依赖。

新版本只下载有 `from` / `to` 版本及 SHA-256 的新增、修正、删除差量。
只校验这些新变化，并一次事务修改本地 SQLite 中对应行；界面复用现有更新循环，
不额外增加定时器。整条版本链失败时全部回滚，继续使用已有版本。

首次启动从**本地内置**的 `2026.65.0-r1`（27,720 条）建立牌名库，
只在首次建立或内置基线升级时校验一次。它不下载全量包。存储位置是独立用户配置目录下
`Names/chinese-names.sqlite`，只保留当前版本，不生成历史副本。后续同版本启动只查本地元数据，
不会重新读取内置 JSON，也不会因检查完成而重复重建显示索引。

公开版本文件和差量来自 `mtga-card-names` 的 `updates/` 渠道。
中文源每次发布稳定版 `data-*` 后自动生成差量；预发布不进入稳定渠道。
网络使用短超时，故障不弹阻塞对话框，不妨碍轮抽；下一次重开应用时再检查。
DNS 等系统网络阶段不是严格实时截止时间，不保证所有网络故障都在固定秒数退出。

高级配置 `settings.auto_update_chinese_names=false` 只关闭联网，仍保留已安装的新版。
指定 `chinese_source_path` 时尊重自定义数据，不进行自动更新。
没有对应差量（例如版本过旧）时保留当前版本，**不会回退为全包下载**。
中文牌名更新不更改游戏数据、英文算法输入、胜率数据集或轮抽记录。

### 维护内置中文基线（仅维护者）

中文牌名不再从维护器 registry 手工导出，而是消费公开的 names-only 包：

- 源仓库：<https://github.com/1996Neil/mtga-card-names>
- 当前 pin：`resources/localization/RELEASE.json`（release、版本、三个 sha256、行数）
- 生成物：`resources/localization/cards.json`（**不要手改**）

检查当前文件是否与 pin 一致：

```bash
python3 Tools/sync_card_names.py --check
```

更新到 `RELEASE.json` 指定的 release（校验 manifest、gz、jsonl 三层 hash）：

```bash
python3 Tools/sync_card_names.py --apply
```

注意：这个命令更新的是**源码中的牌名文件**，而且只更新到固定的版本，
不会自动寻找最新版，也不会自动修改已打包的 `.app`。

只有中文牌名变化、程序代码没有变化时，不必重新构建整个应用。先正常退出应用，
更新固定版本并通过牌名与中文显示测试，再把 `resources/localization/cards.json`
复制到实际使用的 `.app/Contents/Resources/resources/localization/cards.json`，
重新执行 `codesign --force --deep --sign -`、严格签名校验后重开。
不要写入游戏安装目录，不要混用胜率数据集下载按钮（它不更新中文牌名）。

完整包只用于维护应用内置基线或人工离线恢复；日常启动走上面的差量渠道。

离线环境可以先下载 release 资产，再指定本地文件：

```bash
python3 Tools/sync_card_names.py \
  --input /path/to/cards.jsonl \
  --apply
```

发布新游戏版本时：先把 `RELEASE.json` 的 `release` / `data_version` / 三个 sha256 / `rows` 更新到新 pin，再跑 `--apply`，最后跑：

```bash
build-venv2/bin/python -m pytest tests/test_card_names_release.py tests/test_chinese_display.py -q
```

`Tools/snapshot_names.py` 和 `Tools/extend_card_names.py` 是旧路径，已标记 deprecated；发行构建不要再用它们直接改 `cards.json`。

---

## 三、出问题怎么办

| 症状 | 原因 | 处理 |
|---|---|---|
| 弹窗 `Unable to access local Arena data` | 游戏更新了，卡牌库版本变了，内置英文快照对不上 | 见下面「游戏更新后」 |
| 牌表大量显示「—」 | 顶部筛选是 `自动`，按你牌色过滤 | 切成 `全部` |
| 某张牌没中文 | 该卡还没进中文索引 | 属正常；详见 README 第 2 节 |
| 浮窗关不掉 | 旧版本 bug | 新包已修（Esc/单击/右键）；旧包只能重启 |
| 拖动窗口卡顿 | 旧版本每秒全量 GC | 新包已修（空闲 CPU 20% → 4.5%） |
| 启动几秒后闪退 | 旧版本后台线程碰 Tk | 新包已修 |
| 窗口卡死、CPU 100% | 旧版本的表格列宽重绘死循环 | 更新到 2026-11-12 之后的包即可 |
| 启动没反应 | — | 看 `~/Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate/Debug/debug.log` |
| 崩溃 | — | 看 `~/Library/Logs/DiagnosticReports/MTGA_17Lands_ZH_Candidate-*.ips` |

### 窗口卡死、CPU 跑满 100%（旧版本才会遇到，已修）

2026-11-12 遇到过一次：窗口拖不动，活动监视器里进程占满一个核。

根因是表格列宽同步的**重绘死循环**——每次都把同一个宽度写回去，而写回又会触发一次布局，
布局又调回同步。中文名比英文长，所以只在开启中文显示时被触发（关掉中文就不复现，
很容易误判成翻译问题）。

修复：同步前先比较，值没变就不下发（`src/ui/components.py`），另外恢复草稿状态前加了
一致性校验（`src/log_scanner.py`）。**新版本不需要任何手动操作**，出现过问题的那份状态
也能正常恢复。

### 游戏更新后（最常见）

MTGA 每次打补丁都会改卡牌库，内置的英文快照会失效，下载数据集时会报 `Unable to access local Arena data`。处理：

```bash
cd ~/Documents/ChatGPT/mtga-draft-17lands-zh-20261010
APP="deliverables/Mac-Candidate-DataFix-20261029/MTGA_17Lands_ZH_Candidate.app"

# 1) 找到当前库文件（Steam 版路径）
DB=$(ls -t ~/Library/Application\ Support/Steam/steamapps/common/MTGA/MTGA_Data/Downloads/Raw/Raw_CardDatabase_*.mtga | head -1)

# 2) 重绑快照（只改版本指纹，英文数据一条不动）
python3 Tools/rebind_english_snapshot.py "$APP/Contents/Resources/resources/arena/english.json" "$DB"

# 3) 重新签名
codesign --force --deep --sign - "$APP"
```

改完重新打开程序，下载功能就恢复了。**不需要重新打包**，也不用重新下载数据集。

---

## 四、代码与推送

### 仓库

```
~/Documents/ChatGPT/mtga-draft-17lands-zh-20261010
分支：codex/zh-display-v423
远端：mine → https://github.com/1996Neil/mtga-draft-17lands-zh （private）
```

远端 `main` 是**压缩快照**（不含 600MB 上游历史），最新 `06b661f`。

### 推送

| 网络状态 | 命令 |
|---|---|
| VPN 开着 | `git push mine <分支>:main` |
| VPN 关着 / 推不动 | **`gpush push mine <分支>:main`** |

`gpush` 会自动判断本地 Clash 端口 `7897` 在不在，在就走代理，不在就走直连，失败重试 3 次。端口不同可覆盖：

```bash
GPUSH_PROXY=http://127.0.0.1:7890 gpush push
```

**注意**：不要往 git 配置里写死 `http.proxy`，Clash 一关就会连代理失败。

`gh` 命令不会自动走代理，VPN 关着时前面加：

```bash
HTTPS_PROXY=http://127.0.0.1:7897 gh auth status
```

### 跟上游新版

上游发新 release 后，不要再手工挑补丁——仓库里已经记录了 `upstream-4.27` 这个合并父节点，直接合就行：

```bash
cd ~/Documents/ChatGPT/mtga-draft-17lands-zh-20261010

# 1) 只取那一个 tag 的提交（浅取，别拉全量历史，上游有 600MB）
git -c http.proxy=http://127.0.0.1:7897 fetch --depth 1 upstream \
  refs/tags/MTGA_Draft_Tool_V0430:refs/tags/upstream-4.30

# 2) 直接合并
git merge upstream-4.30
```

冲突处理原则：**上游已经替代我们本地临时方案的地方取上游**（例如 `suggest_deck` 的线程队列），**用户可见字符串继续包 `tr()`**，中文资源（`resources/localization/`、`resources/arena/english.json`）保持我们自己的。

合完必须做三件事：

1. `grep -n "APPLICATION_VERSION" src/constants.py` —— 确认版本号跟上了，否则又会弹更新提示
2. 跑测试：`build-venv2/bin/python -m pytest tests -q --ignore=tests/server`
3. 如果动了 `src/card_logic.py` 等计算核心，记得同步更新
   `tests/test_chinese_display.py` 里记录的哈希基线

### 改代码后重新构建

```bash
cd ~/Documents/ChatGPT/mtga-draft-17lands-zh-20261010

# 测试
/path/to/user/Documents/harness_newstart/draft17lands-fix/build-venv2/bin/python \
  -m pytest tests -q --ignore=tests/server

# 打包
/path/to/user/Documents/harness_newstart/draft17lands-fix/build-venv2/bin/pyinstaller \
  candidate.spec --noconfirm --distpath dist-YYYYMMDD --workpath build-YYYYMMDD

# 签名
codesign --force --deep --sign - dist-YYYYMMDD/MTGA_17Lands_ZH_Candidate.app
```

构建环境在 `~/Documents/harness_newstart/draft17lands-fix/build-venv2`（约 400 MB，别删，重装要十分钟）。
依赖版本已对齐上游 4.27：Pillow 13、ttkbootstrap 2.2.5、numpy 2.5.4、numba 0.68.1、scipy 1.18.1、pyinstaller 6.22.3。

---

## CI（GitHub Actions）

仓库里保留了两个工作流，行为已经在 2026-10-31 收敛过：

| 工作流 | 触发 | 干什么 |
|---|---|---|
| `publish-release.yml`（Build & Publish Release） | 只有打 `v*` tag 或手动触发 | 三平台打包、建 Release；产物保留 1 天 |
| `etl-pipeline.yml`（Daily Dataset ETL） | 每天 10:23 / 16:41 UTC + 手动 | 拉 17Lands 数据，生成数据集推到 `gh-pages` |

**为什么 push 不再触发构建**：这个工作流每次跑会给三个平台各上传约 200 MB 制品，免费私有仓库只有 500 MB 配额，几次就满（报 `Artifact storage quota has been hit`）。我们本机打包，CI 产物用不到。

### 两个坑

1. **改了 `pyproject.toml` 一定要重新生成锁文件**，否则 CI 第一句 `poetry install` 就会退出：

   ```bash
   build-venv2/bin/poetry lock
   build-venv2/bin/poetry check --lock
   ```

   2026-10-29 那天 ETL 和三平台打包全部失败，就是这一条。

2. **ETL 第一次运行需要初始化仓库**。没有 `gh-pages` 分支时它拒绝自己创建，会报 `Cannot restore gh-pages; refusing to replace the warehouse.`，手动跑一次：

   ```bash
   gh workflow run etl-pipeline.yml -R 1996Neil/mtga-draft-17lands-zh -f initialize_warehouse=true
   ```

   建好之后定时任务就能增量跑了。

## 五、文件索引

| 内容 | 位置 |
|---|---|
| 程序 | `deliverables/Mac-Candidate-DataFix-20261029/MTGA_17Lands_ZH_Candidate.app` |
| 使用/改动记录 | 同目录 `README.md` |
| 维护脚本 | 仓库 `Tools/`：`sync_card_names.py`、`rebind_english_snapshot.py`、`cleanup_local_datasets.py`、`fix_dataset_face_type.py` |
| 运行时数据 | `~/Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate/` |
| 配置 | 同上 `config.json` |
| 日志 | 同上 `Debug/debug.log` |
| 数据集 | 同上 `Sets/` |
| 构建环境 | `~/Documents/harness_newstart/draft17lands-fix/build-venv2/` |
| 推送脚本 | `~/.local/bin/gpush` |

---

## 六、三条禁忌

1. **别点「重置数据集缓存」**——会把所有数据集删光，还会写进排除列表
2. **别在 git 配置里写死代理**——Clash 一关就报 Connection refused
3. **别把 `Sets/` 当长期备份**——那里只有数据集，源码和包都在工程目录里
