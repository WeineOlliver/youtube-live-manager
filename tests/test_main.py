import main


def test_excepthook_logs_without_raising(tmp_path, monkeypatch):
    log = tmp_path / "error.log"
    monkeypatch.setattr(main, "ERROR_LOG_PATH", str(log))
    try:
        raise ValueError("falhou")
    except ValueError as e:
        main._excepthook(type(e), e, e.__traceback__)
    content = log.read_text(encoding="utf-8")
    assert "ValueError: falhou" in content
