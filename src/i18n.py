"""Small Chinese-first UI text helpers."""

ZH = {
    "Connecting to 17Lands…": "正在连接 17Lands…",
    "No usable 17Lands win rates. Previous dataset kept.": "没有可用的 17Lands 胜率，已保留原数据集。",
    "Dataset saved for another event. Current draft dataset kept.": "其他赛制的数据已保存，当前轮抓继续使用原数据集。",

    "Preferences": "偏好设置",
    "DATA EVALUATION": "数据显示",
    "Win Rate Format:": "胜率格式：",
    "Deck Filter Format:": "套牌筛选格式：",
    "UI Scale:": "界面缩放：",
    "INTELLIGENCE & HUD": "辅助与界面",
    "Always On Top": "窗口置顶",
    "Auto-Sync Cloud Datasets": "启动时自动同步云数据集",
    "Download Chinese Card Text": "下载中文卡名和牌面",
    "Highlight Row by Mana Cost": "按法术力值高亮行",
    "Check for Dataset Updates": "检查数据集更新",
    "Alert on Missing Datasets": "缺少数据集时提醒",
    "Enable Draft Log Creation": "保存轮抓记录",
    "Show Splash Screen on Startup": "启动时显示加载窗口",
    "SYSTEM PATHS": "系统路径",
    "Player.log Location:": "Player.log 位置：",
    "MTGA_Data Location:": "MTGA_Data 位置：",
    "Restore Defaults": "恢复默认",
    "Done": "完成",
    "Confirm Reset": "确认重置",
    "Restore all settings to default?": "要把所有设置恢复为默认值吗？",
    "File": "文件",
    "Preferences...": "偏好设置...",
    "Read Draft Log...": "读取轮抓记录...",
    "Read Player.log...": "读取 Player.log...",
    "Locate MTGA Data Folder...": "定位 MTGA 数据目录...",
    "Export Draft (CSV)": "导出轮抓 CSV",
    "Export Draft (JSON)": "导出轮抓 JSON",
    "Exit": "退出",
    "Tools": "工具",
    "Practice: Generate Random Sealed Pool": "练习：生成随机现开牌池",
    "Practice: Import Sealed Pool from Clipboard": "练习：从剪贴板导入现开牌池",
    "Theme": "主题",
    "System (Native)": "系统原生",
    "Custom Themes (.tcl)": "自定义主题（.tcl）",
    "Browse for .tcl...": "浏览 .tcl 文件...",
    "Mini Mode": "迷你模式",
    "Reload": "重新载入",
    "Datasets": "数据集",
    "Card Pool": "牌池",
    "Deck Builder": "套牌构筑",
    "Custom Deck": "自定义套牌",
    "Comparisons": "对比",
    "Tier Lists": "梯度表",
    "Hide Tabs": "隐藏标签页",
    "Show Tabs": "显示标签页",
    "Set": "系列",
    "Event": "赛事",
    "Group": "分组",
    "Start": "开始",
    "End": "结束",
    "Collected": "收集时间",
    "Games": "对局数",
    "SET:": "系列：",
    "EVENT:": "赛事：",
    "USERS:": "用户：",
    "MIN GAMES:": "最低对局数：",
    "START DATE:": "开始日期：",
    "END DATE:": "结束日期：",
    "Download Selected Dataset": "下载所选数据集",
    "Ready": "就绪",
    "Set as Active Dataset": "设为当前数据集",
    "Delete Dataset": "删除数据集",
    "Cannot Delete": "无法删除",
    "Confirm Delete": "确认删除",
    "Error": "错误",
    "Download Error": "下载错误",
    "Dataset Download Complete": "数据集下载完成",
    "DOWNLOAD SUCCESSFUL": "下载成功",
    "DOWNLOADED (LIMITED DATA)": "已下载（数据有限）",
    "DOWNLOAD FAILED": "下载失败",
    "17Lands Connection Failed": "连接 17Lands 失败",
    "Loading Draft Log": "正在读取轮抓记录",
    "Loading Player.log": "正在读取 Player.log",
    "Queuing file...": "正在加入读取队列...",
    "Success": "成功",
    "Export Complete.": "导出完成。",
    "Loading Dataset...": "正在加载数据集...",
    "Processing dataset...": "正在处理数据集...",
    "Queuing Draft...": "正在加入轮抓读取队列...",
    "ADVISOR RECOMMENDATIONS": "抓牌建议",
}


_enabled = False
_REVERSE = {}


def set_language(enabled):
    global _enabled
    _enabled = bool(enabled)


def is_chinese():
    return _enabled


class RenderedText(str):
    def __new__(cls, value, english, chinese=None):
        obj = super().__new__(cls, value)
        obj.english = english
        obj.chinese = chinese
        return obj


def tr(text: str) -> str:
    if not isinstance(text, str):
        return text
    if isinstance(text, RenderedText) and text.chinese is not None:
        return RenderedText(text.chinese if _enabled else text.english,
                            text.english, text.chinese)
    original = text.english if isinstance(text, RenderedText) else _REVERSE.get(text, text)
    if not _enabled:
        return RenderedText(original, original)
    stripped = original.strip()
    translated = ZH.get(original, ZH.get(stripped, original))
    if translated == original:
        translated = _template_text(original)
    elif stripped != original and stripped in ZH:
        translated = original.replace(stripped, translated, 1)
    if translated != original:
        _REVERSE[translated] = original
    return RenderedText(translated, original)


COLUMN_HEADERS = {
    "name": "牌名",
    "value": "评分",
    "gihwr": "GIH WR",
    "ohwr": "OH WR",
    "gpwr": "GP WR",
    "alsa": "ALSA",
    "ata": "ATA",
    "iwd": "IWD",
    "wheel": "回轮",
    "colors": "颜色",
    "count": "数量",
    "tags": "定位",
}

COLUMN_DESCRIPTIONS = {
    "gihwr": "GIH WR：在手胜率",
    "ohwr": "OH WR：起手胜率",
    "gpwr": "GP WR：使用该牌的对局胜率",
    "alsa": "ALSA：平均最后见到顺位",
    "ata": "ATA：平均被抓顺位",
    "iwd": "IWD：抽到后胜率提升",
    "wheel": "回轮：预计能轮回来的概率",
    "colors": "颜色：卡牌颜色",
    "count": "数量：牌张总数",
    "value": "评分：Advisor 战术评分",
    "tags": "定位：卡牌角色",
}

TAG_LABELS = {
    "removal": "去除",
    "evasion": "规避",
    "fixing_ramp": "调色",
    "fixing": "调色",
    "2-drop": "二费曲线",
}

REASON_EXACT = {
    "TRUE BOMB (High IWD)": "真炸弹（高 IWD）",
    "Off-Color": "非主色",
    "Off-Color Gold": "非主色多色牌",
    "Curve Foundation": "曲线基础",
    "Counters Synergy": "指示物协同",
    "Artifact Synergy": "神器协同",
    "Graveyard Synergy": "坟场协同",
    "Critical: Needs Creatures": "关键需求：生物",
    "Critical: Needs Removal": "关键需求：去除",
    "Critical: Needs Fixing": "关键需求：调色",
    "Removal Saturated": "去除已充足",
    "Premium Fixing": "优质调色",
    "Enables Bomb Splash": "支持炸弹溅色",
    "Bomb Splash": "炸弹溅色",
    "Premium Removal Splash": "优质去除溅色",
    "Greedy Bomb Splash": "贪心炸弹溅色",
    "Uncastable (Double Pip)": "难以施放（双色点）",
    "Basic Land (Skip)": "基本地（跳过）",
    "This is the only available option.": "这是唯一可选项。",
    "Tactically superior for your pool": "更适合当前牌池",
}

ROLE_WORDS = {
    "Evasion": "规避",
    "Removal": "去除",
    "2-Drops": "二费曲线",
    "Creatures": "生物",
    "Fixing": "调色",
}

EVENT_LABELS = {
    "PremierDraft": "Premier 轮抓",
    "TradDraft": "传统轮抓",
    "TraditionalDraft": "传统轮抓",
    "QuickDraft": "快速轮抓",
    "Sealed": "现开",
    "TradSealed": "传统现开",
    "TraditionalSealed": "传统现开",
}

FILTER_LABELS = {
    "Auto": "自动",
    "All": "全部",
    "All Decks": "全部套牌",
    "No Data": "无数据",
}


def column_header(field: str, fallback: str = None) -> str:
    return COLUMN_HEADERS.get(field, fallback or str(field).upper()) if _enabled else (fallback or str(field).upper())


def column_description(field: str, fallback: str = None) -> str:
    return COLUMN_DESCRIPTIONS.get(field, fallback or column_header(field)) if _enabled else (fallback or column_header(field))


def advisor_tag(tag: str) -> str:
    return TAG_LABELS.get(tag, str(tag).capitalize()) if _enabled else str(tag).capitalize()


def _translate_role_words(text: str) -> str:
    for english, chinese in ROLE_WORDS.items():
        text = text.replace(english, chinese)
    return text


def advisor_reason(reason: str) -> str:
    if not reason or not _enabled:
        return reason
    if reason in REASON_EXACT:
        return REASON_EXACT[reason]
    if reason.startswith("Highly Replaceable "):
        role = _translate_role_words(reason.replace("Highly Replaceable ", "", 1))
        return f"高可替代：{role}"
    if reason.startswith("High VOR: Scarce "):
        rest = reason.replace("High VOR: Scarce ", "", 1)
        return f"高稀缺价值：{_translate_role_words(rest)}"
    if reason.startswith("Archetype Synergy"):
        return reason.replace("Archetype Synergy", "原型协同", 1)
    if reason.startswith("Improves Best Deck"):
        return reason.replace("Improves Best Deck", "提升最佳套牌", 1)
    return _translate_role_words(reason)


def display_card_name(name: str) -> str:
    if not name:
        return name
    return name if any(ord(ch) > 127 for ch in name) else name.upper()


def event_label(value: str) -> str:
    return EVENT_LABELS.get(value, value) if _enabled else value


def filter_label(value: str) -> str:
    return FILTER_LABELS.get(value, value) if _enabled else value


# Original identifiers stay English. These are display templates, not rules.
ZH.update({
    "Simplified Chinese display": "简体中文显示",
    "Chinese Display": "中文显示",
    "Reload Chinese Names": "重新读取中文卡名",
    "Curve Too Heavy": "高费牌过多",
    "Critical: Needs 2-Drops": "关键需求：二费曲线",
    "Splashable": "可以溅色",
    "LATE SIGNAL": "晚顺位颜色信号",
    "Waiting for draft...": "等待轮抽…",
    "Calculating tactical scores...": "正在计算选牌评分…",
    "Copy Deck": "复制套牌",
    "Export to Custom Deck": "转入自定义套牌",
    "Generate Decks": "生成构筑候选",
    "Suggest Deck": "推荐套牌",
    "Auto Lands": "自动配地",
    "Main Deck": "主牌",
    "Sideboard": "备牌",
    "Clear": "清空",
    "Analyze": "分析",
    "Cards": "卡牌",
    "Creatures": "生物",
    "Non-Creatures": "非生物",
    "Lands": "地",
    "Spells": "咒语",
    "Curve": "费用曲线",
    "Colors": "颜色",
    "Score": "评分",
    "Power": "强度",
    "Rating": "评分",
    "Name": "牌名",
    "Count": "数量",
    "Value": "评分",
    "Wheel": "回轮概率",
    "Tags": "定位",
    "Unknown": "未知",
    "Synchronizing...": "正在同步…",
    "Syncing with Arena...": "正在读取竞技场日志…",
    "▼ Hide Tabs": "▼ 隐藏标签页",
    "▲ Show Tabs": "▲ 显示标签页",
    "Card Details": "卡牌详情",
    "Select MTGA_Data Folder": "选择 MTGA_Data 文件夹",
    "All Decks": "全部套牌",
    "Win Rate": "胜率",
    "Percentile": "百分位",
    "Color": "颜色",
})
REASON_EXACT.update({k: ZH[k] for k in (
    "Curve Too Heavy", "Critical: Needs 2-Drops", "Splashable", "LATE SIGNAL")})

import re

REASON_TEMPLATES = [
    (r"Archetype Glue \(\+([\d.]+)\)", "原型关键衔接（+{0}）"),
    (r"Archetype Synergy \(\+([\d.]+)\)", "原型协同（+{0}）"),
    (r"Improves Best Deck \(\+([\d.]+)\)", "提升最佳套牌（+{0}）"),
    (r"High VOR: Scarce ([WUBRG]) (2-Drops|Removal|Evasion) \(\+([\d.]+)\)", "高稀缺价值：{0} {1}（+{2}）"),
    (r"ELITE PICK \(\+([-\d.]+)σ\)", "优质选择（+{0}σ）"),
    (r"Pack (\d+) Pick (\d+)", "第 {0} 包第 {1} 抓"),
    (r"Mana Flair: (.+)", "法术力主题：{0}"),
]


def _template_text(text):
    if text in REASON_EXACT:
        return REASON_EXACT[text]
    for pattern, template in REASON_TEMPLATES:
        match = re.fullmatch(pattern, text)
        if match:
            return template.format(*[ROLE_WORDS.get(g, g) for g in match.groups()])
    if text.endswith((" ▲", " ▼")):
        return tr(text[:-2]) + text[-2:]
    for pattern, template in UI_TEMPLATES:
        match = re.fullmatch(pattern, text)
        if match:
            return template.format(*[ZH.get(g, g) for g in match.groups()])
    if text in EVENT_LABELS:
        return EVENT_LABELS[text]
    if text in FILTER_LABELS:
        return FILTER_LABELS[text]
    if " | " in text:
        return " | ".join(tr(part) for part in text.split(" | "))
    if "\n" in text:
        return "\n".join(tr(line) for line in text.split("\n"))
    return text


# Wrap the original fixed dictionary with exhaustive upstream reason templates.
_dictionary_reason = advisor_reason


def advisor_reason(reason):
    if not _enabled:
        return reason
    translated = _template_text(reason)
    return translated if translated != reason else _dictionary_reason(reason)

ZH.update({
 'Advisor':'选牌建议','DECK ANALYTICS':'套牌分析','DECK BUILDER':'套牌构筑',
 'LIVE PACK: TACTICAL EVALUATION':'当前牌包：选牌分析','MAIN DECK (0)':'主牌（0）',
 'MONTE CARLO SIMULATION (10,000 Games)':'蒙特卡洛模拟（10,000 局）',
 'Pack':'牌包','Pool':'牌池','SEEN CARDS (WHEEL TRACKER)':'已见卡牌（回轮追踪）',
 'SIDEBOARD':'备牌','SIDEBOARD (0)':'备牌（0）','SIMULATION & SAMPLE HAND':'模拟与起手抽样',
 'STATS & ANALYSIS':'统计与分析','Stats':'统计','🏆 Draft Recap':'🏆 轮抽回顾',
 '📊 Mana & Curve':'📊 法术力与曲线','🧩 Synergy & Roles':'🧩 协同与定位',
 '(Auto: Detecting...)':'（自动：正在识别…）','17LANDS URL:':'17Lands 链接：',
 'ACTIVE DECK (0)':'当前套牌（0）','ADVISOR SUMMARY':'选牌建议摘要',
 'AI SUGGESTION:':'算法建议：','API Error':'数据接口错误','ARCHETYPE PLAY SHARE':'原型使用比例',
 'Add':'添加','Add All':'全部添加','Add Column':'添加列',
 'Allow all deleted or cleared datasets to download automatically again?':'允许重新自动下载已删除或清理的数据集吗？',
 'Application Update':'程序更新','Are you sure you want to delete the selected tier list(s)?':'确定删除所选梯度表吗？',
 'Auto-Lands':'自动配地','BALANCE':'平衡','CARD ROLES':'卡牌定位','COLOR REQUIREMENTS (PIPS)':'颜色需求（法术力符号）',
 'COMPOSITION':'构成','CONSISTENCY METRICS':'稳定性指标','CUSTOM LABEL (e.g. \'Pro Review\'):':'自定义标签（例如“专业评估”）：',
 'Clear Inactive Datasets':'清理非当前数据集','Colors (Filter)':'颜色（筛选）','Copied! ✔':'已复制 ✔',
 "Could not find 'Downloads/Raw' in the selected folder.\n\nPlease select the valid MTGA_Data folder.":'所选文件夹中找不到 Downloads/Raw。\n\n请选择有效的 MTGA_Data 文件夹。',
 'Could not reach Sealeddeck.tech automatically.\n\nYour deck has been copied to the clipboard. You can paste it manually at sealeddeck.tech.':'无法连接 Sealeddeck.tech。\n\n套牌已复制到剪贴板，可以手动粘贴到该网站。',
 'Could not save dataset exclusions. No files were removed.':'无法保存数据集排除列表，未删除文件。',
 'Could not save dataset preferences.':'无法保存数据集偏好设置。',
 'Creatures: 0\nSpells: 0\nLands: 0':'生物：0\n咒语：0\n地：0','Custom Builder':'自定义构筑',
 'DECK COMPOSITION':'套牌构成','Dataset Cleanup Incomplete':'数据集清理未完成','Dataset Missing':'缺少数据集',
 'Dataset Options:':'数据集选项：','Dataset is incomplete. Cannot generate pool.':'数据集不完整，无法生成牌池。',
 'Deck copied to clipboard in MTGA format!':'已将 MTGA 格式套牌复制到剪贴板。',
 'Deck has fewer than 7 cards.':'套牌不足 7 张。','Deck imported successfully!':'套牌导入成功。',
 'Deck must have 40 cards to analyze.':'套牌需要 40 张牌才能分析。','Delete':'删除','Delete Selected':'删除所选',
 'Delete all downloaded datasets?\n\nThe latest 17Lands data will be re-downloaded automatically the next time you start the app.\n\nDeleted or cleared datasets will remain excluded. To remove unwanted datasets permanently, cancel and use Clear Inactive Datasets or right-click a dataset and choose Delete Dataset.':'删除所有已下载数据集吗？\n\n下次启动时可自动重新下载最新的 17Lands 数据。\n\n已明确删除或清理的数据集仍保留排除状态。若要永久排除数据集，请取消并使用“清理非当前数据集”，或右键选择“删除数据集”。',
 'Deleted Datasets Restored':'已恢复被排除数据集','Deleted datasets are eligible for automatic downloads again. Restart the app with automatic dataset sync enabled to download them, or use Download Selected Dataset.':'已允许再次自动下载这些数据集。可启用自动同步后重启，或使用“下载所选数据集”。',
 'Download & Index Tier List':'下载并建立梯度表索引','Download In Progress':'正在下载','Draft Completed':'轮抽已完成',
 'Draw New Hand':'重新抽取起手','EXPORTING TO BROWSER...':'正在导出到浏览器…',
 "Ensure 'Detailed Logs (Plugin Support)' is checked in your MTGA Account Settings.":'请在 MTGA 账户设置中启用“详细日志（插件支持）”。',
 'Event Type':'赛制','Export Pool':'导出牌池','Export Successful':'导出成功','FILTER:':'筛选：','Filter:':'筛选：',
 'GENERATING SHELLS...':'正在生成构筑候选…','GLOBAL PERFORMANCE':'总体表现',
 'Generate a deck first.':'请先生成套牌。','Generate a deck to analyze.':'请先生成套牌，再进行分析。',
 'Generate a deck to run simulations.':'请先生成套牌，再运行模拟。','IMPORT NEW TIER LIST':'导入新梯度表',
 'IMPORTED TIER LISTS':'已导入梯度表','Image\nUnavailable':'图片\n暂不可用',
 'Import Error':'导入错误','Import Failed':'导入失败','Inactive Datasets Cleared':'已清理非当前数据集',
 'Initializing...':'正在初始化…','Invalid URL':'链接无效','Loading Draft':'正在读取轮抽',
 'Loading...':'正在加载…','MANA CURVE':'费用曲线','MASTER POOL (0)':'完整牌池（0）',
 'MTGA DRAFT TOOL':'MTGA 轮抽辅助','Missing Label':'缺少标签',
 'No 17Lands dataset is currently loaded. You need to download data before you can draft.':'尚未加载 17Lands 数据集。请先下载匹配赛制的数据。',
 'No Scryfall tags found for this set.':'未找到该系列的 Scryfall 标签。',
 'No valid MTGA format cards found in clipboard.':'剪贴板中未找到有效的 MTGA 格式卡牌。',
 'OPEN LANES':'开放颜色路线','POOL BALANCE':'牌池平衡','Partial Import':'部分导入',
 'Pool Power Grade: --':'牌池强度等级：--','Provide a label.':'请输入标签。','RISK FACTORS':'风险因素',
 'ROLES & SYNERGIES':'定位与协同','Reset Dataset Cache':'重置数据集缓存','Reset to Defaults':'恢复默认',
 'Restore Deleted Datasets':'恢复被排除数据集','SEALED STUDIO':'现开工作台','SEARCH:':'搜索：',
 'SEEN CARDS (WHEEL)':'已见卡牌（回轮）','Sealed Studio - MTGA Draft Tool':'现开工作台 — MTGA 轮抽辅助',
 'Select a Set to use for this session:':'选择本次练习使用的系列：','Set History Cleared':'已清理系列历史',
 'Set list not loaded. Please wait for the app to initialize.':'系列列表尚未加载，请等待初始化。',
 'Sort:':'排序：','Startup Error':'启动错误','Switch to List View':'切换列表视图',
 'Switch to Visual View':'切换卡图视图','TIME PERIOD:':'时间范围：',
 'There are no inactive datasets to clear.':'没有可清理的非当前数据集。',
 'Top 23 Cards Avg Win Rate: --%':'最强 23 张牌平均胜率：--%',
 'Use 17Lands URL.':'请使用 17Lands 链接。','User Group':'用户分组',
 'View Draft on 17Lands 🌐':'在 17Lands 查看轮抽 🌐',
 'Wait for the dataset download to finish before clearing data.':'请等待下载完成后再清理数据。',
 'Waiting for draft to begin...':'等待轮抽开始…','Waiting for pack data to appear in the log...':'等待日志出现牌包数据…',
 'Waiting...':'等待中…','You cannot delete the currently active dataset. Please double-click a different dataset to switch to it first.':'不能删除当前使用的数据集。请先双击其他数据集进行切换。',
 'You must have at least one deck variant.':'至少需要一个构筑候选。',
 '• MIN GAMES: The minimum amount of data required to show color-specific win rates.':'• 最低对局数：显示分颜色胜率所需的最小样本量。',
 "• USERS: 'All' pulls data from everyone. 'Top' pulls data exclusively from top players.":'• 用户分组：All 使用所有玩家数据；Top 只使用高水平玩家数据。',
 '⚔️ Enter Sealed Studio':'⚔️ 进入现开工作台','✅ Set as Active Dataset':'✅ 设为当前数据集',
 '✨ Personalize Your Experience':'✨ 调整界面偏好','🌐 Export to Sealeddeck.tech':'🌐 导出到 Sealeddeck.tech',
 '👁️ Switch to List View':'👁️ 切换列表视图','👁️ Switch to Visual View':'👁️ 切换卡图视图',
 '👋 Welcome to MTGA Draft Tool':'👋 欢迎使用 MTGA 轮抽辅助','📋 Copy MTGA Format':'📋 复制 MTGA 格式',
 '📥 Import Deck':'📥 导入套牌','🗑️ Delete Dataset':'🗑️ 删除数据集',
 '🤖 Auto-Generate Shells':'生成构筑候选','🤖 Auto-Optimize Deck':'优化构筑候选',
})

UI_TEMPLATES = [
    (r" \| Elapsed: (\d+)s", " | 已用时：{0} 秒"),
    (r"Collecting (.+) 17Lands Data", "正在读取 {0} 的 17Lands 数据"),
    (r"Downloading '(.+)' \((\d+)/(\d+)\) - (.+)", "正在下载 {0}（{1}/{2}） {3}"),
    (r"Harvesting Tags: '(.+)' \((\d+)/(\d+)\)", "正在读取卡牌定位：{0}（{1}/{2}）"),
    (r"GIH WR available: (\d+)/(\d+)", "在手胜率统计：{0}/{1}"),
    (r"MTGA Draft Tool v(.+)", "MTGA 轮抽辅助 v{0}"),
    (r"(MAIN DECK|SIDEBOARD|ACTIVE DECK|MASTER POOL) \((\d+)\)", "{0}（{1}）"),
    (r"MANA CURVE \(Avg CMC: ([\d.]+)\)", "费用曲线（平均法术力值：{0}）"),
    (r"Total Cards: (\d+)  \|  Creatures: (\d+)  \|  Non-Creatures: (\d+)  \|  Lands: (\d+)", "总张数：{0}  |  生物：{1}  |  非生物：{2}  |  地：{3}"),
    (r"Creatures: (\d+)\nSpells: (\d+)\nLands: (\d+)", "生物：{0}\n咒语：{1}\n地：{2}"),
    (r"Pool Power Grade: (.+)", "牌池强度等级：{0}"),
    (r"Top 23 Cards Avg Win Rate: (.+)%", "最强 23 张牌平均胜率：{0}%"),
]
ZH.update({"Initializing AI Builder...": "正在初始化构筑算法…", "Deep Scanning Log...": "正在深入扫描日志…", "Queuing Draft...": "正在排队读取轮抽…", "Loading Dataset...": "正在读取数据集…", "Processing dataset...": "正在处理数据集…", "Colorless": "无色", "Top": "高水平玩家", "(Missing Dataset)": "（缺少数据集）"})

ZH.update({"No matching dataset. Download this event in Datasets.": "缺少匹配赛制的数据集，请在数据集页下载。", "Loading event dataset...": "正在读取匹配赛制的数据集…", "MAIN DECK": "主牌", "SIDEBOARD": "备牌", "ACTIVE DECK": "当前套牌", "MASTER POOL": "完整牌池"})

ZH.update({
    'NAME':'牌名', 'VALUE':'评分', 'COLORS':'颜色', 'COUNT':'数量', 'TAGS':'定位',
    'WHEEL':'回轮', 'TYPES':'类别', 'CMC':'法术力值', 'RARITY':'稀有度',
    'GIH WR: Games in Hand Win Rate':'GIH WR：在手胜率',
    'OH WR: Opening Hand Win Rate':'OH WR：起手胜率',
    'GP WR: Games Played Win Rate':'GP WR：使用该牌的对局胜率',
    'ALSA: Average Last Seen At':'ALSA：平均最后见到顺位',
    'ATA: Average Taken At':'ATA：平均被抓顺位',
    'IWD: Improvement When Drawn':'IWD：抽到后胜率提升',
    'WHEEL: Probability of Wheeling':'回轮：预计能轮回来的概率',
    'COLORS: Card Colors':'颜色：卡牌颜色', 'COUNT: Total Card Count':'数量：牌张总数',
    'VALUE: Advisor Tactical Score':'评分：选牌算法战术评分', 'TAGS: Card Roles':'定位：卡牌角色',
    'No major steals detected.':'未发现明显的晚抓好牌。',
    'No premium staples drafted.':'尚未抓到优质常用牌。',
    'No non-basic lands drafted.':'尚未抓到非基本地。',
    'No Rares or Mythics drafted.':'尚未抓到稀有或秘稀牌。',
    'None Identified':'尚未识别', 'Creature':'生物', 'Planeswalker':'鹏洛客',
    'Battle':'战役', 'Instant':'瞬间', 'Sorcery':'法术', 'Enchantment':'结界',
    'Artifact':'神器', 'Land':'地',
})

ZH.update({"Searching Local Files":"正在查找本地卡牌数据", "Retrieving Localization Data":"正在校验英文原始数据", "Building Temporary Card Data File":"正在建立英文卡牌索引", "Retrieving Temporary Card Data":"正在读取英文卡牌索引", "Starting Deep Data Retrieval...":"正在读取 17Lands 各颜色统计…", "Finalizing Dataset...":"正在整理数据集…"})
