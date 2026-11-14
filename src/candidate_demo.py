"""Explicit offline acceptance scene. No game, network, scans or input automation."""
import copy
import hashlib
import json
import logging
import os
import tkinter as tk
from pathlib import Path
from src import constants
from src.card_display import DISPLAY
from src.configuration import read_configuration
from src.limited_sets import SetDictionary, SetInfo
from src.log_scanner import ArenaScanner
from src.ui.app import DraftApp


def run(smoke=False, gc_guard=None):
    resource=Path(constants.RESOURCE_DIR)
    config,_=read_configuration()
    config.features.images_enabled=False
    config.settings.chinese_enabled=True
    config.settings.draft_log_enabled=False
    config.settings.auto_sync_datasets=False
    empty=Path(constants.BASE_DIR)/'offline-demo-empty.log';empty.write_text('')
    sets=SetDictionary(data={'FRA':SetInfo(set_code='FRA',arena=['FRA'],scryfall=['fra'],seventeenlands=['FRA'],formats=['QuickDraft'])},version=1)
    scanner=ArenaScanner(str(empty),sets,retrieve_unknown=False)
    dataset=resource/'fixtures/localization/FRA_QuickDraft_All_Data.json'
    assert scanner.set_data.open_file(str(dataset)).name=='VALID'
    pack=json.loads((resource/'fixtures/localization/fra-pack.json').read_text())[0]['DraftPack']
    scanner.current_pack=1;scanner.current_pick=1
    scanner.pack_cards[0]=pack;scanner.initial_pack[0]=pack
    scanner.draft_sets=['FRA'];scanner.draft_label='QuickDraft'
    scanner.event_string='QuickDraft_FRA_20261008'
    root=tk.Tk()
    # Windowed frozen builds have no stderr. Keep offline UI probe failures
    # observable in the disposable profile instead of silently hiding them.
    root.report_callback_exception = lambda kind, value, traceback: logging.getLogger(__name__).error(
        "Offline UI callback failed", exc_info=(kind, value, traceback)
    )
    from src.ui.candidate_icon import apply_candidate_icon
    apply_candidate_icon(root)
    if gc_guard is not None:gc_guard.attach(root)
    if smoke:root.withdraw()
    app=DraftApp(root,scanner,config)
    root.title('MTGA 17Lands 简体中文候选 — 离线历史牌包')
    worker=DISPLAY.request(scanner.set_data.get_display_snapshot(),resource/'resources/localization/cards.json')
    # UI stays usable while names load; there is no scanning loop in this demo.
    def refresh():
        if DISPLAY.drain():app._refresh_ui_data()
        if DISPLAY.pending:root.after(50,refresh)
    app._refresh_ui_data();root.after(50,refresh)
    if smoke:
        worker.join(10);assert not worker.is_alive();DISPLAY.drain()
        before=copy.deepcopy(scanner.set_data.get_card_ratings())
        app._refresh_ui_data();root.update_idletasks()
        tree=app.dashboard.get_treeview()
        zh=[tree.item(i) for i in tree.get_children()]
        assert len(zh)==14 and any('寒意相迎' in str(r['values']) for r in zh)
        app._apply_language(False);root.update_idletasks()
        en=[tree.item(i) for i in tree.get_children()]
        assert [r['text'] for r in zh]==[r['text'] for r in en]
        assert all('寒意相迎' not in str(r['values']) for r in en)
        assert before==scanner.set_data.get_card_ratings()
        app._apply_language(True)
        # Force frozen Numba/scipy construction path with the same fixed pool.
        from src.dataset import Dataset
        from src.set_metrics import SetMetrics
        from src.advisor.deck_builder import suggest_deck,clear_deck_cache
        from src.card_logic import copy_deck
        ds=Dataset(retrieve_unknown=False)
        ds.open_file(str(resource/'fixtures/localization/fixed-dataset.json'))
        pool=ds.get_data_by_id(list(ds.get_card_ratings()))
        clear_deck_cache()
        decks=suggest_deck(pool,SetMetrics(ds),config,event_type='QuickDraft',dataset_name='candidate-smoke')
        assert decks and all('Fixed ' in copy_deck(d['deck_cards'],d['sideboard_cards']) for d in decks.values())
        result={'native_tk':root.tk.call('info','patchlevel'),'fra_pack_rows':14,'chinese_names':DISPLAY.coverage(scanner.set_data.get_card_ratings())['verified_chinese'],'english_switch_and_rank_equal':True,'raw_data_unchanged':True,'frozen_constructed_candidates':len(decks),'profile':constants.BASE_DIR}
        (Path(constants.BASE_DIR)/'offline-smoke-result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result),flush=True)
        app.orchestrator.stop();root.destroy()
    else:
        root.mainloop()
