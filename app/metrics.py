

class Metrics():
    min_score = 0.0
    max_score = 1.0
    def __init__(self) -> None:
        self.name: str = ""
        self.weight: float = 0.125

    def get_latency(self):
        pass

    def calculate(self):
        return 