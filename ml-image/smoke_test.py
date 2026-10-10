"""Test CPU sur un film local, dans un répertoire temporaire isolé."""
import argparse
import csv
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Vérifier démarrage et poids uniquement.')
    parser.add_argument('--trailer', type=Path, help='Vidéo locale, courte de préférence.')
    parser.add_argument('--poster', type=Path, help='Affiche locale.')
    args = parser.parse_args()
    if not args.check and (args.trailer is None or args.poster is None):
        parser.error('--trailer et --poster sont requis sans --check')
    env = dict(os.environ)
    for name, folder in [('XDG_CACHE_HOME', 'cache'), ('MPLCONFIGDIR', 'matplotlib'), ('YOLO_CONFIG_DIR', 'ultralytics')]:
        path = ROOT / 'tmp' / folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    subprocess.run([sys.executable, 'main.py', '--help'], cwd=ROOT, env=env, check=True,
                   stdout=subprocess.DEVNULL)
    missing = [name for name in ('yolov11n-face.pt', 'res34_fair_align_multi_7_20190809.pt')
               if not (ROOT / 'models' / name).is_file() or (ROOT / 'models' / name).stat().st_size == 0]
    if missing:
        parser.exit(1, 'Poids absents : ' + ', '.join(missing) + '\nExécuter install/download_models.sh dans le venv.\n')
    if args.check:
        print('Démarrage OK ; deux fichiers de poids présents. Inférence non exécutée.')
        return
    trailer, poster = args.trailer.resolve(), args.poster.resolve()
    for path in (trailer, poster):
        if not path.is_file():
            parser.error(f'Fichier absent : {path}')
    run = Path(tempfile.mkdtemp(prefix='smoke-', dir=ROOT / 'tmp'))
    media = run / 'tmp' / 'downloaded_media'
    media.mkdir(parents=True)
    shutil.copy2(trailer, media / '1.mp4')
    shutil.copy2(poster, media / '1.jpg')
    source = run / 'input.csv'
    with source.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['visa_number', 'allocine_id', 'allocine_url', 'trailer_url', 'poster_url'])
        writer.writeheader()
        # Identifiants synthétiques : aucune insertion en base.
        writer.writerow(dict(visa_number=1, allocine_id=1, allocine_url='local-test',
                             trailer_url='local-test', poster_url='local-test'))
    env.update(TEMP_FOLDER=str(run / 'tmp'), OUTPUTS_FOLDER=str(run / 'outputs'),
               DOWNLOADED_MEDIA_FOLDER='downloaded_media', PREDICTIONS_FOLDER='stored_predictions',
               FINAL_PREDICTIONS_FOLDER='final_predictions', INTERMEDIATE_FOLDER='intermediate_results',
               VISUALS_FOLDER='stored_visuals', CUDA_VISIBLE_DEVICES='')
    print(f'Résultats : {run}', flush=True)
    subprocess.run([sys.executable, 'main.py', '--source', str(source), '--mode', 'infer',
                    '--istop', '1', '--num_cpu', '2', '--batch_size', '4'],
                   cwd=ROOT, env=env, check=True)
    for kind in ('poster', 'trailer'):
        prediction = run / 'tmp' / 'stored_predictions' / f'1_{kind}_predictions.pkl'
        exported = run / 'outputs' / 'final_predictions' / f'predictions_on_{kind}s.csv'
        if not prediction.is_file() or not exported.is_file():
            raise RuntimeError(f'Sortie absente : {kind}. Consulter les erreurs de la pipeline.')
        with exported.open(newline='') as stream:
            if not list(csv.DictReader(stream)):
                raise RuntimeError(f'Aucun personnage exporté : {kind}. Test non concluant.')
    print('PASS : prédictions et CSV présents pour la vidéo et l’affiche. Qualité non évaluée.')


if __name__ == '__main__':
    main()
