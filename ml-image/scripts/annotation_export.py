"""Export optionnel avant agrégation, sans relancer les modèles."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys


def export_annotation(poster_path, detections, row, args):
    destination = os.getenv('ANNOTATION_EXPORT_DIR')
    if not destination:
        return
    root = Path(__file__).resolve().parents[1]
    # ml-image est aussi lancé depuis son propre répertoire, sans installation du dépôt.
    tool_root = root / 'annotation-poster'
    if str(tool_root) not in sys.path:
        sys.path.insert(0, str(tool_root))
    from api.importer import convert_predictions, prepare

    code = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True)
    weights = {}
    for path in (root / 'models').glob('*.pt'):
        weights[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    run_id = Path(args.source).stem + '-' + os.environ.get('ANNOTATION_RUN_ID', 'local')
    prepare(destination, f'allocine-{int(row.allocine_id)}', Path(poster_path).read_bytes(),
            convert_predictions(detections), dict(title=f'Allociné {int(row.allocine_id)}',
                allocine_id=int(row.allocine_id), visa_number=str(row.visa_number),
                poster_url=str(row.poster_url), prediction_stage='filtered', run_id=run_id,
                code_version=code.stdout.strip() if code.returncode == 0 else None,
                weights=weights, parameters=vars(args)))
