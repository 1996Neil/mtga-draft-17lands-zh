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
| 启动没反应 | — | 看 `~/Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate/Debug/debug.log` |
| 崩溃 | — | 看 `~/Library/Logs/DiagnosticReports/MTGA_17Lands_ZH_Candidate-*.ips` |

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

## 五、文件索引

| 内容 | 位置 |
|---|---|
| 程序 | `deliverables/Mac-Candidate-DataFix-20261029/MTGA_17Lands_ZH_Candidate.app` |
| 使用/改动记录 | 同目录 `README.md` |
| 维护脚本 | 仓库 `Tools/`：`rebind_english_snapshot.py`、`cleanup_local_datasets.py`、`fix_dataset_face_type.py` |
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
