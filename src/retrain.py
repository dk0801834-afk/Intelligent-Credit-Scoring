"""
Background retraining manager.

When the number of new (untrained) user submissions reaches RETRAIN_THRESHOLD,
a background daemon thread retrains the model without blocking the UI. A simple
file lock prevents concurrent training runs. The UI can poll `get_status()`.
"""
import threading
import datetime as dt

from . import config, model, database

_lock = threading.Lock()
_state = {
    "training": False,
    "last_started": None,
    "last_finished": None,
    "last_metrics": None,
    "last_error": None,
    "trigger": None,
}


def is_training() -> bool:
    return _state["training"]


def get_status() -> dict:
    return dict(_state)


def _run(trigger: str):
    try:
        _state["training"] = True
        _state["last_started"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _state["last_error"] = None
        _state["trigger"] = trigger
        metrics = model.train(trigger=trigger)
        _state["last_metrics"] = metrics
        _state["last_finished"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:  # pragma: no cover
        _state["last_error"] = str(e)
    finally:
        _state["training"] = False
        _lock.release()


def trigger_retrain(trigger: str = "manual") -> bool:
    """Start a non-blocking retrain. Returns False if one is already running."""
    if not _lock.acquire(blocking=False):
        return False
    t = threading.Thread(target=_run, args=(trigger,), daemon=True)
    t.start()
    return True


def maybe_retrain() -> bool:
    """Auto-trigger a background retrain if enough new data has accrued."""
    try:
        pending = database.count_untrained()
    except Exception:
        return False
    if pending >= config.RETRAIN_THRESHOLD and not is_training():
        return trigger_retrain(trigger=f"auto ({pending} new records)")
    return False
