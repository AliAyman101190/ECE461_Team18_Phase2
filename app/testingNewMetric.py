import logging
from submetrics import ReproducibilityMetric

# Configure logging for normal (non-debug) output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


def run_test_case(name: str, model_info: dict):
    """
    Run a reproducibility test case and show summarized results.
    """
    logger.info("=" * 10 + f" Running test: {name} " + "=" * 10)

    metric = ReproducibilityMetric()
    score = metric.calculate_metric(model_info)
    latency = metric.calculate_latency()

    logger.info(f"Result for '{name}': Score = {score}, Latency = {latency} ms\n")
    print(f"\n>>> {name} | Score: {score:.2f} | Latency: {latency} ms <<<\n")


if __name__ == "__main__":
    logger.info("Initializing ReproducibilityMetric test harness...")

    # ------------------------------------------------------------------
    # Case 0 — No code snippet
    # ------------------------------------------------------------------
    model_info_0 = {
        "readme": "This model predicts cats vs dogs. No code provided.",
    }
    run_test_case("Case 0.0 (No Code)", model_info_0)

    # ------------------------------------------------------------------
    # Case 1 — Incomplete / Broken snippet (expected ~0.5)
    # ------------------------------------------------------------------
    model_info_1 = {
        "readme": """
        ## Example
        ```python
        import torch
        model = MyModel()
        model.train()
        ```
        """,
    }
    run_test_case("Case 0.5 (Partial / Needs Fixes)", model_info_1)

    # ------------------------------------------------------------------
    # Case 2 — Fully runnable snippet (expected 1.0)
    # ------------------------------------------------------------------
    model_info_2 = {
        "readme": """
        ## Example
        ```python
        print("Hello world — reproducible example")
        ```
        """,
    }
    run_test_case("Case 1.0 (Runs Without Debugging)", model_info_2)

    # ------------------------------------------------------------------
    # Case 3 — Mixed snippets (should pick the highest score)
    # ------------------------------------------------------------------
    model_info_3 = {
        "readme": """
        ## Example 1 (broken)
        ```python
        import torchx
        model = MyModel()
        ```

        ## Example 2 (good)
        ```python
        print("Hi, reproducibility works!")
        ```
        """,
    }
    run_test_case("Case 3.0 (Mixed Snippets)", model_info_3)

    logger.info("All reproducibility test cases completed.")
