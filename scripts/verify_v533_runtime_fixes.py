from __future__ import annotations
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_curation_tool.paths import AppPaths
from data_curation_tool.services.three_d_service import ThreeDService
from data_curation_tool.models.adapters import _parse_prediction_table

class Dummy:
    pass

def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        runtime = root / 'runtime'; models = root / 'models'; outputs = root / 'outputs'
        runtime.mkdir(); models.mkdir(); outputs.mkdir()
        paths = AppPaths(root=root, runtime=runtime, models=models, outputs=outputs, database=runtime/'app.db', settings=runtime/'settings.json', thumbnails=runtime/'thumbnails', presets=runtime/'presets', downloads=runtime/'downloads', exports=runtime/'exports')
        paths.ensure()
        svc = ThreeDService(paths, Dummy(), Dummy())
        install = root / 'Blender Foundation' / 'Blender 5.0'
        install.mkdir(parents=True)
        launcher = install / 'blender-launcher.exe'
        blender = install / 'blender.exe'
        launcher.write_text('launcher')
        blender.write_text('exe')
        resolved = svc._resolve_blender_executable(str(launcher))
        assert resolved == str(blender.resolve()), resolved

    parsed = _parse_prediction_table('filename,tag_a,tag_b,rating_safe\nimage.png,0.91,0.25,0.99\n')
    assert ('tag_a', 0.91) in parsed, parsed
    assert ('rating_safe', 0.99) in parsed, parsed
    print('v5.33 runtime fixes verified')

if __name__ == '__main__':
    main()
