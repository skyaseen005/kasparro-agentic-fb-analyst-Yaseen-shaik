#!/usr/bin/env python3
"""
Kasparro Agentic FB Analyst - Main Orchestration Script
Usage: python run.py "Analyze ROAS drop"
"""

import sys
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.orchestrator.workflow import AgenticWorkflow
from src.utils.logger import setup_logger
from src.utils.data_loader import DataLoader


def main():

    parser = argparse.ArgumentParser(
        description="Agentic Facebook Ads Performance Analyst"
    )

    parser.add_argument(
        "query",
        type=str,
        help="Analysis query (e.g., 'Why did ROAS drop?')"
    )

    parser.add_argument(
        "--data-path",
        type=str,
        default="data/sample_fb_ads.csv",
        help="Path to Facebook Ads CSV file"
    )

    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use example dataset"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for results"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logger()

    logger.info("=" * 80)
    logger.info("KASPARRO AGENTIC FB ANALYST - START")
    logger.info("=" * 80)
    logger.info(f"Query: {args.query}")
    logger.info(f"Data Path: {args.data_path}")
    logger.info(f"Config: {args.config}")

    try:
        # Initialize workflow
        workflow = AgenticWorkflow(config_path=args.config)

        # Load dataset
        logger.info("\n[STEP 1] Loading data...")
        data_loader = DataLoader(args.data_path)
        df = data_loader.load()
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")

        # Run agentic workflow
        logger.info("\n[STEP 2] Running agentic workflow...")
        results = workflow.run(query=args.query, data=df)

        # Save results
        logger.info("\n[STEP 3] Saving outputs...")

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        insights_path = output_dir / "insights.json"
        creatives_path = output_dir / "creatives.json"
        report_path = output_dir / "report.md"

        # Save insights JSON
        with open(insights_path, "w", encoding="utf-8") as f:
            json.dump(results["insights"], f, ensure_ascii=False, indent=2)

        # Save creative recommendations
        with open(creatives_path, "w", encoding="utf-8") as f:
            json.dump(results["creatives"], f, ensure_ascii=False, indent=2)

        # Save markdown report
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(results["report"])

        # Terminal summary
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print(f"\n📊 Insights saved: {insights_path}")
        print(f"💡 Creative recommendations saved: {creatives_path}")
        print(f"📄 Full analysis report saved: {report_path}")
        print("\nView all results in the 'reports/' directory")
        print("=" * 80)

        logger.info("\n" + "=" * 80)
        logger.info("KASPARRO AGENTIC FB ANALYST - SUCCESS")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
        print(f"\n❌ Analysis failed: {str(e)}")
        print("Check logs/ directory for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
