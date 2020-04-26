from aqt import mw


def gc(arg, fail=False):
    if arg == "fuzzy_panel: shortcut delete":
        return "ctrl+d"
    if arg == "fuzzy_panel: shortcut edit":
        return "ctrl+e"
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail
