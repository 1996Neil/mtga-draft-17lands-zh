"""Retain English per rendered control; never translate machine variables/rows."""
import tkinter as tk
from tkinter import ttk
from src.i18n import tr, RenderedText


def _source(value):
    return value.english if isinstance(value, RenderedText) else str(value)


def _remember(widget, key, value):
    if not hasattr(widget, '_language_sources'):
        widget._language_sources = {}
    if isinstance(value, RenderedText):
        widget._language_sources[key] = value
    else:
        widget._language_sources.pop(key, None)


# Tk converts text to a plain Tcl string. Capture its source before that boundary.
# This is necessary because distinct English phrases can share a Chinese phrase.
if not getattr(tk.Misc, '_display_language_hook', False):
    _options = tk.Misc._options
    def options(self, cnf, kw=None):
        merged = dict(cnf or {});merged.update(kw or {})
        if 'text' in merged:
            _remember(self, ('text',), merged['text'])
        return _options(self, cnf, kw)
    tk.Misc._options = options

    _menu_add = tk.Menu.add
    def menu_add(self, itemType, cnf={}, **kw):
        result = _menu_add(self, itemType, cnf, **kw)
        label = kw.get('label', cnf.get('label'))
        if label is not None:
            _remember(self, ('menu', str(self.index('end'))), label)
        return result
    tk.Menu.add = menu_add
    _menu_entry = tk.Menu.entryconfigure
    def menu_entry(self, index, cnf=None, **kw):
        label = kw.get('label', (cnf or {}).get('label'))
        if label is not None:
            _remember(self, ('menu', str(self.index(index))), label)
        return _menu_entry(self, index, cnf, **kw)
    tk.Menu.entryconfigure = tk.Menu.entryconfig = menu_entry

    _nb_add = ttk.Notebook.add
    def nb_add(self, child, **kw):
        if 'text' in kw:
            _remember(self, ('tab', str(child)), kw['text'])
        return _nb_add(self, child, **kw)
    ttk.Notebook.add = nb_add
    _nb_tab = ttk.Notebook.tab
    def nb_tab(self, tab_id, option=None, **kw):
        if 'text' in kw:
            _remember(self, ('tab', self.tabs()[self.index(tab_id)]), kw['text'])
        return _nb_tab(self, tab_id, option, **kw)
    ttk.Notebook.tab = nb_tab

    _heading = ttk.Treeview.heading
    def heading(self, column, option=None, **kw):
        if 'text' in kw:
            _remember(self, ('heading', str(column)), kw['text'])
        return _heading(self, column, option, **kw)
    ttk.Treeview.heading = heading
    _title = tk.Wm.wm_title
    def title(self, string=None):
        if string is not None:
            _remember(self, ('title',), string)
        return _title(self, string)
    tk.Wm.wm_title = tk.Wm.title = title
    tk.Misc._display_language_hook = True


def refresh_language(root):
    """Re-render static controls from their own source, preserving all UI state."""
    def visit(widget):
        for key, english in list(getattr(widget, '_language_sources', {}).items()):
            try:
                text = tr(english)
                kind = key[0]
                if kind == 'text':
                    if 'text' in widget.keys() and not ('textvariable' in widget.keys() and widget.cget('textvariable')):
                        widget.configure(text=text)
                elif kind == 'menu':
                    if widget.type(key[1]) not in ('separator','tearoff'):
                        widget.entryconfigure(key[1], label=text)
                elif kind == 'tab' and key[1] in widget.tabs():
                    widget.tab(key[1], text=text)
                elif kind == 'heading':
                    widget.heading(key[1], text=text)
                elif kind == 'title':
                    widget.title(text)
            except tk.TclError:
                # A tab/menu/widget can have been removed since it was recorded.
                continue
        for child in widget.winfo_children():
            visit(child)
        refresh = getattr(widget, "refresh_localized_view", None)
        if callable(refresh):
            refresh()
    visit(root)
