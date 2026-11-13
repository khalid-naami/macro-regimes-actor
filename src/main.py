"""Main entrypoint for the Cross-Asset Macro Regimes Actor."""

import asyncio
import logging
import math
import sys
from datetime import datetime, timezone
from typing import Dict, Any, List
from apify import Actor

from src.data_engine import MacroDataEngine
from src.regimes_engine import MacroRegimesEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("macro-regimes-actor")


def sanitize_record(obj: Any) -> Any:
    """Recursively strip None and non-finite floats before pushing to Apify dataset."""
    if obj is None:
        return None
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, list):
        return [v for v in (sanitize_record(x) for x in obj) if v is not None]
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            sv = sanitize_record(v)
            if sv is not None:
                clean[k] = sv
        return clean
    return obj


async def main() -> None:
    """Actor main execution routine."""
    async with Actor:
        actor_input = await Actor.get_input() or {}

        period = str(actor_input.get("period", "2y")).strip().lower()
        gold_symbol = str(actor_input.get("goldSymbol", "GC=F")).strip()
        copper_symbol = str(actor_input.get("copperSymbol", "HG=F")).strip()
        include_history = bool(actor_input.get("includeHistoricalTimeSeries", True))

        logger.info("Starting Cross-Asset Macro Regimes Actor...")
        logger.info(f"Configuration: period={period}, gold={gold_symbol}, copper={copper_symbol}")

        data_engine = MacroDataEngine(gold_symbol=gold_symbol, copper_symbol=copper_symbol)
        regimes_engine = MacroRegimesEngine()

        # 1. Fetch data
        raw_df = data_engine.fetch_regime_data(period=period)
        if raw_df is None or raw_df.empty:
            logger.error("Failed to load cross-asset macro market data. Aborting.")
            await Actor.fail(status_message="Failed to load cross-asset macro market data.")
            return

        # 2. Run Quant Pipeline
        results = regimes_engine.analyze_regimes(raw_df)
        if not results or not results.get("records"):
            logger.error("Macro regime analysis failed to compute.")
            await Actor.fail(status_message="Macro regime analysis failed to compute any records.")
            return

        summary = results["summary"]
        regression_models = results["regressionModels"]
        narrative = results["narrative"]
        records = [sanitize_record(r) for r in results["records"]]
        records = [r for r in records if r]

        if not records:
            await Actor.fail(status_message="Macro regime analysis produced 0 valid records.")
            return

        # 3. Push to Apify Default Dataset
        if include_history:
            logger.info(f"Pushing {len(records)} daily records to Apify dataset...")
            await Actor.push_data(records)
        else:
            # Push only latest snapshot
            await Actor.push_data([records[-1]])

        # 4. Save comprehensive report to Key-Value Store (OUTPUT)
        output_payload = {
            "title": "Institutional Cross-Asset Macro Regimes & Yield Premium Report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lookbackPeriod": period,
            "currentRegimeSummary": summary,
            "regressionModels": regression_models,
            "automatedMacroNarrative": narrative,
            "latestMetrics": records[-1] if records else {}
        }
        await Actor.set_value("OUTPUT", output_payload)

        logger.info(
            f"Macro Regimes Actor completed successfully! Latest Cu/Au Ratio: {summary['copperGoldRatio']} "
            f"(P{summary['ratioPercentile']}), 10Y Yield Spread: {summary['residualBp']:+.1f} bp ({summary['termPremiumStatus']})."
        )


if __name__ == "__main__":
    asyncio.run(main())
