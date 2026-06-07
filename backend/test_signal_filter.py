from signal_filter import RssiMedianFilter


def test_median_filter_uses_three_scan_window():
    filter_ = RssiMedianFilter(window_size=3)

    filter_.apply({"rssi_a": -50, "rssi_b": -60, "rssi_c": -70, "rssi_d": -80})
    filter_.apply({"rssi_a": -60, "rssi_b": -62, "rssi_c": -72, "rssi_d": -82})
    filtered = filter_.apply({"rssi_a": -70, "rssi_b": -64, "rssi_c": -74, "rssi_d": -84})

    assert filtered["rssi_a"] == -60
    assert filtered["rssi_b"] == -62
    assert filtered["rssi_c"] == -72
    assert filtered["rssi_d"] == -82


def test_carried_anchor_does_not_update_filter_history():
    filter_ = RssiMedianFilter(window_size=3)

    filter_.apply({"rssi_a": -50, "rssi_b": -60, "rssi_c": -70, "rssi_d": -80})
    carried = filter_.apply(
        {
            "rssi_a": -90,
            "rssi_b": -62,
            "rssi_c": -72,
            "rssi_d": -82,
            "carried": ["rssi_a"],
        }
    )
    filtered = filter_.apply({"rssi_a": -52, "rssi_b": -64, "rssi_c": -74, "rssi_d": -84})

    assert carried["rssi_a"] == -50
    assert filtered["rssi_a"] == -51
