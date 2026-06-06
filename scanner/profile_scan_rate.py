import argparse
import statistics
import time

from scanner import (
    ANCHOR_KEYS,
    DEFAULT_BACKEND_URL,
    apply_carry_forward,
    find_anchor_signals,
    get_wifi_interface,
    scan_wifi_networks,
)


WAIT_SECONDS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
TARGET_P90_LOOP_SECONDS = 1.0
MIN_ANCHOR_HIT_RATE = 0.9


def choose_recommended_wait(results):
    stable_results = [
        result
        for result in results
        if result["anchor_hit_rate"] >= MIN_ANCHOR_HIT_RATE
    ]

    for result in stable_results:
        if result["p90_loop_seconds"] <= TARGET_P90_LOOP_SECONDS:
            return result["wait"]

    if stable_results:
        return stable_results[0]["wait"]

    return None


def has_subsecond_recommendation(results, recommended_wait):
    if recommended_wait is None:
        return False

    for result in results:
        if result["wait"] == recommended_wait:
            return result["p90_loop_seconds"] <= TARGET_P90_LOOP_SECONDS

    return False


def profile_wait(interface, wait, samples):
    loop_seconds = []
    complete_count = 0
    carried_total = 0
    network_counts = []

    for _ in range(samples):
        started = time.perf_counter()
        networks = scan_wifi_networks(interface, wait)
        payload, _ = find_anchor_signals(networks)
        fresh_complete = all(payload[key] is not None for key in ANCHOR_KEYS)
        payload, carried = apply_carry_forward(payload)

        loop_seconds.append(time.perf_counter() - started)
        network_counts.append(len(networks))
        carried_total += len(carried)

        if fresh_complete:
            complete_count += 1

    return {
        "wait": wait,
        "samples": samples,
        "anchor_hit_rate": complete_count / samples,
        "carried_count": carried_total,
        "network_count_median": statistics.median(network_counts),
        "p50_loop_seconds": statistics.median(loop_seconds),
        "p90_loop_seconds": _percentile(loop_seconds, 90),
    }


def print_result(result):
    print(
        f"wait={result['wait']:.2f}s "
        f"hit={result['anchor_hit_rate']:.0%} "
        f"p50={result['p50_loop_seconds']:.2f}s "
        f"p90={result['p90_loop_seconds']:.2f}s "
        f"networks~{result['network_count_median']} "
        f"carried={result['carried_count']}"
    )


def main(argv=None):
    args = parse_args(argv)
    interface = get_wifi_interface()
    results = []

    print("Profiling Wi-Fi scan waits. Keep anchors on and stay near the demo area.")
    for wait in args.waits:
        result = profile_wait(interface, wait, args.samples)
        results.append(result)
        print_result(result)

    recommended = choose_recommended_wait(results)
    if recommended is None:
        print("\nNo wait met the 90% fresh-anchor rule. Use 1.0s as a safe starting point.")
        recommended = 1.0
    elif not has_subsecond_recommendation(results, recommended):
        print(
            "\nNo stable wait kept p90 loop time under 1.0s. "
            "Using the fastest reliable anchor hit rate."
        )

    print("\nRecommended fast-demo command:")
    print(
        "py scanner/scanner.py "
        f"--scan-wait {recommended} --interval 0 --quiet "
        f"--backend-url {args.backend_url}"
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Profile Windows Wi-Fi scan wait timing.")
    parser.add_argument("--samples", type=int, default=5, help="Scans per wait value.")
    parser.add_argument(
        "--waits",
        type=float,
        nargs="+",
        default=WAIT_SECONDS,
        help="Wait values to sweep.",
    )
    parser.add_argument(
        "--backend-url",
        default=DEFAULT_BACKEND_URL,
        help="URL to print in the recommended scanner command.",
    )
    return parser.parse_args(argv)


def _percentile(values, percentile):
    if not values:
        raise ValueError("values cannot be empty")

    ordered = sorted(values)
    index = (len(ordered) - 1) * (percentile / 100)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


if __name__ == "__main__":
    main()
