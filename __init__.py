"""matrix-context: a mention-only Matrix bot that still knows what was said in the room."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from . import context_store as cs

logger = logging.getLogger(__name__)


def register(ctx) -> None:
    settings = cs.Settings.from_env(dict(os.environ))
    problems = settings.problems()
    if problems:
        logger.warning("matrix-context: inactive (%s)", "; ".join(problems))
        return
    try:
        from hermes_constants import get_hermes_home
        home = get_hermes_home()
    except Exception:
        home = os.path.expanduser("~/.hermes")
    store = cs.Store(Path(home) / "matrix-context" / "messages.sqlite3")
    context = cs.MatrixContext(settings, store)

    def on_pre_gateway_dispatch(event=None, **_):
        if event is None:
            return None
        return context.handle(event)

    ctx.register_hook("pre_gateway_dispatch", on_pre_gateway_dispatch)
    logger.info("matrix-context: active in %d rooms for %s", len(settings.rooms), settings.bot_user_id)
