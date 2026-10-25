import pytest

from randomizer.api import randomize_rom
from randomizer.progress import NullProgressReporter, PrintProgressReporter


def test_randomize_rom_rejects_bad_input_types():
    with pytest.raises(TypeError, match="rom_data"):
        randomize_rom("not bytes", "seed")

    with pytest.raises(TypeError, match="seed"):
        randomize_rom(b"not a rom", 123)


def test_progress_reporters(capsys):
    NullProgressReporter().update("stage", "ignored")
    assert capsys.readouterr().out == ""

    PrintProgressReporter().update("stage", "hello")
    assert capsys.readouterr().out == "[stage] hello\n"
