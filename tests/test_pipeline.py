from pathlib import Path
import tempfile, json, yaml
from factory.core.config import DEFAULT_ROOT
from factory.adapters import parse as parse_adapter

def test_parse_generates_shots(tmp_path=Path(tempfile.mkdtemp())):
    film_dir = Path(tempfile.mkdtemp()) / "test-film"
    film_dir.mkdir(parents=True)
    (film_dir / "input.txt").write_text("Hello world. This is a test of pixar factory. One more sentence here.", encoding="utf-8")
    config = {"input_text": str(film_dir / "input.txt"), "duration_target": 30, "preset": "pixar"}
    res = parse_adapter.run(film_dir, config, dry_run=False)
    assert (film_dir / "shots.json").exists()
    data = json.loads((film_dir / "shots.json").read_text())
    assert len(data["shots"]) >= 2

def test_cli_new_film():
    # smoke via subprocess ideally, but check scaffolding logic exists
    assert (DEFAULT_ROOT / "presets" / "pixar.yaml").exists()
    assert (DEFAULT_ROOT / "presets" / "render_colab.yaml").exists()
