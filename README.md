# statusline

三行版 Claude Code 狀態列 — 純 Python stdlib，無外部依賴，跨平台可用。

> A three-line status line for [Claude Code](https://claude.com/claude-code), written in pure Python stdlib (no pip dependencies). Cross-platform.

## 預覽 / Preview

```
Claude Opus 4.6 200K v2.0.24 | my-repo (main) | +42 -18 lines | 3M 1A
●●●●●●●●●○○○○○○ 60% | $1.23 | 12m 34s | 5h 45% (1h 20m) | 7d 12%
cache 87% | in: 1.2M out: 45.3K | api wait 8m 12s (65%) | cur 18.2K in 156.4K read 892 write
```

**顯示內容**：

| 區段 | 項目 |
|------|------|
| L1 | 模型名 / context 窗格大小 / 版本 / repo 超連結 + 分支 / 新增刪除行數 / Git 狀態 (M/A/D) / 目前 agent / Vim 模式 |
| L2 | Context 使用進度條 / 費用 / 本次時長 / 5h 速率限制 % + 倒數 / 7d 速率限制 % + 倒數 |
| L3 | Cache hit rate / 累計 input/output tokens / API wait 時間佔比 / 當前 turn 的 cache 細節 |

顏色自動分級：≥80% 紅、≥50% 黃、<50% 綠。

## 特色

- **純 stdlib**：Python 3.8+ 即可，不需要 pip install
- **Windows 原生**：正確處理 UTF-8 輸出，不需要 jq 或 bash
- **資訊密度高**：3 行塞進 15+ 個即時指標
- **Repo 超連結**：支援 OSC 8 escape，點擊 repo 名直接開 GitHub 頁
- **Git 狀態整合**：自動偵測 branch / modified / added / deleted 檔案數
- **速率限制倒數**：5 小時 / 7 天額度的重置倒數

## 安裝

### 1. 取得腳本

```bash
# 方式 A：clone
git clone https://github.com/kira001210-lgtm/statusline.git
cp statusline/statusline.py ~/.claude/scripts/

# 方式 B：直接下載
curl -o ~/.claude/scripts/statusline.py https://raw.githubusercontent.com/kira001210-lgtm/statusline/main/statusline.py
```

> Windows Git Bash 的 `~` 指向 `C:\Users\<你的帳號>\`，`~/.claude/scripts/` 對應 `C:\Users\<你的帳號>\.claude\scripts\`。

### 2. 修改 Claude Code 設定

編輯 `~/.claude/settings.json`，加入 `statusLine` 區塊：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python C:/Users/<你的帳號>/.claude/scripts/statusline.py"
  }
}
```

**指令範例**（依平台選擇）：

| 平台 | command 寫法 |
|------|-------------|
| Windows（python 在 PATH） | `"python C:/Users/<帳號>/.claude/scripts/statusline.py"` |
| Windows（指定 Python） | `"C:/Users/<帳號>/AppData/Local/Programs/Python/Python312/python.exe C:/Users/<帳號>/.claude/scripts/statusline.py"` |
| macOS / Linux | `"python3 $HOME/.claude/scripts/statusline.py"` |

### 3. 重啟 Claude Code

下次開啟任何 session 就會看到三行狀態列。

## 客製化

所有視覺元素在腳本頂部：

- **顏色**：line 58-67 ANSI 常數
- **進度條寬度**：line 142 `BAR_W = 15`
- **百分比分級門檻**：line 70-73 `color_pct()`
- **時間格式**：line 75-81 `fmt_dur()`

刪掉不想看的指標：在 L1/L2/L3 建構段把對應行註解掉即可。

## 需求

- Python 3.8+（stdlib only）
- 終端機需支援 ANSI escape codes
- Git（可選 — 用於 branch/stats 顯示，沒有 git 也能跑，只是少幾個欄位）

## 為什麼另做一個？

原生 Claude Code 狀態列很精簡。這版針對**長時間、大量 context 使用**的重度使用者，把以下資訊直接 surface：

1. **看 cache hit rate** — 判斷是不是該 /clear 換新 session
2. **看 5h / 7d 額度** — 避免跑到一半被限流
3. **看 api wait %** — 判斷 bottleneck 是網路還是本地處理
4. **看 context 進度條** — 一眼估計還能聊多少輪

## 授權

MIT — 隨意使用、修改、散佈。
