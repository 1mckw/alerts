# US AR/DR Touch Alerts

GitHub Pages 每小時掃描 **道瓊 30、納指 100 指數及成分股** 日 K，輸出 AR/DR 與趨勢線觸碰報告。

## 線上報告

- HTML：https://1mckw.github.io/alerts/
- JSON：`/latest.json`

## 商品池

| 池 | 數量 | 說明 |
|----|------|------|
| **指數** | 2 | DJI30（`^DJI`）、NDX100（`^NDX`） |
| **DJI30 成分** | 30 | 道瓊 30 成分股 |
| **NDX100 成分** | ~102 | 納指 100 成分股（與 DJI 重疊者歸類為 DJI30） |

週期：**1D** · 更新：每小時（UTC 整點）

## AR/DR 規則

| | AR | DR |
|---|----|----|
| 觸發 | 急跌後反轉陽線 | 急漲後反轉陰線 |
| 射線 | 信號 K 上下引線各向右延伸，碰到即停 |
| 晚觸碰 | AR→上引線、DR→下引線，超過 5 根日 K 後 |

**趨勢線：** 至少 3 觸點；急漲/跌貫穿 grace 2 根 K。

## 手動觸發

Repo → **Actions** → **Hourly US Alerts (DJI30 + NDX100)** → **Run workflow**

## 本機

```bash
python scan_signals.py
```

成分股清單：`universe.py`（NDX100 來源：slickcharts.com/nasdaq100）
