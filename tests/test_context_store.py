import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import context_store as cs  # noqa: E402

BOT = "@cfobot:example.org"
OWNER = "@joao:example.org"
OTHER = "@rafael:example.org"
AGENT = "@rbrain:example.org"
ROOM = "!shared"
PRIVATE = "!private"


class Clock:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        self.t += 1
        return self.t


def make(tmp_path, **kw):
    settings = cs.Settings(bot_user_id=BOT, rooms={ROOM}, owners={OWNER}, **kw)
    return cs.MatrixContext(settings, cs.Store(tmp_path / "m.sqlite3"), clock=Clock())


def event(sender, text, eid, room=ROOM, thread=None, mention=False, chat_type="group", platform="matrix", name=None):
    raw = {"body": text}
    if thread:
        raw["m.relates_to"] = {"rel_type": "m.thread", "event_id": thread}
    if mention:
        raw["m.mentions"] = {"user_ids": [BOT]}
    source = SimpleNamespace(platform=SimpleNamespace(value=platform), chat_id=room, chat_type=chat_type,
                             user_id=sender, user_name=name, message_id=eid)
    return SimpleNamespace(source=source, raw_message=raw, text=text, user_id=sender, user_name=name, message_id=eid)


def test_unmentioned_message_is_stored_and_skipped(tmp_path):
    mc = make(tmp_path)
    assert mc.handle(event(OTHER, "decidimos 1 de novembro", "$1"))["action"] == "skip"
    assert len(mc.store.since_cursor(ROOM, "", exclude="")) == 1


def test_owner_mention_gets_the_thread_since_last_turn(tmp_path):
    mc = make(tmp_path)
    mc.handle(event(OTHER, "raiz da thread", "$root", name="Rafael"))
    mc.handle(event(AGENT, "a validação", "$2", thread="$root", name="rbrain"))
    mc.handle(event(OTHER, "noutra thread", "$3", thread="$other"))
    out = mc.handle(event(OWNER, "valida esta estratégia", "$4", thread="$root", mention=True))
    assert out["action"] == "rewrite"
    assert "[Rafael] raiz da thread".split("]")[-1] in out["text"] and "a validação" in out["text"]
    assert "noutra thread" not in out["text"]
    assert out["text"].endswith(f"{cs.FOOTER}\nvalida esta estratégia")
    assert out["text"].startswith(cs.HEADER)


def test_second_mention_only_gets_what_is_new(tmp_path):
    mc = make(tmp_path)
    mc.handle(event(OTHER, "antes", "$1", thread="$t"))
    mc.handle(event(OWNER, "primeira", "$2", thread="$t", mention=True))
    mc.handle(event(OTHER, "depois", "$3", thread="$t"))
    out = mc.handle(event(OWNER, "segunda", "$4", thread="$t", mention=True))
    assert "depois" in out["text"] and "antes" not in out["text"]


def test_mention_with_nothing_new_passes_unchanged(tmp_path):
    mc = make(tmp_path)
    assert mc.handle(event(OWNER, "olá", "$1", mention=True)) is None


def test_mention_from_non_owner_is_stored_not_answered(tmp_path):
    mc = make(tmp_path)
    assert mc.handle(event(OTHER, "@cfobot responde", "$1", mention=True))["action"] == "skip"
    assert mc.handle(event(AGENT, "pergunta ao cfobot", "$2", mention=True))["action"] == "skip"


def test_owner_without_mention_is_skipped(tmp_path):
    mc = make(tmp_path)
    assert mc.handle(event(OWNER, "nota para o Rafael", "$1"))["action"] == "skip"


def test_owner_command_passes(tmp_path):
    mc = make(tmp_path)
    assert mc.handle(event(OWNER, "/stop", "$1")) is None


def test_other_rooms_dms_and_platforms_untouched(tmp_path):
    mc = make(tmp_path)
    assert mc.handle(event(OTHER, "x", "$1", room=PRIVATE)) is None
    assert mc.handle(event(OTHER, "x", "$2", chat_type="dm")) is None
    assert mc.handle(event(OTHER, "x", "$3", platform="discord")) is None


def test_mention_detection_variants():
    assert cs.is_mentioned({"m.mentions": {"user_ids": [BOT]}}, "CFO bot: olá", BOT)
    assert cs.is_mentioned({}, "olá @cfobot, vê isto", BOT)
    assert cs.is_mentioned({"formatted_body": '<a href="https://matrix.to/#/%40cfobot%3Aexample.org">CFO bot</a>'}, "x", BOT)
    assert cs.is_mentioned({}, "CFO bot vê isto", BOT, ["CFO bot"])
    assert not cs.is_mentioned({}, "o cfobot do João", BOT)
    assert not cs.is_mentioned({}, "email@cfobot.pt", BOT)


def test_render_caps_messages_and_chars():
    rows = [(1_000_000 + i, "@a", "A", "x" * 100) for i in range(60)]
    assert len(cs.render(rows, 40, 100_000).splitlines()) == 40
    assert len(cs.render(rows, 40, 500)) <= 500


def test_settings_from_env_reports_problems():
    s = cs.Settings.from_env({"MATRIX_USER_ID": BOT})
    assert "MATRIX_CONTEXT_ROOMS is empty" in s.problems()
    s = cs.Settings.from_env({"MATRIX_USER_ID": BOT, "MATRIX_CONTEXT_ROOMS": f"{ROOM}, ", "MATRIX_ALLOWED_USERS": OWNER})
    assert s.problems() == [] and s.rooms == {ROOM}
