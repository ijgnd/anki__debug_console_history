"""
Anki Add-on "Debug Console History/Filter"

Copyright (c):  2019- ijgnd

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


This add-on incorporates the file fuzzy_panel.py which has this copyright and permission notice:

    Copyright (c): 2018  Rene Schallner (sublimeless_zk)
                   2019- ijgnd
        
    fuzzy_panel.py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import pickle

from aqt import gui_hooks
from aqt import mw
from aqt.qt import (
    QAction,
    QKeySequence,
    QShortcut,
    QSplitter,
    QPlainTextEdit,
)
from aqt.utils import (
    getOnlyText,
    tooltip,
)
from .config import gc
from .fuzzy_panel import FilterDialog


addon_path = os.path.dirname(__file__)
user_files_folder = os.path.join(addon_path, "user_files")
debug_saved = os.path.join(user_files_folder, "debug_contents.python_pickle")


def loaddict():
    if os.path.isfile(debug_saved):
        with open(debug_saved, 'rb') as PO:
            try:
                mw.recent_debugs = pickle.load(PO)
            except:
                mw.recent_debugs = []
    else:
        mw.recent_debugs = []


def savedict():
    # prevent error after deleting add-on
    if os.path.exists(os.path.join(addon_path, "fuzzy_panel.py")):
        with open(debug_saved, 'wb') as PO:
            pickle.dump(mw.recent_debugs, PO)


gui_hooks.profile_did_open.append(loaddict)
gui_hooks.profile_will_close.append(savedict)


def text_from_dc_instance(dc_instance):
    for c in dc_instance.children():
        if isinstance(c, QSplitter):
            splitter = c
            break    
    for c in splitter.children():
        if isinstance(c, QPlainTextEdit):
            if c.objectName() == "text":
                text = c
            if c.objectName() == "log":
                log = c
    return text


def history_helper(dc_instance):
    text = text_from_dc_instance(dc_instance)
    d = FilterDialog(parent=dc_instance, values=mw.recent_debugs)
    if d.exec():
        mw.recent_debugs = d.keys
        if d.append:
            new = "\n" + d.selkey
        else:
            text.clear()
            new = d.selkey
        text.textCursor().insertText(new)


def save_current(dc_instance):
    t = ""
    if gc("debug console: ask for comment before saving", True):
        user = getOnlyText("Add unique comment to find the snippet later")
        if user:
            t = user + '\n'
            if not user.startswith('#'):
                t = '#' + t               
    text = text_from_dc_instance(dc_instance)
    code = t + text.toPlainText()
    mw.recent_debugs.append(code)


def extend_debug_console(dc_instance):
    cut = gc("debug console: shortcut open history window", "ctrl+i")
    if cut:
        hist_window = QShortcut(QKeySequence(cut), dc_instance)
        hist_window.activated.connect(lambda d=dc_instance: history_helper(d))
    cut = gc("debug console: shortcut save", "ctrl+s")
    if cut:
        save = QShortcut(QKeySequence(cut), dc_instance)
        save.activated.connect(lambda d=dc_instance: save_current(d))

gui_hooks.debug_console_will_show.append(extend_debug_console)
