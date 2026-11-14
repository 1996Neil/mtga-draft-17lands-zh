"""Isolated Mac trial entry point. No official app/game/maintainer writes."""
import json
import os
import sys
from pathlib import Path

PROFILE = Path.home() / 'Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate'
# Only this named trial profile is used. Official app data is never migrated.
PROFILE.mkdir(parents=True, exist_ok=True)
os.environ['MTGA_DRAFT_PROFILE'] = str(PROFILE)
os.environ['MTGA_DRAFT_SAFE_INPUT'] = '1'
RESOURCE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
os.chdir(PROFILE)
config = PROFILE / 'config.json'
if not config.exists():
    config.write_text(json.dumps({'settings': {'chinese_enabled': True, 'last_run_version': '4.23',
        'auto_sync_datasets': False, 'update_notifications_enabled': False,
        'missing_notifications_enabled': False, 'draft_log_enabled': False},
        'features': {'images_enabled': False}}))
# Historical acceptance fixtures belong only to the explicit offline demo.
# Repair the earlier candidate's exact seeded sample reversibly; never move
# user-downloaded datasets just because their names are similar.
sets = PROFILE / 'Sets'; sets.mkdir(exist_ok=True)
historical = sets / 'FRA_QuickDraft_All_Data.json'
import hashlib
migrated_sample = False
if historical.is_file() and hashlib.sha256(historical.read_bytes()).hexdigest() in {
    'c78746867adf9f5c471cd5b321bf86acc7ef53d1917c56af732725c724f2ecaf',
    '2a3394ca743e09eb93508f315df097352514d4e7e753049d06f0e9804b9a6866',
}:
    archive = PROFILE / 'Offline-Samples'; archive.mkdir(exist_ok=True)
    destination = archive / historical.name
    if not destination.exists():
        historical.replace(destination)
        migrated_sample = True
    elif destination.read_bytes() == historical.read_bytes():
        historical.unlink()
        migrated_sample = True
source = RESOURCE / 'resources/datasets/FRA_QuickDraft_All_Custom-AllTime-20261010_Data.json'
target = sets / source.name
state = json.loads(config.read_text())
excluded = state.get('card_data', {}).get('excluded_datasets', [])
if source.is_file() and not target.exists() and source.name not in excluded:
    payload = source.read_bytes()
    if hashlib.sha256(payload).hexdigest() != '8ba03442998fd3cb69485eacc21aecbb2c50218b36799daea878330199170ba8':
        raise ValueError('Bundled 17Lands dataset failed integrity validation.')
    target.write_bytes(payload)
previous_selection = state.get('card_data', {}).get('latest_dataset', '')
if target.exists() and source.name not in excluded and (not previous_selection or (migrated_sample and previous_selection == 'FRA_QuickDraft_All_Data.json')):
    state.setdefault('card_data', {})['latest_dataset'] = source.name
    config.write_text(json.dumps(state, ensure_ascii=False))
# Resource path must stay independent of the profile working directory.
os.environ['MTGA_DRAFT_RESOURCES'] = str(RESOURCE)
from src.ui.tk_gc import TkGCGuard

# Cover startup imports and all asynchronous readers, including the splash
# hand-off. The normal upstream entry point is unaffected by this trial guard.
with TkGCGuard() as gc_guard:
    if '--offline-demo' in sys.argv or '--offline-smoke' in sys.argv:
        from src.candidate_demo import run
        run(smoke='--offline-smoke' in sys.argv, gc_guard=gc_guard)
    elif '--startup-smoke' in sys.argv:
        from src.candidate_startup_smoke import run
        run(gc_guard)
    else:
        from main import main
        main(gc_guard=gc_guard)
