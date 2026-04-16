# statusline

三行版 Claude Code 狀態列 — 純 Python stdlib，無外部依賴，跨平台可用。

> 參考自 **YAHA 學堂**。

## 預覽

```
Claude Opus 4.6 200K v2.0.24 | my-repo (main) | +42 -18 lines | 3M 1A
●●●●●●●●●○○○○○○ 60% | $1.23 | 12m 34s | 5h 45% (1h 20m) | 7d 12%
cache 87% | in: 1.2M out: 45.3K | api wait 8m 12s (65%) | cur 18.2K in 156.4K read 892 write
```

## 顯示內容

| 區段 | 項目 |
|------|------|
| L1 | 模型名 / context 窗格大小 / 版本 / repo 超連結 + 分支 / 新增刪除行數 / Git 狀態 (M/A/D) / 目前 agent / Vim 模式 |
| L2 | Context 使用進度條 / 費用 / 本次時長 / 5h 速率限制 % + 倒數 / 7d 速率限制 % + 倒數 |
| L3 | Cache hit rate / 累計 input/output tokens / API wait 時間佔比 / 當前 turn 的 cache 細節 |

顏色自動分級：≥80% 紅、≥50% 黃、<50% 綠。

---

# 安裝教學（給 Claude Code 自己看的 SOP）

> 這段為讓另一台機器上的 Claude Code agent 直接按步驟執行而寫。每一步都是具體指令 + 驗證方式。

## Step 0 — 偵測環境

先決定你是哪個平台，後面路徑寫法會不同。

```bash
# 偵測平台
uname -s 2>/dev/null || echo "Windows"
```

- `MINGW*` / `MSYS*` / 輸出 `Windows` → 走「Windows Git Bash」路線
- `Darwin` → macOS
- `Linux` → Linux

確認 Python 版本 ≥ 3.8：

```bash
python --version 2>/dev/null || python3 --version
```

如果沒有 python 在 PATH，找一下實際路徑：

```bash
# Windows 常見位置
ls "C:/Users/$USER/AppData/Local/Programs/Python/" 2>/dev/null
ls "C:/Users/$USER/AppData/Local/Python/" 2>/dev/null

# macOS / Linux
which python3
```

## Step 1 — 下載腳本

放到 `~/.claude/scripts/statusline.py`：

```bash
# 確認目錄存在
mkdir -p ~/.claude/scripts

# 下載
curl -fsSL -o ~/.claude/scripts/statusline.py \
  https://raw.githubusercontent.com/kira001210-lgtm/statusline/main/statusline.py

# 驗證下載成功（應該看到 ~9.7KB 檔案）
ls -l ~/.claude/scripts/statusline.py
```

驗證腳本能跑：

```bash
echo '{}' | python ~/.claude/scripts/statusline.py
```

看到 3 行輸出（可能帶 ANSI 顏色碼，有模型名「Claude」預設值）就是正常。如果跳 error，先檢查 Python 版本。

## Step 2 — 寫入 Claude Code 設定

編輯 `~/.claude/settings.json`，加入 `statusLine` 區塊。

### 情境 A：settings.json 已存在

讀取當前內容：

```bash
cat ~/.claude/settings.json
```

把下面這段合併進去（放在最外層大括號內）：

```json
"statusLine": {
  "type": "command",
  "command": "<你的 command 字串>"
}
```

`<你的 command 字串>` 依平台填：

| 平台 | command 寫法 |
|------|-------------|
| **Windows（python 在 PATH）** | `python C:/Users/<帳號>/.claude/scripts/statusline.py` |
| **Windows（python 不在 PATH）** | `C:/Users/<帳號>/AppData/Local/Programs/Python/Python312/python.exe C:/Users/<帳號>/.claude/scripts/statusline.py` |
| **macOS / Linux** | `python3 $HOME/.claude/scripts/statusline.py` |

取得當前使用者帳號：

```bash
# Windows
echo $USERNAME
# macOS / Linux
echo $USER
```

### 情境 B：settings.json 不存在

建立最小版：

```bash
cat > ~/.claude/settings.json <<'EOF'
{
  "statusLine": {
    "type": "command",
    "command": "python C:/Users/__REPLACE_ME__/.claude/scripts/statusline.py"
  }
}
EOF
```

再用 `sed` 換掉 placeholder：

```bash
# Windows Git Bash
sed -i "s|__REPLACE_ME__|$USERNAME|g" ~/.claude/settings.json

# macOS / Linux
sed -i "s|python C:/Users/__REPLACE_ME__/.claude/scripts/statusline.py|python3 $HOME/.claude/scripts/statusline.py|" ~/.claude/settings.json
```

## Step 3 — 驗證設定 JSON 合法

```bash
python -c "import json; json.load(open('$HOME/.claude/settings.json')); print('OK')"
```

看到 `OK` 就是有效 JSON；看到 `JSONDecodeError` 要手動修。

## Step 4 — 重啟 Claude Code

```bash
# 關掉現有 session 後重開
claude
```

重啟後 prompt 底下應該出現 3 行資訊。如果沒有，檢查：

```bash
# 手動跑腳本確認沒壞
echo '{"model":{"display_name":"Test"},"workspace":{"current_dir":"."}}' | \
  python ~/.claude/scripts/statusline.py
```

## Step 5（可選）— 更新腳本

之後上游有改，重跑 Step 1 的 curl 覆蓋即可。

---

# 疑難排解

| 症狀 | 原因 | 解法 |
|------|------|------|
| 狀態列沒出現 | `settings.json` 格式錯 | 跑 Step 3 的 JSON 驗證 |
| 狀態列亂碼 | 終端機不支援 ANSI | 換支援 ANSI 的終端機（Windows Terminal、iTerm2） |
| 中文變問號 | Windows 終端機編碼不是 UTF-8 | `chcp 65001` 切成 UTF-8 |
| `python: command not found` | Python 不在 PATH | 用完整路徑（見 Step 2 表格） |
| Git 欄位沒顯示 | 當前目錄不是 git repo | 正常，該欄位會自動隱藏 |

# 客製化

所有視覺元素在腳本頂部，直接編輯 `~/.claude/scripts/statusline.py`：

- **顏色**：line 58-67 ANSI 常數
- **進度條寬度**：line 142 `BAR_W = 15`
- **百分比分級門檻**：line 70-73 `color_pct()`

刪掉不想看的指標：在 L1/L2/L3 建構段把對應行註解掉即可。

# 需求

- Python 3.8+（stdlib only）
- 終端機需支援 ANSI escape codes
- Git（可選，沒裝也能跑，只是少 branch/stats 欄位）

# 為什麼另做一個？

原生 Claude Code 狀態列很精簡。這版針對**長時間、大量 context 使用**的重度使用者，把以下資訊直接 surface：

1. **Cache hit rate** — 判斷是不是該 `/clear` 換新 session
2. **5h / 7d 額度倒數** — 避免跑到一半被限流
3. **API wait %** — 判斷 bottleneck 是網路還是本地處理
4. **Context 進度條** — 一眼估計還能聊多少輪

# 來源

本狀態列的概念與實作參考自 **YAHA 學堂**（Claude Code 學習社群資源）。

# 授權

MIT — 隨意使用、修改、散佈。
