
"""Detect large market orders sweeping multiple price levels."""


class WhaleDetector:
    def __init__(self, quantity_threshold=1000, level_threshold=2):
        if quantity_threshold <= 0:
            raise ValueError("Quantity threshold must be positive")

        if level_threshold <= 0:
            raise ValueError("Level threshold must be positive")

        self.quantity_threshold = quantity_threshold
        self.level_threshold = level_threshold

        self.total_detected = 0

    def detect(self, trades, incoming_side):
        """Detect large orders consuming multiple price levels."""

        if incoming_side not in (0, 1):
            raise ValueError("Side must be 0 (BUY) or 1 (SELL)")

        if not trades:
            return None

        try:
            total_quantity = sum(
                trade[3] for trade in trades
            )

            execution_prices = [
                trade[2] for trade in trades
            ]

        except (IndexError, TypeError) as exc:
            raise ValueError("Invalid trade format") from exc

        if total_quantity <= 0:
            return None

        levels_cleared = len(set(execution_prices))

        if (
            total_quantity < self.quantity_threshold
            or levels_cleared < self.level_threshold
        ):
            return None

        self.total_detected += 1

        return {
            "type": "WHALE_ORDER",
            "side": "BUY" if incoming_side == 0 else "SELL",
            "total_quantity": total_quantity,
            "levels_cleared": levels_cleared,
            "execution_prices": execution_prices,
            "trade_count": len(trades),
            "alert_number": self.total_detected,
        }
