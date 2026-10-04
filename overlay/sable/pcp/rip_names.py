"""Readable file names that also work through a Windows SMB share."""
import re


def safe_name(value, fallback='Unknown'):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', ' ', str(value))
    value = ' '.join(value.split()).strip(' .') or fallback
    if re.fullmatch(r'(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', value, re.I):
        value = '_' + value
    return value.encode('utf-8')[:180].decode('utf-8', errors='ignore').rstrip(' .')


def album_name(disc):
    if disc.get('album'):
        return safe_name(' - '.join(v for v in (disc.get('artist'), disc['album']) if v))
    return 'Audio CD ' + disc['id']


def track_name(track, fmt):
    return '%02d - %s.%s' % (track['number'],
        safe_name(track.get('title') or 'Track %02d' % track['number']), fmt)


def new_folder(parent, name):
    index = 1
    while True:
        folder = parent / (name if index == 1 else '%s (%d)' % (name, index))
        try:
            folder.mkdir(mode=0o775)
            return folder
        except FileExistsError:
            index += 1
