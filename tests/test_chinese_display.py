"""Identity, hostile cache, stale worker and real Tk display boundaries."""
import copy
import json
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk
import pytest
from src.card_display import DisplayIndex, DisplayRecord, verified_index, identity_key
from src.i18n import set_language, tr, advisor_reason
from src.ui.language_refresh import refresh_language

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'fixtures/localization/FRA_QuickDraft_All_Data.json').read_text())['card_ratings']
AID = '106256'
CARD = DATA[AID]
RECORD = dict(arena_id=AID, english=CARD['name'], chinese='寒意相迎', set_code=CARD['set'], primary=CARD['isprimarycard'], face_type=CARD['linkedfacetype'], source='verified-maintainer-snapshot', status='static-verified-client-pending')

@pytest.fixture(autouse=True)
def english_after():
    set_language(False)
    yield
    set_language(False)

def snapshot(tmp_path, record=None):
    p = tmp_path/'cards.json'
    p.write_text(json.dumps({'schema': 1, 'cards': [record or RECORD]}))
    return p

def load(index, cards, source):
    worker=index.request(cards, source)
    worker.join(3)
    assert not worker.is_alive()
    assert index.drain()
    return index

def test_trusted_name_is_copy_only_and_switchable(tmp_path):
    before=copy.deepcopy(CARD)
    index=load(DisplayIndex(), {AID:CARD}, snapshot(tmp_path))
    index.enabled=True
    assert index.name(copy.deepcopy(CARD), AID)=='寒意相迎 / Icy Reception'
    assert CARD==before
    index.enabled=False
    assert index.name(CARD)==CARD['name']

@pytest.mark.parametrize('field,value', [('english','Wrong'),('arena_id','999'),('set_code','DSK'),('primary',0),('face_type',7),('status','needs-review'),('chinese','Unverified')])
def test_wrong_or_unknown_identity_falls_back(tmp_path,field,value):
    record=dict(RECORD, **{field:value})
    index=load(DisplayIndex(),{AID:CARD},snapshot(tmp_path,record)); index.enabled=True
    assert index.name(CARD,AID)==CARD['name']

def test_conflicting_source_rows_fail_closed():
    rows=[DisplayRecord(**RECORD), DisplayRecord(**dict(RECORD,chinese='冲突译名'))]
    assert verified_index({AID:CARD},rows)=={}

def test_hostile_oracle_and_statistics_never_enter_raw_card(tmp_path):
    original=copy.deepcopy(CARD)
    bad=dict(RECORD,oracle_text='Flying',types=['Land'],tags=['removal'],name='Wrong',deck_colors={'All Decks':{'gihwr':99}},cmc=99)
    index=load(DisplayIndex(),{AID:CARD},snapshot(tmp_path,bad));index.enabled=True
    assert index.name(CARD,AID).startswith('寒意相迎')
    assert CARD==original
    assert index.coverage({AID:CARD})['verified_chinese']==1
    changed=dict(CARD,oracle_text='Flying')
    assert index.name(changed,AID)==changed['name']

@pytest.mark.parametrize('kind', ['missing','malformed','unknown-schema'])
def test_unavailable_cache_fallback(tmp_path,kind):
    p=tmp_path/'none.json'
    if kind=='malformed':p.write_text('{')
    if kind=='unknown-schema':p.write_text('{"schema":999}')
    index=load(DisplayIndex(),{AID:CARD},p);index.enabled=True
    assert index.name(CARD)==CARD['name']
    assert not index.pending

def test_snapshot_is_detached():
    from src.dataset import Dataset
    ds=Dataset(retrieve_unknown=False)
    assert ds.open_file(str(ROOT/'fixtures/localization/FRA_QuickDraft_All_Data.json')).name=='VALID'
    snapshot=ds.get_display_snapshot()
    snapshot[AID]['oracle_text']='Flying'
    snapshot[AID]['types'].append('Land')
    assert ds.get_card_ratings()[AID]==CARD

def test_slow_and_stale_worker_cannot_block_or_replace_current(tmp_path,monkeypatch):
    import src.card_display as module
    started=threading.Event();release=threading.Event()
    def reader(path):
        if path=='slow':
            started.set();assert release.wait(3)
            return [DisplayRecord(**dict(RECORD,chinese='过期译名'))]
        return [DisplayRecord(**RECORD)]
    monkeypatch.setattr(module,'read_source',reader)
    index=DisplayIndex();first=index.request({AID:CARD},'slow')
    assert started.wait(1) and first.is_alive()
    second=index.request({AID:CARD},'fast');second.join(1);index.drain();index.enabled=True
    assert index.name(CARD).startswith('寒意相迎')
    release.set();first.join(1);assert not index.drain()
    assert index.name(CARD).startswith('寒意相迎')

def test_actual_tk_switch_keeps_machine_rows_and_variables(session_tk_root):
    root=session_tk_root;set_language(False)
    label=ttk.Label(root,text=tr('File'));label.pack()
    machine=tk.StringVar(value='QuickDraft')
    tree=ttk.Treeview(root,columns=('name',));tree.heading('name',text=tr('Name'))
    item=tree.insert('', 'end',text='Icy Reception',values=('Icy Reception',));tree.pack()
    menu=tk.Menu(root,tearoff=False);menu.add_command(label=tr('Preferences...'))
    root.configure(menu=menu)
    notebook=ttk.Notebook(root);page=ttk.Frame(notebook);notebook.add(page,text=tr('Deck Builder'));notebook.pack()
    set_language(True);refresh_language(root);root.update_idletasks()
    assert label.cget('text')=='文件'
    assert menu.entrycget(0,'label')=='偏好设置...'
    assert notebook.tab(page,'text')=='套牌构筑'
    assert tree.heading('name','text')=='牌名'
    assert tree.item(item,'text')=='Icy Reception' and machine.get()=='QuickDraft'
    set_language(False);refresh_language(root)
    assert label.cget('text')=='File' and notebook.tab(page,'text')=='Deck Builder'
    assert tree.heading('name','text')=='Name'

def test_reason_parameters_and_unknown_fallback():
    set_language(True)
    assert advisor_reason('Archetype Glue (+2.3)')=='原型关键衔接（+2.3）'
    assert tr('Pack 3 Pick 8')=='第 3 包第 8 抓'
    assert tr('Name ▲')=='牌名 ▲'
    assert advisor_reason('future unknown reason')=='future unknown reason'
    chinese=tr('Total Cards: 40  |  Creatures: 17  |  Non-Creatures: 6  |  Lands: 17')
    assert '40' in chinese and '生物' in chinese
    set_language(False)
    assert tr(chinese)=='Total Cards: 40  |  Creatures: 17  |  Non-Creatures: 6  |  Lands: 17'

def test_three_ingestion_paths_have_no_chinese_mutation():
    for f in ('src/dataset.py','src/file_extractor.py','src/ui/app_controller.py'):
        code=(ROOT/f).read_text()
        assert 'apply_metadata' not in code and 'MtgchClient' not in code
    # Every calculation core stays byte-identical to upstream v4.23.
    import subprocess
    for f in ['src/card_logic.py','src/card_utils.py','src/signals.py','src/set_metrics.py','src/sealed_logic.py']+list(str(p.relative_to(ROOT)) for p in (ROOT/'src/advisor').glob('*.py')):
        assert (ROOT/f).read_bytes()==subprocess.check_output(['git','show',f'HEAD:{f}'],cwd=ROOT)

def test_missing_quickdraft_never_falls_into_premier_on_repeated_refresh(session_tk_root):
    from unittest.mock import MagicMock, patch
    from src.configuration import Configuration
    from src.ui.top_bar import TopBarControls
    app=MagicMock();app.root=session_tk_root;app.configuration=Configuration()
    app.vars={k:tk.StringVar(value='') for k in ['status_text','set_label','deck_filter','selected_event','selected_group']}
    app._loading=False;app._initialized=True
    app.active_event_set='FRA';app.active_event_type='QuickDraft';app.current_draft_id='fixture'
    app.orchestrator.scanner.current_draft_id='fixture'
    app.orchestrator.scanner.retrieve_current_limited_event.return_value=('FRA','QuickDraft')
    app.orchestrator.scanner.set_list.data={}
    bar=TopBarControls(session_tk_root,app)
    with patch('src.ui.top_bar.retrieve_local_set_list',return_value=([('FRA','PremierDraft','All','','',500,'/fake/FRA_PremierDraft_All.json','')], [])):
        for _ in range(3):bar.update_data_sources()
    assert app.vars['selected_event'].get()=='QuickDraft'
    assert app.vars['selected_group'].get()==''
    app.orchestrator.scanner.retrieve_set_data.assert_not_called()
    assert app.orchestrator.sync_dataset_to_event.call_count==3

def test_colliding_translations_restore_each_control(session_tk_root):
    set_language(True)
    labels=[ttk.Label(session_tk_root,text=tr(word)) for word in ('Score','Value','Rating')]
    assert [x.cget('text') for x in labels]==['评分']*3
    set_language(False);refresh_language(session_tk_root)
    assert [x.cget('text') for x in labels]==['Score','Value','Rating']

def test_recommendation_requires_current_card_identity(tmp_path,monkeypatch):
    import src.card_display as module
    index=load(DisplayIndex(),{AID:CARD},snapshot(tmp_path));index.enabled=True
    monkeypatch.setattr(module,'DISPLAY',index)
    assert module.recommendation_name(CARD['name'],[CARD]).startswith('寒意相迎')
    assert module.recommendation_name(CARD['name'],[dict(CARD,set='UNK')])==CARD['name']
    assert module.recommendation_name(CARD['name'],[CARD,dict(CARD,set='UNK')])==CARD['name']
    assert module.recommendation_name(CARD['name'])==CARD['name']

def test_numeric_sort_and_name_sort_use_canonical_english(session_tk_root):
    from src.ui.components import ModernTreeview
    tree=ModernTreeview(session_tk_root,columns=('name','value'))
    a=tree.insert('','end',iid='a',text='A',values=('A',50))
    z=tree.insert('','end',iid='z',text='Z',values=('Z',50))
    tree._handle_sort('value',False);before=tree.get_children()
    tree.item(a,values=('中 / A',50));tree.item(z,values=('一 / Z',50))
    tree._handle_sort('value',False);assert tree.get_children()==before
    tree._handle_sort('name',False);assert tree.get_children()==('a','z')

def test_isolated_profile_path(monkeypatch,tmp_path):
    from src.configuration import get_config_path
    monkeypatch.setenv('MTGA_DRAFT_PROFILE',str(tmp_path))
    assert get_config_path()==str(tmp_path/'config.json')

def test_real_fra_full_app_display_and_english_export(session_tk_root,tmp_path):
    from src.log_scanner import ArenaScanner
    from src.ui.app import DraftApp
    from src.configuration import Configuration
    from src.card_display import DISPLAY
    from src.card_logic import copy_deck
    from unittest.mock import patch
    log=tmp_path/'empty.log';log.write_text('')
    from src.limited_sets import SetDictionary
    scanner=ArenaScanner(str(log),SetDictionary(data={},version=1),retrieve_unknown=False)
    assert scanner.set_data.open_file(str(ROOT/'fixtures/localization/FRA_QuickDraft_All_Data.json')).name=='VALID'
    ids=json.loads((ROOT/'fixtures/localization/fra-pack.json').read_text())[0]['DraftPack']
    scanner.current_pack=1;scanner.current_pick=1
    scanner.pack_cards[0]=ids;scanner.initial_pack[0]=ids
    scanner.draft_sets=['FRA'];scanner.draft_label='QuickDraft'
    scanner.event_string='QuickDraft_FRA_20261008';scanner.taken_cards=[AID]
    config=Configuration();config.settings.chinese_enabled=True
    config.settings.draft_log_enabled=False;config.features.images_enabled=False
    app=DraftApp(session_tk_root,scanner,config)
    load(DISPLAY,scanner.set_data.get_display_snapshot(),ROOT/'resources/localization/cards.json')
    DISPLAY.enabled=True
    before=copy.deepcopy(scanner.set_data.get_card_ratings())
    app._refresh_ui_data();session_tk_root.update_idletasks()
    tree=app.dashboard.get_treeview()
    rows=[tree.item(i) for i in tree.get_children()]
    assert len(rows)==14
    assert any('寒意相迎' in str(r['values']) for r in rows)
    assert all('/' not in r['text'] for r in rows)
    export=copy_deck(scanner.retrieve_taken_cards(),[])
    with patch('src.ui.app.write_configuration'):
        app._apply_language(False)
    en_rows=[tree.item(i) for i in tree.get_children()]
    assert [r['text'] for r in rows]==[r['text'] for r in en_rows]
    assert all('寒意相迎' not in str(r['values']) for r in en_rows)
    assert scanner.set_data.get_card_ratings()==before
    assert copy_deck(scanner.retrieve_taken_cards(),[])==export and 'Icy Reception' in export
    app.orchestrator.stop()

def test_open_sealed_studio_switches_rows_and_keeps_variant_and_export(session_tk_root,tmp_path):
    from src.ui.windows.sealed_studio import SealedStudioWindow
    from src.card_display import DISPLAY
    from src.configuration import Configuration
    from src.dataset import Dataset
    from src.set_metrics import SetMetrics
    from src.card_logic import copy_deck
    from unittest.mock import MagicMock,patch
    ds=Dataset(retrieve_unknown=False);ds.open_file(str(ROOT/'fixtures/localization/FRA_QuickDraft_All_Data.json'))
    load(DISPLAY,ds.get_display_snapshot(),ROOT/'resources/localization/cards.json');DISPLAY.enabled=True;set_language(True)
    cfg=Configuration();cfg.features.images_enabled=False
    app=MagicMock();app.orchestrator.scanner.current_draft_id='language-regression'
    with patch('src.ui.windows.sealed_studio.ThreadPoolExecutor'),patch('src.sealed_logic.SealedSession.load_session',return_value=None):
        studio=SealedStudioWindow(session_tk_root,app,cfg,[dict(CARD,count=1)],SetMetrics(ds),draft_id='language-regression')
        studio.view_mode='list';studio._refresh_data()
        tree=studio.pool_manager.tree
        assert any('寒意相迎' in str(tree.item(i,'values')) for i in tree.get_children())
        studio.session.create_variant('Pool');studio.session.active_variant_name='Pool';studio._refresh_tabs()
        before={name:copy.deepcopy(v.__dict__) for name,v in studio.session.variants.items()}
        lists=studio.session.get_active_deck_lists();export=copy_deck(*lists)
        DISPLAY.enabled=False;set_language(False);refresh_language(session_tk_root)
        assert all('寒意相迎' not in str(tree.item(i,'values')) for i in tree.get_children())
        assert studio.session.active_variant_name=='Pool' and {name:v.__dict__ for name,v in studio.session.variants.items()}==before
        assert copy_deck(*studio.session.get_active_deck_lists())==export
        assert any(studio.notebook_list.tab(t,'text').strip()=='Pool' for t in studio.notebook_list.tabs())
        studio.destroy()

def test_bilingual_card_title_survives_ui_translation_and_restore(session_tk_root,tmp_path):
    index=load(DisplayIndex(),{AID:CARD},snapshot(tmp_path));index.enabled=True
    set_language(True)
    name=index.name(CARD,AID)
    label=ttk.Label(session_tk_root,text=tr(name))
    assert label.cget('text')=='寒意相迎 / Icy Reception'
    set_language(False);refresh_language(session_tk_root)
    assert label.cget('text')=='Icy Reception'
    set_language(True);refresh_language(session_tk_root)
    assert label.cget('text')=='寒意相迎 / Icy Reception'
