"""Display-only Chinese card names. Never returns or changes computation objects."""
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import queue
import re
import sqlite3
import threading
from src.i18n import RenderedText

IDENTITY_FIELDS = ('name', 'set', 'isprimarycard', 'linkedfacetype', 'cmc',
                   'mana_cost', 'types', 'subtypes', 'colors', 'oracle_text', 'tags')
TRUSTED = {'static-verified-client-pending',
           'native-regression-passed;unsampled-cards-static-only'}


def identity_key(card):
    return hashlib.sha256(json.dumps({k: card.get(k) for k in IDENTITY_FIELDS},
                          sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class DisplayRecord:
    arena_id: str
    english: str
    chinese: str
    set_code: str
    primary: int
    face_type: int
    source: str
    status: str


def read_source(path):
    """Only read an existing, checkpointed source. No migrations/network/writes."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size > 1024 * 1024 * 1024:
        return []
    if path.suffix == '.sqlite':
        if any(Path(str(path) + suffix).exists() and Path(str(path) + suffix).stat().st_size
               for suffix in ('-wal', '-journal')):
            raise ValueError('Translation source has active SQLite journal; use a snapshot')
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True) as db:
            rows = db.execute('SELECT arena_grp_id,english_canonical,chinese_display,identity_json,source,compatibility_status FROM card_names WHERE display_enabled=1').fetchall()
        result = []
        for aid, english, chinese, identity, source, status in rows:
            try:
                face = json.loads(identity)
                if int(face['GrpId']) != int(aid) or int(face['IsToken']) != 0:
                    continue
                result.append(DisplayRecord(str(aid), english, chinese,
                              str(face['ExpansionCode']), int(face['IsPrimaryCard']),
                              int(face['LinkedFaceType']), str(source), status))
            except (ValueError, TypeError, KeyError):
                continue
        return result
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('Translation snapshot exceeds size limit')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema') != 1:
        raise ValueError('Unknown translation snapshot schema')
    result = []
    for row in data.get('cards', []):
        if not isinstance(row, dict):
            continue
        try:
            # Explicit whitelist: oracle_text, stats, types and IDs never enter cards.
            result.append(DisplayRecord(str(row['arena_id']), row['english'], row['chinese'],
                          row['set_code'], int(row['primary']), int(row['face_type']),
                          row['source'], row['status']))
        except (KeyError, ValueError, TypeError):
            continue
    return result


def verified_index(cards, records):
    by_id = defaultdict(list)
    for rec in records:
        if (rec.status in TRUSTED and isinstance(rec.english, str)
                and isinstance(rec.chinese, str) and rec.chinese.strip()
                and re.search('[\u3400-\u9fff]', rec.chinese)):
            by_id[rec.arena_id].append(rec)
    indexed = {}
    for aid, card in cards.items():
        if not isinstance(card, dict):
            continue
        def same_face(record, card):
            wanted = int(card.get('linkedfacetype') or 0)
            got = int(record.face_type)
            if got == wanted:
                return True
            # Prepared cards: the live client reports linked face type 19 while
            # 17Lands datasets report 0 for the same single card identity.
            return {got, wanted} == {0, 19}

        matches = [r for r in by_id[str(aid)] if r.english == card.get('name')
                   and r.set_code == card.get('set')
                   and r.primary == card.get('isprimarycard')
                   and same_face(r, card)]
        # Conflicting or unknown printings cannot become trusted via name lookup.
        all_for_id = by_id[str(aid)]
        if not matches or any(r not in matches for r in all_for_id):
            continue
        if len({r.chinese for r in matches}) != 1:
            continue
        indexed[str(aid)] = (identity_key(card), matches[0])
    return indexed


class DisplayIndex:
    def __init__(self):
        self.enabled = False
        self._generation = 0
        self._index = {}
        self._by_identity = {}
        self._queue = queue.SimpleQueue()
        self._lock = threading.Lock()
        self.error = ''
        self.pending = False

    def request(self, cards, source):
        """Called outside scoring. Worker receives independent identity-only copies."""
        snapshot = {str(aid): {k: card.get(k) for k in IDENTITY_FIELDS}
                    for aid, card in cards.items() if isinstance(card, dict)}
        # Deep-copy nested fields before handing them to another thread.
        snapshot = json.loads(json.dumps(snapshot))
        with self._lock:
            self._generation += 1
            generation = self._generation
            self._index, self._by_identity = {}, {}
            self.pending = True
        def work():
            try:
                result, error = verified_index(snapshot, read_source(source)), ''
            except (OSError, ValueError, sqlite3.Error, TypeError) as exc:
                result, error = {}, str(exc)
            self._queue.put((generation, result, error))
        worker = threading.Thread(target=work, daemon=True, name='chinese-display-reader')
        worker.start()
        return worker

    def drain(self):
        changed = False
        while not self._queue.empty():
            generation, indexed, error = self._queue.get()
            with self._lock:
                if generation != self._generation:
                    continue
                by_key = defaultdict(list)
                for key, record in indexed.values():
                    by_key[key].append(record)
                self._index = indexed
                self._by_identity = {k: v[0] for k, v in by_key.items()
                                     if len({r.chinese for r in v}) == 1}
                self.error, self.pending, changed = error, False, True
        return changed

    def name(self, card, arena_id=None, bilingual=True):
        english = str(card.get('name') or 'Unknown')
        if not self.enabled:
            return english
        key = identity_key(card)
        if arena_id is not None:
            value = self._index.get(str(arena_id))
            record = value[1] if value and value[0] == key else None
        else:
            record = self._by_identity.get(key)
        if not record or record.english != english:
            return english
        translated = f'{record.chinese} / {english}' if bilingual else record.chinese
        return RenderedText(translated, english, translated)

    def coverage(self, cards):
        return {'total': len(cards), 'verified_chinese': sum(
            str(aid) in self._index and self._index[str(aid)][0] == identity_key(c)
            for aid, c in cards.items()), 'pending': self.pending, 'error': self.error}


DISPLAY = DisplayIndex()


def localized_name(card, arena_id=None):
    return DISPLAY.name(card, arena_id)


def tooltip_title(card):
    return localized_name(card)


def recommendation_name(english, cards=None):
    # Recommendations carry names; bind to the current raw pack before display.
    matches = [c for c in (cards or []) if c.get('name') == english]
    if not DISPLAY.enabled or not matches or len({identity_key(c) for c in matches}) != 1:
        return english
    return DISPLAY.name(matches[0])
