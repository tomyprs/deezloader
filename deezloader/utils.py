#!/usr/bin/python3
import mutagen
from Crypto.Hash import MD5
from binascii import a2b_hex, b2a_hex
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, USLT
from Crypto.Cipher import AES, Blowfish
def md5hex(data):
    h = MD5.new()
    h.update(data)
    return b2a_hex(h.digest())
def genurl(md5, quality, ids, media):
    data = b"\xa4".join(a.encode() for a in [md5, quality, ids, str(media)])
    data = b"\xa4".join([md5hex(data), data]) + b"\xa4"
    if len(data) % 16:
     data += b"\x00" * (16 - len(data) % 16)
    c = AES.new("jo6aey6haid2Teih", AES.MODE_ECB)
    c = b2a_hex(c.encrypt(data)).decode()
    return c
def calcbfkey(songid):
    h = md5hex(b"%d" % int(songid))
    key = b"g4el58wc0zvf9na1"
    return "".join(chr(h[i] ^ h[i + 16] ^ key[i]) for i in range(16))
def blowfishDecrypt(data, key):
    c = Blowfish.new(key, Blowfish.MODE_CBC, a2b_hex("0001020304050607"))
    return c.decrypt(data)
def decryptfile(fh, key, fo):
    seg = 0
    for data in fh:
        if not data:
         break
        if (seg % 3) == 0 and len(data) == 2048:
         data = blowfishDecrypt(data, key)
        fo.write(data)
        seg += 1
def write_tags(song, data):
    try:
       tag = FLAC(song)
       tag.delete()
       images = Picture()
       images.type = 3
       images.data = data['image']
       tag.add_picture(images)
       tag['lyrics'] = data['lyric']
    except mutagen.flac.FLACNoHeaderError:
       tag = mutagen.File(song, easy=True)
    tag['artist'] = data['artist']
    tag['title'] = data['music']
    tag['date'] = data['year']
    tag['album'] = data['album']
    tag['tracknumber'] = data['tracknum']
    tag['discnumber'] = data['discnum']
    tag['genre'] = data['genre']
    tag['albumartist'] = data['ar_album']
    tag['author'] = data['author']
    tag['composer'] = data['composer']
    tag['copyright'] = data['copyright']
    tag['bpm'] = data['bpm']
    tag['length'] = data['duration']
    tag['organization'] = data['label']
    tag['isrc'] = data['isrc']
    tag['replaygain_*_gain'] = data['gain']
    tag['lyricist'] = data['lyricist']
    tag.save()
    try:
       audio = ID3(song)
       audio['APIC'] = APIC(encoding=3, mime="image/jpeg", type=3, desc=u"Cover", data=data['image']) 
       audio['USLT'] = USLT(encoding=3, lang=u"eng", desc=u"desc", text=data['lyric'])
       audio.save()
    except mutagen.id3._util.ID3NoHeaderError:
       pass