'''
Watch files and translate the changes into salt events
'''
# Import python libs
import collections
# Import third party libs
import pyinotify


def _enqueue(revent):
    '''
    Enqueue the event
    '''
    __context__['inotify.queue'].append(revent)


def _get_notifier():
    '''
    Check the context for the notifier and construct it if not present
    '''
    if 'inotify.notifier' in __context__:
        return __context__['inotify.notifier']
    __context__['inotify.queue'] = collections.dequeue()
    wm = pyinotify.WatchManager()
    __context__['inotify.notifier'] = pyinotify.Notifier(wm, _enqueue)
    return __context__['inotify.notifier']

def beacon(config):
    '''
    Watch the configured files
    '''
    ret = []
    notifier = _get_notifier()
    wm = notifier._watch_manager
    # Read in existing events
    # remove watcher files that are not in the config
    # update all existing files with watcher settings
    # return original data
    if notifier.check_events(1):
        notifier.read_events()
        while __context__['inotify.queue']:
            sub = {}
            event = __context__['inotify.queue'].popleft()
            sub['tag'] = event.path
            sub['path'] = event.pathname
            sub['change'] = event.maskname
            ret.append(sub)

    current = set()
    for wd in wm.watches:
        current.add(wm.watches[wd].path)
    need = set(config)
    for path in current.difference(need):
        # These need to be removed
        for wd in wm.watches:
            if path == wm.watches[wd].path:
                wm.rm_watch(wd)
    for path in config:
        mask = config[path].get('mask', pyinotify.ALL_EVENTS)
        rec = config[path].get('rec', False)
        auto_add = config[path].get('auto_add', False)
        # TODO: make the config handle more options
        if not path in current:
            wm.add_watch(
                    path,
                    mask,
                    rec=rec,
                    auto_add=auto_add)
        else:
            for wd in wm.watches:
                if path == wm.watches[wd].path:
                    update = False
                    if wm.watches[wd].mask != mask:
                        update = True
                    if wm.watches[wd].auto_add != auto_add:
                        update = True
                    if update:
                        wm.update_watch(
                                wd,
                                mask=mask,
                                rec=rec,
                                auto_add=auto_add)
    return ret
