"""
Copyright (c): 2018  Rene Schallner
               2019- ijgnd
    
This file (fuzzy_panel.py) is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This file is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this file.  If not, see <http://www.gnu.org/licenses/>.


extracted from https://github.com/renerocksai/sublimeless_zk/tree/6738375c0e371f0c2fde0aa9e539242cfd2b4777/src
mainly from fuzzypanel.py (both Classes) and utils.py (the helper functions from the 
bottom of this file)


This is a pyqt dialog that 
- takes a list or dict
- shows the listitems or dictkeys in a QListWidget that you can filter
- returns select listitem or dictkey/dictvalue

use the class FilterDialog like this:
    d = FilterDialog(parentWindow, dict_, windowtitle)
    if d.exec():
        print(d.selkey)
        print(d.selvalue)  # if input was a dict

syntax for the default search method: 
- strings (separated by space) can be in any order, 
- ! to exclude a string, 
- " to search for space (e.g. "the wind"), 
- _ to indicate that the line must start with this string (e.g. _wind won't match some wind)

"""

from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip, restoreGeom, saveGeom

from .config import gc


class MiniTextEditor(QDialog):
    def __init__(self, parent, val):
        QDialog.__init__(self, parent, Qt.Window)
        self.setWindowTitle("Anki - Edit Saved Debug Console Entry")
        vlay = QVBoxLayout()
        self.textedit = QPlainTextEdit()
        self.textedit.setPlainText(val)
        vlay.addWidget(self.textedit)

        self.button_ok = QPushButton("Ok", self)
        self.button_ok.clicked.connect(self.accept)
        self.button_ok.setToolTip("Ctrl+Return")
        self.button_ok.setShortcut(QKeySequence("Ctrl+Return"))

        self.button_cancel = QPushButton("Cancel", self)
        self.button_cancel.clicked.connect(self.reject)
        self.button_cancel.setToolTip("Esc")

        self.bottombar = QHBoxLayout()
        self.bottombar.addStretch(1)
        self.bottombar.addWidget(self.button_ok)
        self.bottombar.addWidget(self.button_cancel)
        
        vlay.addLayout(self.bottombar)
        self.setLayout(vlay)
        self.resize(800, 350)
        self.textedit.setFocus()
        restoreGeom(self, "debug_code_editor")

    def accept(self):
        saveGeom(self, "debug_code_editor")
        self.val = self.textedit.toPlainText()
        QDialog.accept(self)


class PanelInputLine(QLineEdit):
    down_pressed = pyqtSignal()
    up_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        mod = mw.app.keyboardModifiers() & Qt.ControlModifier
        key = event.key()
        if key == Qt.Key_Down:
            self.down_pressed.emit()
        elif key == Qt.Key_Up:
            self.up_pressed.emit()
        elif mod and (key == Qt.Key_N):
            self.down_pressed.emit()
        elif mod and (key == Qt.Key_P):
            self.up_pressed.emit()
        elif mod and (key == Qt.Key_H):
            self.up_pressed.emit()
        # when PanelInputLine is focused Ctrl+E doesn't work so I seem to need this
        # on the other hand ctlr+d seems to always work irrespective of the following code??
        elif mod and (key == Qt.Key_E):
            self.parent.on_edit()
        elif mod and (key == Qt.Key_D):
            self.parent.on_delete()


class FilterDialog(QDialog):
    def __init__(self, parent=None, values=None, windowtitle="Anki Filter", max_items=2000, prefill=""):
        super().__init__(parent)
        self.parent = parent
        self.max_items = max_items
        self.setObjectName("FilterDialog")
        if windowtitle:
            self.setWindowTitle(windowtitle)
        if isinstance(values, dict):
            self.dict = values
            self.keys = sorted(self.dict.keys())
        else:
            self.dict = False
            self.keys = sorted(values)
        self.fuzzy_items = self.keys[:max_items]
        self.initUI()
        if prefill:
            self.input_line.setText(prefill)

    def initUI(self):
        self.vlay = QVBoxLayout()
        self.input_line = PanelInputLine(self)
        self.list_box = QListWidget()
        for i in range(self.max_items):
            self.list_box.insertItem(i, '')
        self.vlay.addWidget(self.input_line)
        self.vlay.addWidget(self.list_box)

        self.button_del = QPushButton("Delete", self)
        self.button_del.clicked.connect(self.on_delete)
        delcut = gc("fuzzy_panel: shortcut delete")
        if delcut:
            self.button_del.setShortcut(QKeySequence(delcut))
            self.button_del.setToolTip(delcut)

        self.button_edit = QPushButton("Edit", self)
        self.button_edit.clicked.connect(self.on_edit)
        editcut = gc("fuzzy_panel: shortcut edit")
        if editcut:
            self.button_edit.setShortcut(QKeySequence(editcut))
            self.button_edit.setToolTip(editcut)

        self.button_ok = QPushButton("Overwrite", self)
        self.button_ok.clicked.connect(self.accept)
        self.button_ok.setToolTip("Ctrl+Return")
        self.button_ok.setShortcut(QKeySequence("Ctrl+Return"))
        # self.button_ok.setAutoDefault(True)

        self.append = False
        self.button_append = QPushButton("Append (default)", self)
        self.button_append.clicked.connect(self.set_append_and_accept)
        self.button_append.setToolTip("Return")
        
        self.button_cancel = QPushButton("Cancel", self)
        self.button_cancel.clicked.connect(self.reject)
        self.button_cancel.setToolTip("Esc")

        self.bottombar = QHBoxLayout()
        self.bottombar.addWidget(self.button_del)
        self.bottombar.addWidget(self.button_edit)
        self.bottombar.addStretch(1)
        self.bottombar.addWidget(self.button_ok)
        self.bottombar.addWidget(self.button_append)
        self.bottombar.addWidget(self.button_cancel)
        
        self.vlay.addLayout(self.bottombar)
        
        self.update_listbox()
        self.setLayout(self.vlay)
        self.resize(800, 350)
        restoreGeom(self, "debug_history")
        self.list_box.setAlternatingRowColors(True)

        # connections
        self.input_line.textChanged.connect(self.text_changed)
        self.input_line.returnPressed.connect(self.return_pressed)
        self.input_line.down_pressed.connect(self.down_pressed)
        self.input_line.up_pressed.connect(self.up_pressed)
        self.list_box.itemDoubleClicked.connect(self.item_doubleclicked)
        self.list_box.installEventFilter(self)
        self.input_line.setFocus()

    def on_delete(self):
        row = self.list_box.currentRow()
        del self.fuzzy_items[row]
        del self.keys[row]
        self.update_listbox()

    def on_edit(self):
        row = self.list_box.currentRow()
        val = self.fuzzy_items[row]
        m = MiniTextEditor(self, val)
        if m.exec():
            self.fuzzy_items[row] = m.val
            self.keys[row] = m.val
            self.update_listbox()

    def reject(self):
        saveGeom(self, "debug_history")
        QDialog.reject(self)

    def accept(self):
        if len(self.fuzzy_items) > 0:
            row = self.list_box.currentRow()
            self.selkey = self.fuzzy_items[row]
            if self.dict:
                self.selvalue = self.dict[self.selkey]
            saveGeom(self, "debug_history")
            QDialog.accept(self)
        else:
            tooltip('nothing selected. Aborting ...')
            return

    def set_append_and_accept(self):
        if not len(self.fuzzy_items) > 0:
            tooltip('nothing selected. Aborting ...')
            return   
        self.append = True
        self.accept()

    def update_listbox(self):
        for i in range(self.max_items):
            item = self.list_box.item(i)
            if i < len(self.fuzzy_items):
                item.setHidden(False)
                item.setText(self.fuzzy_items[i])
            else:
                item.setHidden(True)
        self.list_box.setCurrentRow(0)

    def text_changed(self):
        search_string = self.input_line.text()
        FILTER_WITH = "slzk_mod"   # "slzk", "fuzzyfinder"
        if FILTER_WITH == "fuzzyfinder":  # https://pypi.org/project/fuzzyfinder/
            if search_string:
                self.fuzzy_items = list(fuzzyfinder(search_string, self.keys))[:self.max_items]   
            else:
                self.fuzzy_items = list(self.keys)[:self.max_items]
        else:
            if not search_string:
                search_string = ""
            if FILTER_WITH == "slzk_mod":
                self.fuzzy_items = process_search_string_withStart(search_string, self.keys, self.max_items)
            elif FILTER_WITH == "slzk":
                self.fuzzy_items = process_search_string(search_string, self.keys, self.max_items)
        self.update_listbox()

    def up_pressed(self):
        row = self.list_box.currentRow()
        if row == 0:
            self.list_box.setCurrentRow(len(self.fuzzy_items) - 1) 
        else:
            self.list_box.setCurrentRow(row - 1)

    def down_pressed(self):
        row = self.list_box.currentRow()
        if row == len(self.fuzzy_items) - 1:
            self.list_box.setCurrentRow(0)
        else:
            self.list_box.setCurrentRow(row + 1)

    def return_pressed(self):
        self.set_append_and_accept()

    def item_doubleclicked(self):
        self.set_append_and_accept()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.KeyPress and event.matches(QKeySequence.InsertParagraphSeparator):
            self.return_pressed()
            return True
        # https://stackoverflow.com/questions/48890473/how-do-i-make-a-context-menu-for-each-item-in-a-qlistwidget
        elif (event.type() == QEvent.ContextMenu and watched is self.list_box):
            menu = QMenu()
            d = menu.addAction("delete")
            d.triggered.connect(self.on_delete)
            e = menu.addAction("edit")
            e.triggered.connect(self.on_edit)
            menu.exec_(QCursor.pos())
            return True
        else:
            return QWidget.eventFilter(self, watched, event)


def process_search_string_withStart(search_terms, keys, max):
    """inspired by find_in_files from sublimelesszk"""
    search_terms = split_search_terms_withStart(search_terms)
    results = []
    for lent in keys:
        for presence, atstart, term in search_terms:
            if term.islower():
                i = lent.lower()
            else:
                i = lent

            # if presence and term not in i:
                # break
            # elif not presence and term in i:
                # break
                
            if presence:
                if term not in i:
                    break
                elif atstart and not i.startswith(term):
                    break
            else:   # not in
                if term in i:
                    break
                elif atstart and i.startswith(term):
                    break
        else:
            results.append(lent)
    return results
    

def split_search_terms_withStart(search_string):
    """
    Split a search-spec (for find in files) into tuples:
    (posneg, string)
    posneg: True: must be contained, False must not be contained
    string: what must (not) be contained
    """
    in_quotes = False
    in_neg = False

    at_start = False

    pos = 0
    str_len = len(search_string)
    results = []
    current_snippet = ''

    literal_quote_sign = '"'
    exclude_sign = '!'
    startswith_sign = "_" 

    while pos < str_len:
        if search_string[pos:].startswith(literal_quote_sign):
            in_quotes = not in_quotes
            if not in_quotes:
                # finish this snippet
                if current_snippet:
                    results.append((in_neg, at_start, current_snippet))
                in_neg = False
                current_snippet = ''
            pos += 1
        elif search_string[pos:].startswith(exclude_sign) and not in_quotes and not current_snippet:
            in_neg = True
            pos += 1
        elif search_string[pos:].startswith(startswith_sign) and not in_quotes and not current_snippet:
            at_start = True
            pos += 1
        elif search_string[pos] in (' ', '\t') and not in_quotes:
            # push current snippet
            if current_snippet:
                results.append((in_neg, at_start, current_snippet))
            in_neg = False
            at_start = False
            current_snippet = ''
            pos += 1
        else:
            current_snippet += search_string[pos]
            pos += 1
    if current_snippet:
        results.append((in_neg, at_start, current_snippet))
    return [(not in_neg, at_start, s) for in_neg, at_start, s in results]


def process_search_string(search_terms, keys, max):
    """inspired by find_in_files from sublimelesszk"""
    search_terms = split_search_terms(search_terms)
    results = []
    for lent in keys:
        for presence, term in search_terms:
            if term.islower():
                i = lent.lower()
            else:
                i = lent
            if presence and term not in i:
                break
            elif not presence and term in i:
                break
        else:
            results.append(lent)
    return results


def split_search_terms(search_string):
    """
    Split a search-spec (for find in files) into tuples:
    (posneg, string)
    posneg: True: must be contained, False must not be contained
    string: what must (not) be contained
    """
    in_quotes = False
    in_neg = False
    pos = 0
    str_len = len(search_string)
    results = []
    current_snippet = ''
    while pos < str_len:
        if search_string[pos:].startswith('"'):
            in_quotes = not in_quotes
            if not in_quotes:
                # finish this snippet
                if current_snippet:
                    results.append((in_neg, current_snippet))
                in_neg = False
                current_snippet = ''
            pos += 1
        elif search_string[pos:].startswith('!') and not in_quotes and not current_snippet:
            in_neg = True
            pos += 1
        elif search_string[pos] in (' ', '\t') and not in_quotes:
            # push current snippet
            if current_snippet:
                results.append((in_neg, current_snippet))
            in_neg = False
            current_snippet = ''
            pos += 1
        else:
            current_snippet += search_string[pos]
            pos += 1
    if current_snippet:
        results.append((in_neg, current_snippet))
    return [(not in_neg, s) for in_neg, s in results]
