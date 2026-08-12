# DJI30 AR/DR Touch Alerts

GitHub Pages 每小時掃描 **道瓊 30（DJI30 / Yahoo `^DJI`）** 日 K，輸出 AR/DR 與趨勢線觸碰報告。

## 線上報告

- HTML：https://1mckw.github.io/alerts/
- JSON：`/latest.json`

首次請到 **Settings → Pages → Source: GitHub Actions**。

## 商品與週期

| 項目 | 值 |
|------|-----|
| 顯示名稱 | DJI30 |
| Yahoo 代碼 | `^DJI` |
| 週期 | 1D |
| 更新 | 每小時（UTC 整點） |

## AR/DR 規則

| | AR | DR |
|---|----|----|
| 觸發 | 急跌後反轉陽線 | 急漲後反轉陰線 |
| 射線 | 信號 K 上下引線各向右延伸，碰到即停 |
| 晚觸碰 | AR→上引線、DR→下引線，超過 5 根日 K 後 |

**趨勢線：** 至少 3 觸點；急漲/跌貫穿 grace 2 根 K。

## 手動觸發

Repo → **Actions** → **Hourly DJI30 Alerts** → **Run workflow**

## 本機

```bash
python scan_signals.py
```

輸出：`signals/latest.html`、`signals/latest.json`
