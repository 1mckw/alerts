# US AR/DR Touch Alerts

GitHub Pages 每小時掃描 **道瓊 30、納指 100、標普 500 指數及成分股** 日 K，輸出 AR/DR 與趨勢線觸碰報告。

## 線上報告

- HTML：https://1mckw.github.io/alerts/
- JSON：`/latest.json`

## 商品池

| 池 | 數量 | 說明 |
|----|------|------|
| **指數** | 3 | DJI30（`^DJI`）、NDX100（`^NDX`）、SP500（`^GSPC`） |
| **DJI30 成分** | 30 | 道瓊 30 成分股 |
| **NDX100 成分** | ~94 | 納指 100 成分股（與 DJI 重疊者歸 DJI30） |
| **SP500 成分** | ~393 | 標普 500 成分股（與 DJI/NDX 重疊者依優先序歸類） |

共 **520** 檔 × **1D** = **520** 掃描 jobs（去重後）。

週期：**1D** · 更新：每小時（UTC 整點）

| 週期 | 歷史 K | 圖表顯示 |
|------|--------|----------|
| 1D | 800 | 320 |

### AR/DR 晚觸碰門檻

| 週期 | 最少根數（信號後） |
|------|-------------------|
| 1D | 5 根（約一週） |

## AR/DR 規則

| | AR | DR |
|---|----|----|
| 觸發 | 急跌後反轉陽線 | 急漲後反轉陰線 |
| 射線 | 信號 K 上下引線各向右延伸，碰到即停 |
| 晚觸碰 | AR→上引線、DR→下引線，超過 5 根日 K 後 |

**趨勢線：** 至少 3 觸點；最多 2 條上升支撐 + 2 條下降阻力；觸點較少者圖上 50% 透明；急漲/跌貫穿 grace 2 根 K。

## 手動觸發

Repo → **Actions** → **Hourly US Alerts (DJI30 + NDX100)** → **Run workflow**

## 本機

```bash
python scan_signals.py
```

成分股清單：`universe.py` · SP500 來源：Wikipedia List of S&P 500 companies（`sp500_constituents.py`）
