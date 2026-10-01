"""Quantitative Engine for Macro Regimes, OLS Regressions, Term-Premium Residuals & Beta Sensitivities."""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

class MacroRegimesEngine:
    """Computes cross-asset macro ratios, regressions, residuals, and rolling sensitivity metrics."""

    def analyze_regimes(self, raw_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Run complete macro regime analysis pipeline on daily price & yield series."""
        if raw_df is None or len(raw_df) < 30:
            logger.error("Insufficient data points for macro regime calculation.")
            return None

        try:
            df = raw_df.copy()

            # 1. Copper / Gold Ratio (Copper in $/lb vs Gold in $/oz scaled by 100)
            df['ratio'] = (df['copper'] / df['gold']) * 100.0

            # 2. Z-Scores over the lookback window
            df['gold_z'] = (df['gold'] - df['gold'].mean()) / (df['gold'].std() or 1.0)
            df['copper_z'] = (df['copper'] - df['copper'].mean()) / (df['copper'].std() or 1.0)
            df['y10_z'] = (df['y10'] - df['y10'].mean()) / (df['y10'].std() or 1.0)
            df['y30_z'] = (df['y30'] - df['y30'].mean()) / (df['y30'].std() or 1.0)
            df['ratio_z'] = (df['ratio'] - df['ratio'].mean()) / (df['ratio'].std() or 1.0)

            # 3. Daily returns and yield changes
            df['gold_ret_pct'] = df['gold'].pct_change() * 100.0
            df['copper_ret_pct'] = df['copper'].pct_change() * 100.0
            df['y10_chg_bp'] = df['y10'].diff() * 100.0  # 1 bp = 0.01%
            df['y30_chg_bp'] = df['y30'].diff() * 100.0

            # 4. Rolling Correlations (Gold Returns vs 30Y Yield Changes)
            df['corr_20d'] = df['gold_ret_pct'].rolling(20).corr(df['y30_chg_bp'])
            df['corr_60d'] = df['gold_ret_pct'].rolling(60).corr(df['y30_chg_bp'])

            # 5. OLS Regressions: 10Y Yield on Copper/Gold Ratio
            # 1-Year Fit (last 252 trading days)
            n_1y = min(len(df), 252)
            sub_1y = df.iloc[-n_1y:]
            slope_1y, intercept_1y, r_value_1y, p_value_1y, _ = stats.linregress(sub_1y['ratio'], sub_1y['y10'])
            r2_1y = float(r_value_1y ** 2)

            # 2-Year Fit (up to 504 trading days)
            n_2y = min(len(df), 504)
            sub_2y = df.iloc[-n_2y:]
            slope_2y, intercept_2y, r_value_2y, p_value_2y, _ = stats.linregress(sub_2y['ratio'], sub_2y['y10'])
            r2_2y = float(r_value_2y ** 2)

            df['implied_10y_1y'] = slope_1y * df['ratio'] + intercept_1y
            df['implied_10y_2y'] = slope_2y * df['ratio'] + intercept_2y

            # Residual in basis points: (Actual - Implied) * 100 bp
            df['residual_bp'] = (df['y10'] - df['implied_10y_1y']) * 100.0

            # 6. Gold Beta to 30Y Yield (% per bp, 60d rolling)
            cov_60 = df['gold_ret_pct'].rolling(60).cov(df['y30_chg_bp'])
            var_60 = df['y30_chg_bp'].rolling(60).var()
            df['gold_beta_60d'] = cov_60 / var_60.replace(0, np.nan)

            # Extract latest snapshot
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest

            cur_ratio = float(latest['ratio'])
            prev_ratio = float(prev['ratio'])
            ratio_pctile = float((df['ratio'] < cur_ratio).mean() * 100.0)

            actual_10y = float(latest['y10'])
            prev_10y = float(prev['y10'])
            implied_10y = float(latest['implied_10y_1y'])
            residual_bp = float(latest['residual_bp'])
            actual_30y = float(latest['y30'])
            gold_price = float(latest['gold'])
            copper_price = float(latest['copper'])

            gold_beta_60d = float(latest['gold_beta_60d']) if not np.isnan(latest['gold_beta_60d']) else 0.0
            corr_20d = float(latest['corr_20d']) if not np.isnan(latest['corr_20d']) else 0.0
            corr_60d = float(latest['corr_60d']) if not np.isnan(latest['corr_60d']) else 0.0

            # 7. Regime Status Classifications
            if residual_bp > 15.0:
                term_premium_status = "Rich (Term Premium Surplus)"
                regime_bias = "Fiscal/Supply Pressure on Long End"
            elif residual_bp < -15.0:
                term_premium_status = "Cheap (Growth Discount / Safe-Haven)"
                regime_bias = "Economic Growth Disconnect / Flight to Quality"
            else:
                term_premium_status = "Fundamental Alignment"
                regime_bias = "Yields Fairly Priced by Copper/Gold Proxy"

            if gold_beta_60d < -0.04:
                gold_regime = "Rates-Reactor Mode (Negative Beta to Yields)"
            elif gold_beta_60d > 0.02:
                gold_regime = "Stagflation / Fiscal Credibility Hedge (Decoupled from Yields)"
            else:
                gold_regime = "Neutral Sensitivity (Balanced Macro Drivers)"

            # 8. Generate Automated Institutional Macro Narrative
            narrative = []
            narrative.append(
                f"• Copper/Gold Ratio is at {cur_ratio:.4f} (Historical Percentile: P{ratio_pctile:.0f}), representing the current macro growth/inflation balance."
            )
            narrative.append(
                f"• Actual 10Y Yield ({actual_10y:.2f}%) vs 1Y Implied Model ({implied_10y:.2f}%): Yields are trading at a {residual_bp:+.1f} bp spread ({term_premium_status})."
            )
            narrative.append(
                f"• Gold Sensitivity to 30Y Yield: 60-day rolling beta is {gold_beta_60d:+.3f} %/bp with correlation {corr_60d:+.2f} ({gold_regime})."
            )

            # Build Historical Dataset Records
            records = []
            for idx, row in df.iterrows():
                dt_str = idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx)[:10]
                r_bp = float(row['residual_bp']) if not np.isnan(row['residual_bp']) else 0.0
                g_beta = float(row['gold_beta_60d']) if not np.isnan(row['gold_beta_60d']) else 0.0
                c_60 = float(row['corr_60d']) if not np.isnan(row['corr_60d']) else 0.0
                c_ratio = float(row['ratio'])

                row_status = "Rich (Surplus)" if r_bp > 15.0 else ("Cheap (Discount)" if r_bp < -15.0 else "Aligned")

                records.append({
                    "date": dt_str,
                    "copperGoldRatio": round(c_ratio, 4),
                    "ratioPercentile": round(float((df['ratio'] < c_ratio).mean() * 100.0), 1),
                    "actual10yYieldPct": round(float(row['y10']), 2),
                    "implied10yYieldPct": round(float(row['implied_10y_1y']), 2) if not np.isnan(row['implied_10y_1y']) else None,
                    "residualBp": round(r_bp, 1),
                    "termPremiumStatus": row_status,
                    "actual30yYieldPct": round(float(row['y30']), 2),
                    "goldPriceUsd": round(float(row['gold']), 2),
                    "copperPriceUsd": round(float(row['copper']), 4),
                    "goldBeta30y": round(g_beta, 4),
                    "corr60d": round(c_60, 2),
                    "macroRegimeSignal": f"{row_status} | Gold Beta: {g_beta:+.3f}"
                })

            summary = {
                "latestDate": df.index[-1].strftime("%Y-%m-%d") if hasattr(df.index[-1], 'strftime') else str(df.index[-1])[:10],
                "copperGoldRatio": round(cur_ratio, 4),
                "ratioPercentile": round(ratio_pctile, 1),
                "ratioChangePct": round(((cur_ratio - prev_ratio) / prev_ratio) * 100.0, 2) if prev_ratio > 0 else 0.0,
                "goldPriceUsd": round(gold_price, 2),
                "copperPriceUsd": round(copper_price, 4),
                "actual10yYieldPct": round(actual_10y, 2),
                "actual10yChangeBp": round((actual_10y - prev_10y) * 100.0, 1),
                "implied10yYieldPct": round(implied_10y, 2),
                "residualBp": round(residual_bp, 1),
                "termPremiumStatus": term_premium_status,
                "regimeBias": regime_bias,
                "actual30yYieldPct": round(actual_30y, 2),
                "goldBeta30y": round(gold_beta_60d, 4),
                "goldRegime": gold_regime,
                "correlation20d": round(corr_20d, 2),
                "correlation60d": round(corr_60d, 2)
            }

            regression_models = {
                "fit1Y": {
                    "lookbackTradingDays": n_1y,
                    "slope": round(float(slope_1y), 4),
                    "intercept": round(float(intercept_1y), 4),
                    "rSquared": round(r2_1y, 4),
                    "formula": f"Implied 10Y = {slope_1y:.4f} * (Cu/Au Ratio) + {intercept_1y:.4f}"
                },
                "fit2Y": {
                    "lookbackTradingDays": n_2y,
                    "slope": round(float(slope_2y), 4),
                    "intercept": round(float(intercept_2y), 4),
                    "rSquared": round(r2_2y, 4),
                    "formula": f"Implied 10Y = {slope_2y:.4f} * (Cu/Au Ratio) + {intercept_2y:.4f}"
                }
            }

            return {
                "summary": summary,
                "regressionModels": regression_models,
                "narrative": narrative,
                "records": records
            }

        except Exception as e:
            logger.error(f"Error executing macro regimes engine: {e}", exc_info=True)
            return None
