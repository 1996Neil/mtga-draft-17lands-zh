"""Regressions for live input isolation, event selection and Tk worker safety."""
import hashlib
import json
import queue
import sqlite3
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import tkinter
from src.arena_english import english_localizations, identity_signature, connect_readonly
from src.ui_progress import UIProgress
from src.ui.windows.download import DownloadWindow
from src.limited_sets import SetInfo
from src.ui.styles import Theme


def database(path, title='English Name'):
    con=sqlite3.connect(path)
    con.executescript('CREATE TABLE Versions (name TEXT); CREATE TABLE Cards (TitleId INT, GrpId INT); CREATE TABLE Enums (LocId INT); CREATE TABLE Localizations_enUS (LocId INT, Formatted INT, Loc TEXT);')
    con.execute('INSERT INTO Versions VALUES (?)',('same',))
    con.execute('INSERT INTO Cards VALUES (1, 123)')
    con.execute('INSERT INTO Enums VALUES (2)')
    con.executemany('INSERT INTO Localizations_enUS VALUES (?,0,?)',[(1,title),(2,'Creature')])
    con.commit();con.close()


def test_patched_enus_requires_same_identity_and_trusted_payload(tmp_path):
    path=tmp_path/'cards.db';database(path,'中文牌名')
    con=connect_readonly(path)
    rows=[{'LocId':1,'Formatted':0,'Loc':'English Name'},{'LocId':2,'Formatted':0,'Loc':'Creature'}]
    snapshot={'schema':1,'identity_sha256':identity_signature(con),'localizations':rows,
              'localizations_sha256':hashlib.sha256(json.dumps(rows,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()}
    resource=tmp_path/'english.json';resource.write_text(json.dumps(snapshot))
    assert english_localizations(con,resource)==rows
    with pytest.raises(sqlite3.OperationalError):con.execute('DELETE FROM Cards')
    snapshot['identity_sha256']='wrong';resource.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError,match='identities changed'):english_localizations(con,resource)
    snapshot['identity_sha256']=identity_signature(con);snapshot['localizations'][0]['Loc']='Bad English';resource.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError,match='corrupt'):english_localizations(con,resource)
    con.close()


def test_unmodified_english_needs_no_translation_resource(tmp_path):
    path=tmp_path/'cards.db';database(path)
    with connect_readonly(path) as con:
        assert english_localizations(con,tmp_path/'missing.json')[0]['Loc']=='English Name'


def test_worker_progress_has_no_tk_calls():
    messages=queue.Queue();ui=MagicMock();status=MagicMock();bar=MagicMock()
    progress=UIProgress(bar,status,ui,dispatch=messages.put)
    worker=threading.Thread(target=lambda:(progress._update_status('Connecting'),progress._update_progress(7)))
    worker.start();worker.join(2)
    assert list(messages.queue)==[('status','Connecting'),('progress',(7,True))]
    assert not ui.mock_calls and not status.mock_calls and not bar.mock_calls


@pytest.fixture
def panel():
    root=tkinter.Tk();root.withdraw();Theme.apply(root,'Dark')
    config=MagicMock();config.settings.column_configs={};config.card_data.latest_dataset='old.json'
    sets=MagicMock(data={'FRA':SetInfo(arena=['ALL'],seventeenlands=['FRA'],set_code='FRA',formats=['QuickDraft','PremierDraft','ContenderDraft'])},latest_set='FRA')
    with patch('src.ui.windows.download.retrieve_local_set_list',return_value=([],None)):
        window=DownloadWindow(root,sets,config,MagicMock(),event_getter=lambda:('FRA','QuickDraft'))
    yield window
    root.destroy()


def test_download_defaults_to_detected_format_not_alphabetical(panel):
    assert panel.vars['event'].get()=='QuickDraft'
    panel.vars['event'].set('PremierDraft')
    # Manual format remains selectable; no silent forced downloads.
    assert panel.vars['event'].get()=='PremierDraft'


def test_worker_completion_is_queued_not_tk_after(panel):
    with patch.object(panel,'after') as after,patch.object(panel,'_activate_download') as activate:
        worker=threading.Thread(target=lambda:panel._safe_finalize('done','new.json'))
        worker.start();worker.join(2)
        after.assert_not_called();activate.assert_not_called()
        assert panel._messages.get_nowait()==('success',('done','new.json'))


def test_activation_rejects_empty_statistics_and_other_event(panel,tmp_path):
    cards={'1':{'deck_colors':{'All Decks':{'gihwr':0}}}}
    filename='FRA_QuickDraft_All_Data.json'
    with patch('src.ui.windows.download.constants.SETS_FOLDER',str(tmp_path)),patch('tkinter.messagebox.showerror') as error,patch('tkinter.messagebox.showinfo'),patch('src.ui.windows.download.write_configuration',return_value=True) as save:
        path=tmp_path/filename;path.write_text(json.dumps({'card_ratings':cards}))
        panel._activate_download('done',filename)
        assert panel.configuration.card_data.latest_dataset=='old.json'
        error.assert_called_once();save.assert_not_called()
        cards['1']['deck_colors']['All Decks']['gihwr']=57
        other='FRA_ContenderDraft_All_Data.json';(tmp_path/other).write_text(json.dumps({'card_ratings':cards}))
        panel._activate_download('done',other)
        assert panel.configuration.card_data.latest_dataset=='old.json'
        save.assert_not_called()
        path.write_text(json.dumps({'card_ratings':cards}));panel._activate_download('done',filename)
        assert panel.configuration.card_data.latest_dataset==filename
        save.assert_called_once()


def test_current_fra_public_dataset_maps_actual_pack():
    root=Path(__file__).resolve().parents[1]
    data=json.loads((root/'resources/datasets/FRA_QuickDraft_All_Custom-AllTime-20261010_Data.json').read_text())
    ids=json.loads((root/'fixtures/localization/fra-pack.json').read_text())[0]['DraftPack']
    cards=[data['card_ratings'][cid] for cid in ids]
    assert len(cards)==14
    assert all(not any('\u3400'<=c<='\u9fff' for c in card['name']) for card in cards)
    assert sum(card['deck_colors']['All Decks']['gihwr']>0 for card in cards)==11
    assert next(c for c in cards if c['name']=='Icy Reception')['deck_colors']['All Decks']['gihwr']==59.33


def test_zero_repeat_download_preserves_existing_file(tmp_path,monkeypatch):
    from src.file_extractor import FileExtractor
    from src import constants
    monkeypatch.setattr(constants,'SETS_FOLDER',str(tmp_path))
    filename='FRA_QuickDraft_All_Custom-AllTime-20261010_Data.json'
    existing=tmp_path/filename;existing.write_bytes(b'previous valid dataset bytes')
    before=hashlib.sha256(existing.read_bytes()).hexdigest()
    ex=FileExtractor('',None,None,None,require_usable_statistics=True)
    ex.select_sets(SetInfo(arena=['ALL'],seventeenlands=['FRA']))
    ex.set_draft_type('QuickDraft');ex.set_end_date('2026-10-10');ex.set_user_group('All')
    ex.combined_data={'card_ratings':{'1':{'deck_colors':{'All Decks':{'gihwr':0}}}}}
    assert ex.export_card_data()==''
    assert hashlib.sha256(existing.read_bytes()).hexdigest()==before
    assert not list(tmp_path.glob('*.tmp'))


def test_missing_score_placeholder_preserves_numeric_sort(panel):
    from src.ui.components import ModernTreeview
    tree=ModernTreeview(panel,columns=['name','value'])
    tree.insert('', 'end',iid='higher',text='Zulu',values=('朱鲁','—'))
    tree.insert('', 'end',iid='lower',text='Alpha',values=('阿尔法','10'))
    tree.raw_sort_values={'higher':{'value':'20'},'lower':{'value':'10'}}
    tree._handle_sort('value',True)
    assert tree.get_children()==('higher','lower')
    tree._handle_sort('value',False)
    assert tree.get_children()==('lower','higher')


@pytest.mark.parametrize('kind',['known-sample','same-name-user-data','excluded-bootstrap'])
def test_candidate_bootstrap_respects_user_data(tmp_path,monkeypatch,kind):
    root=Path(__file__).resolve().parents[1]
    profile=tmp_path/'Library/Application Support/MTGA_Draft_17Lands_ZH_Candidate'
    sets=profile/'Sets';sets.mkdir(parents=True)
    old='FRA_QuickDraft_All_Data.json';new='FRA_QuickDraft_All_Custom-AllTime-20261010_Data.json'
    state={'settings':{},'card_data':{'latest_dataset':old,'excluded_datasets':[]}}
    if kind=='known-sample':(sets/old).write_bytes((root/'fixtures/localization'/old).read_bytes())
    elif kind=='same-name-user-data':(sets/old).write_bytes(b'user chosen file')
    else:
        state['card_data'].update(latest_dataset='',excluded_datasets=[new])
    (profile/'config.json').write_text(json.dumps(state))
    monkeypatch.setattr(Path,'home',lambda:tmp_path)
    monkeypatch.setenv('MTGA_DRAFT_PROFILE','/tmp/test-before-bootstrap')
    monkeypatch.setenv('MTGA_DRAFT_SAFE_INPUT','0')
    monkeypatch.setenv('MTGA_DRAFT_RESOURCES',str(root))
    monkeypatch.chdir(root)
    source=(root/'candidate_main.py').read_text().split('from src.ui.tk_gc import')[0]
    exec(compile(source,'candidate-bootstrap','exec'),{'__file__':str(root/'candidate_main.py')})
    result=json.loads((profile/'config.json').read_text())
    if kind=='known-sample':
        assert (profile/'Offline-Samples'/old).is_file() and not (sets/old).exists()
        assert result['card_data']['latest_dataset']==new
    elif kind=='same-name-user-data':
        assert (sets/old).read_bytes()==b'user chosen file'
        assert result['card_data']['latest_dataset']==old
    else:
        assert not (sets/new).exists()
        assert result['card_data']['latest_dataset']==''
