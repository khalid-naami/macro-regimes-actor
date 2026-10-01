# Cross-Asset Macro Regimes & Yield Premium Intelligence Actor

Institutional-grade quantitative macro model analyzing the **Copper/Gold Growth Proxy Ratio**, **10-Year & 30-Year Treasury Yield Regimes**, **OLS Linear Regression Implied Yields**, **Term-Premium Residuals (Rich vs Cheap $bp$)**, and **Rolling Gold Beta / Correlation Sensitivities**.

---

## 🏛️ Economic Rationale & Institutional Model

1. **Copper / Gold Ratio ($\frac{\text{Copper}}{\text{Gold}} \times 100$):**
   - **Copper (Doctor Copper):** Highly sensitive to global industrial production, manufacturing demand, and capital expenditures.
   - **Gold:** The ultimate monetary store of value and safe-haven asset responding to real yields and debt sustainability risks.
   - **The Ratio:** Represents the global benchmark for macroeconomic expansion vs risk-off deflationary pressure.

2. **10Y Yield OLS Regression & Term Premium:**
   - Linear regression of US 10-Year Benchmark Yields against the Copper/Gold Ratio over 1-Year and 2-Year rolling windows:
     $$\text{Implied } 10\text{Y Yield} = \alpha + \beta \cdot \left(\frac{\text{Copper}}{\text{Gold}} \times 100\right)$$
   - **Residual (Term Premium Spread):**
     $$\text{Residual } (bp) = \left(Y_{10\text{Y, Actual}} - Y_{10\text{Y, Implied}}\right) \times 100\text{ bp}$$
     - **Rich / Term Premium Surplus ($> +15\text{ bp}$):** Long-end yields are elevated above growth fundamentals (supply/deficit pressures, fiscal risk, or rate persistence).
     - **Cheap / Growth Discount ($< -15\text{ bp}$):** Yields are depressed relative to commodity growth signals (flight-to-quality or safe-haven demand).
     - **Fundamental Alignment:** Market rates are trading in fair-value equilibrium with global industrial demand.

3. **Gold Beta & Correlation to 30Y Treasury Yields:**
   - Evaluates gold's sensitivity to shifts in long-term discount rates:
     $$\beta_{\text{Gold}, 60d} = \frac{\text{Cov}(\Delta \% \text{Gold}, \Delta bp Y_{30})}{\text{Var}(\Delta bp Y_{30})}$$
   - **Rates-Reactor Mode ($\beta < -0.04$):** Standard monetary policy reaction (gold drops when long yields surge).
   - **Stagflation / Fiscal Credibility Hedge ($\beta > +0.02$):** Gold decouples from rates, rising alongside yields as an inflation and debt hedge.

---

## 📥 Input Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `period` | `String` | `"2y"` | Lookback window for regression and Z-score calculations (`1y`, `2y`, `3y`, `5y`, `10y`). |
| `goldSymbol` | `String` | `"GC=F"` | Gold ticker (Futures `GC=F` or ETF `GLD`). |
| `copperSymbol` | `String` | `"HG=F"` | Copper ticker (Futures `HG=F` or ETF `CPER`). |
| `includeHistoricalTimeSeries` | `Boolean` | `true` | Include full daily historical dataset records. |

---

## 📤 Output Structure

### 1. Default Dataset (Daily Overview)
```json
{
  "date": "2026-09-30",
  "copperGoldRatio": 0.1582,
  "ratioPercentile": 42.5,
  "actual10yYieldPct": 4.15,
  "implied10yYieldPct": 3.92,
  "residualBp": 23.0,
  "termPremiumStatus": "Rich (Surplus)",
  "actual30yYieldPct": 4.48,
  "goldPriceUsd": 2685.50,
  "copperPriceUsd": 4.2485,
  "goldBeta30y": 0.0315,
  "corr60d": 0.18,
  "macroRegimeSignal": "Rich (Surplus) | Gold Beta: +0.032"
}
```

### 2. Key-Value Store (`OUTPUT`)
Comprehensive JSON report with:
- **`currentRegimeSummary`**: Latest snapshot, ratio percentile, yield spreads, and regime classifications.
- **`regressionModels`**: 1-Year and 2-Year OLS regression formulas, slopes, intercepts, and $R^2$ goodness of fit.
- **`automatedMacroNarrative`**: Dynamic institutional commentary.

---

## 🎯 Institutional Use Cases

- **Asset Allocation & Fixed Income Positioning**: Identify when 10Y/30Y Treasuries are mispriced relative to global physical commodity demand.
- **Commodity & Precious Metals Trading**: Detect regime shifts where Gold transitions from a rates-sensitive asset to a fiscal debasement hedge.
- **Cross-Asset Macro Hedge Funds**: Systematic factor inputs for global macro models and risk parity portfolios.
