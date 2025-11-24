import numpy as np


def calculate_linear_regression(
    x_values: list[float], y_values: list[float]
) -> tuple[float, float]:
    """
    Calculate linear regression coefficients using least squares method.

    Args:
        x_values: voltage values
        y_values: pressure values

    Returns:
        tup [float, float]: (slope, intercept) where y = slope * x + intercept

    Raises:
        ValueError: If input arrays have different lengths, or have less than 2 entries
    """
    if len(x_values) != len(y_values):
        raise ValueError(
            f"Input arrays must have same length. "
            f"Got x_values: {len(x_values)}, y_values: {len(y_values)}"
        )

    if len(x_values) == 0 or len(y_values) == 0:
        raise ValueError("Input arrays cannot be empty")

    if len(x_values) < 2 or len(y_values) < 2:
        raise ValueError("At least 2 data points required for linear regression")

    x_array = np.asarray(x_values, dtype=float)
    y_array = np.asarray(y_values, dtype=float)

    slope, intercept = np.polyfit(x_array, y_array, 1)

    return float(np.round(slope, decimals=15)), float(np.round(intercept, decimals=5))
