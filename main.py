from card.engine import CardEngine
from minimalog.minimal_log import MinimalLog
ml = MinimalLog()

ml.log_event('starting program', announce=True)
ce = CardEngine()
ml.log_event('closing program', announce=True)
pass
