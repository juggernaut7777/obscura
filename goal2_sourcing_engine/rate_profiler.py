"""
Rate Limit Profiler — Find the exact safe threshold for Google Flow
====================================================================
Uses the ALREADY-LIMITED account to systematically test how many
generations can be done at different intervals before triggering
a 403/rate limit.

Results tell us the EXACT safe spacing for the production account.

Usage:
    python rate_profiler.py --test-interval 300   # Test 5-min spacing
    python rate_profiler.py --burst 5              # Rapid burst of 5
    python rate_profiler.py --analyze              # Show all test results
"""
import json
import time
import os
import sys
import requests

BRIDGE_URL = "http://127.0.0.1:9877"
RESULTS_FILE = "rate_limit_results.json"

TEST_PROMPT = (
    "Simple photo of a plain white t-shirt on a wooden hanger against a grey wall. "
    "Natural lighting, clean composition, product photography."
)


def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return {"tests": [], "findings": {}}


def save_results(data):
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def test_single_generation():
    """Send one generation request and return the result."""
    start = time.time()
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/generate",
            json={"prompt": TEST_PROMPT},
            timeout=120
        )
        elapsed = time.time() - start
        return {
            "status": resp.status_code,
            "success": resp.status_code == 200,
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "response_snippet": resp.text[:200] if resp.status_code != 200 else "OK",
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "status": 0,
            "success": False,
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "response_snippet": str(e)[:200],
        }


def run_interval_test(interval_seconds: int, count: int = 5):
    """Test a specific interval between generations."""
    results = load_results()
    test_name = f"interval_{interval_seconds}s_x{count}"

    print(f"\n{'='*50}")
    print(f"  RATE LIMIT TEST: {interval_seconds}s interval, {count} generations")
    print(f"  Total time: ~{(interval_seconds * count) / 60:.1f} minutes")
    print(f"{'='*50}")

    test_results = []
    successes = 0
    failures = 0

    for i in range(1, count + 1):
        print(f"\n  [{i}/{count}] Generating...")
        result = test_single_generation()
        test_results.append(result)

        if result["success"]:
            successes += 1
            print(f"  OK ({result['elapsed_seconds']}s)")
        else:
            failures += 1
            print(f"  FAILED: {result['status']} - {result['response_snippet'][:80]}")
            # If we get a 403, log it and stop
            if result["status"] == 403:
                print(f"\n  403 DETECTED at generation #{i}!")
                print(f"  The limit at {interval_seconds}s spacing is approximately {i-1} generations.")
                break

        # Wait for next attempt (except after last one)
        if i < count:
            print(f"  Waiting {interval_seconds}s...")
            time.sleep(interval_seconds)

    # Save results
    results["tests"].append({
        "test_name": test_name,
        "interval_seconds": interval_seconds,
        "attempted": len(test_results),
        "successes": successes,
        "failures": failures,
        "success_rate": round(successes / len(test_results) * 100, 1),
        "results": test_results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_results(results)

    print(f"\n  RESULT: {successes}/{len(test_results)} succeeded ({successes/len(test_results)*100:.0f}%)")
    return successes, failures


def run_burst_test(count: int = 5):
    """Rapid-fire burst test with no delay between generations."""
    return run_interval_test(interval_seconds=5, count=count)


def analyze_results():
    """Analyze all test results to find the safe threshold."""
    results = load_results()
    if not results["tests"]:
        print("No test results found. Run some tests first.")
        return

    print(f"\n{'='*60}")
    print(f"  RATE LIMIT ANALYSIS — {len(results['tests'])} tests recorded")
    print(f"{'='*60}")

    for test in results["tests"]:
        status = "SAFE" if test["success_rate"] == 100 else "RISKY" if test["success_rate"] > 50 else "BLOCKED"
        emoji = {"SAFE": "  ", "RISKY": "  ", "BLOCKED": "  "}[status]
        print(f"\n  {emoji} {test['test_name']}")
        print(f"     Interval: {test['interval_seconds']}s | Attempted: {test['attempted']} | Success: {test['success_rate']}%")
        print(f"     Verdict: {status}")

    # Find the safest interval
    safe_tests = [t for t in results["tests"] if t["success_rate"] == 100]
    if safe_tests:
        safest = max(safe_tests, key=lambda t: t["attempted"])
        print(f"\n  RECOMMENDATION: {safest['interval_seconds']}s interval is SAFE")
        print(f"  ({safest['attempted']} generations at 100% success rate)")
    else:
        print(f"\n  WARNING: No fully safe interval found yet. Need more testing.")


if __name__ == "__main__":
    if "--analyze" in sys.argv:
        analyze_results()
    elif "--burst" in sys.argv:
        idx = sys.argv.index("--burst")
        count = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 5
        run_burst_test(count)
    elif "--test-interval" in sys.argv:
        idx = sys.argv.index("--test-interval")
        interval = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 300
        count = 5
        if "--count" in sys.argv:
            cidx = sys.argv.index("--count")
            count = int(sys.argv[cidx + 1])
        run_interval_test(interval, count)
    else:
        print("Usage:")
        print("  python rate_profiler.py --test-interval 300        # Test 5-min spacing")
        print("  python rate_profiler.py --test-interval 600 --count 10  # Test 10-min, 10 gens")
        print("  python rate_profiler.py --burst 5                  # Rapid burst of 5")
        print("  python rate_profiler.py --analyze                  # Show all results")
