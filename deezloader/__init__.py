#!/usr/bin/python3
import os
import mutagen
import spotipy
import requests
from tqdm import tqdm
from Crypto.Hash import MD5
from bs4 import BeautifulSoup
import spotipy.oauth2 as oauth2
from mutagen.id3 import ID3, APIC
from collections import OrderedDict
from binascii import a2b_hex, b2a_hex
from mutagen.flac import FLAC, Picture
from Crypto.Cipher import AES, Blowfish
localdir = os.getcwd()
def generate_token():
    token = oauth2.SpotifyClientCredentials(client_id="4fe3fecfe5334023a1472516cc99d805", client_secret="0f02b7c483c04257984695007a4a8d5c").get_access_token()
    return token
token = generate_token()
spo = spotipy.Spotify(auth=token)
header = {"Accept-Language": "en-US,en;q=0.5"}
params = {
          "api_version": "1.0",
          "api_token": "null",
          "input": "3",
          "method": "deezer.getUserData"
}
class TrackNotFound(Exception):
      def __init__(self, message):
          super().__init__(message)
class AlbumNotFound(Exception):
      def __init__(self, message):
          super().__init__(message)
class InvalidLink(Exception):
      def __init__(self, message):
          super().__init__(message)
class BadCredentials(Exception):
      def __init__(self, message):
          super().__init__(message)
class QuotaExceeded(Exception):
      def __init__(self, message):
          super().__init__(message)
class QualityNotFound(Exception):
      def __init__(self, message):
          super().__init__(message)
class Login:
      def __init__(self, mail, password):
          self.req = requests.Session()
          check = self.req.post("http://www.deezer.com/ajax/gw-light.php", params).json()['results']['checkFormLogin']
          post_data = {
                       "type": "login",
                       "mail": mail,
                       "password": password,
                       "checkFormLogin": check
          }
          if "success" == self.req.post("https://www.deezer.com/ajax/action.php", post_data).text:
           print("Success, you are in")
          else:
              raise BadCredentials("Invalid password or username")
      def request(self, url, control=False):
          try:
             thing = requests.get(url, headers=header)
          except:
             thing = requests.get(url, headers=header)
          if control == True:
           try:
              if thing.json()['error']:
               raise InvalidLink("Invalid link ;)")
           except KeyError:
              pass
           try:
              if thing.json()['error']['message'] == "Quota limit exceeded":
               raise QuotaExceeded("Too much requests limit yourself")
           except KeyError:
              pass
           try:
              if thing.json()['error']['message'] == "no data":
               raise TrackNotFound("Track not found: " + song)
           except KeyError:
              pass
          return thing
      def write_tags(self, song, data):
          try:
             tag = mutagen.File(song, easy=True)
             tag.add_tags()
          except mutagen.flac.FLACVorbisError:
             tag = FLAC(song)
             tag.delete()
             images = Picture()
             images.type = 3
             images.data = image
             tag.add_picture(images)
          except mutagen.id3._util.error:
             pass
          tag['artist'] = data['artist']
          tag['title'] = data['music']
          tag['date'] = data['year']
          tag['album'] = data['album']
          tag['tracknumber'] = data['tracknum']
          tag['discnumber'] = data['discnum']
          tag['genre'] = " & ".join(data['genre'])
          tag['albumartist'] = data['ar_album']
          tag.save()
          try:
             audio = ID3(song)
             audio['APIC'] = APIC(encoding=3, mime="image/jpeg", type=3, desc=u"Cover", data=data['image'])
             audio.save()
          except mutagen.id3._util.ID3NoHeaderError:
             pass
      def download(self, track, location, quality, check):
          ids = track.split("/")[-1]
          def login():
              try:
                 token = self.req.post("http://www.deezer.com/ajax/gw-light.php", params).json()['results']['checkForm']
              except:
                 token = self.req.post("http://www.deezer.com/ajax/gw-light.php", params).json()['results']['checkForm']
              data = {
                      "api_version": "1.0",
                      "input": "3",
                      "api_token": token,
                      "method": "song.getData"
              }
              param = {"sng_id": ids}
              try:
                 return self.req.post("http://www.deezer.com/ajax/gw-light.php", json=param, params=data).json()
              except:
                 return self.req.post("http://www.deezer.com/ajax/gw-light.php", json=param, params=data).json()
          def md5hex(data):
              h = MD5.new()
              h.update(data)
              return b2a_hex(h.digest())
          def genurl(md5, quality, media):
              data = b"\xa4".join(a.encode() for a in [md5, quality, str(ids), str(media)])
              data = b"\xa4".join([md5hex(data), data]) + b"\xa4"
              if len(data) % 16:
               data += b"\x00" * (16 - len(data) % 16)
              c = AES.new("jo6aey6haid2Teih", AES.MODE_ECB)
              c = b2a_hex(c.encrypt(data)).decode()
              return "https://e-cdns-proxy-%s.dzcdn.net/mobile/1/%s" % (md5[0], c)
          def calcbfkey(songid):
              h = md5hex(b"%d" % int(songid))
              key = b"g4el58wc0zvf9na1"
              return "".join(chr(h[i] ^ h[i + 16] ^ key[i]) for i in range(16))
          def blowfishDecrypt(data, key):
              c = Blowfish.new(key, Blowfish.MODE_CBC, a2b_hex("0001020304050607"))
              return c.decrypt(data)
          def decryptfile(fh, key, fo):
              i = 0
              for data in fh:
                  if not data:
                   break
                  if (i % 3) == 0 and len(data) == 2048:
                   data = blowfishDecrypt(data, key)
                  fo.write(data)
                  i += 1
          infos = login()
          while not "MD5_ORIGIN" in str(infos):
              infos = login()
          extension = ".mp3"
          try:
             if int(infos['results']['FILESIZE_' + quality]) > 0 and quality == "FLAC":
              quality = "9"
              extension = ".flac"
              qualit = "FLAC"
             elif int(infos['results']['FILESIZE_' + quality]) > 0 and quality == "MP3_320":
              quality = "3"
              qualit = "320"
             elif int(infos['results']['FILESIZE_' + quality]) > 0 and quality == "MP3_256":
              quality = "5"
              qualit = "256"
             elif int(infos['results']['FILESIZE_' + quality]) > 0 and quality == "MP3_128":
              quality = "1"
              qualit = "128"
             else:
                 if check == True:
                  raise QualityNotFound("The quality chose can't be downloaded")
                 quality = "1"
                 qualit = "MP3_128"
          except KeyError:
             if check == True:
              raise QualityNotFound("The quality chose can't be downloaded")
             quality = "1"
             qualit = "MP3_128"
          crypt = self.request(genurl(infos['results']['MD5_ORIGIN'], quality, infos['results']['MEDIA_VERSION']))
          if len(crypt.content) == 0:
           raise TrackNotFound("")
          open(location + ids, "wb").write(crypt.content)
          decry = open(location + ids, "wb")
          decryptfile(crypt.iter_content(2048), calcbfkey(ids), decry)
          return extension, qualit
      def download_trackdee(self, URL, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          datas = {}
          array = []
          if "?utm" in URL:
           URL, a = URL.split("?utm")
          URL1 = "https://www.deezer.com/track/" + URL.split("/")[-1]
          URL2 = "https://api.deezer.com/track/" + URL.split("/")[-1]
          url = self.request(URL2, True).json()
          url1 = self.request("http://api.deezer.com/album/" + str(url['album']['id']), True).json()
          try:
             image = url['album']['cover_xl'].replace("1000x1000", "1200x1200")
          except AttributeError:
             image = self.request(URL1).text
             image = BeautifulSoup(image, "html.parser").find("img", class_="img_main").get("src").replace("120x120", "1200x1200")
          image = self.request(image).content
          if len(image) == 13:
           image = self.request("https://e-cdns-images.dzcdn.net/images/cover/1200x1200-000000-80-0-0.jpg").content
          datas['image'] = image
          datas['music'] = url['title']
          for a in url['contributors']:
              array.append(a['name'])
          if len(array) > 1:
           for a in array:
               for b in array:
                   if a in b and a != b:
                    array.remove(b)
          while len(", ".join(array)) + len(datas['music']) >= 240:
              del array[-1]
          if len(array) == 0:
           array.append("Unknown")
          datas['artist'] = ", ".join(OrderedDict.fromkeys(array))
          datas['album'] = url1['title']
          datas['tracknum'] = str(url['track_position'])
          datas['discnum'] = str(url['disk_number'])
          datas['year'] = url['release_date']
          song = datas['music'] + " - " + datas['artist']
          datas['genre'] = []
          try:
             for a in url1['genres']['data']:
                 datas['genre'].append(a['name'])
          except KeyError:
             pass
          datas['ar_album'] = url1['artist']['name']
          dir = str(output) + "/" + datas['artist'].replace("/", "").replace("$", "S") + "/"
          try:
             os.makedirs(dir)
          except FileExistsError:
             pass
          name = datas['artist'].replace("/", "").replace("$", "S") + " " + datas['music'].replace("/", "").replace("$", "S")
          if os.path.isfile(dir + name):
           if check == False:
            return dir + name
           ans = input("Song already exist do you want to redownload it?(y or n):")
           if ans != "y":
            return
          print("\nDownloading:" + song)
          try:
             extension, qualit = self.download(URL, dir, quality, recursive)
          except TrackNotFound:
             url = self.request("https://api.deezer.com/search/track/?q=" + datas['music'].replace("#", "") + " + " + datas['artist'].replace("#", ""), True).json()
             try:
                for a in range(url['total'] + 1):
                    if url['data'][a]['title'] == datas['music'] or url['data'][a]['title_short'] in datas['music']:
                     URL = url['data'][a]['link']
                     break
             except IndexError:
                try:
                   url = self.request("https://api.deezer.com/search/track/?q=" + datas['music'].replace("#", "").split(" ")[0] + " + " + datas['artist'].replace("#", ""), True).json()
                   for a in range(url['total'] + 1):
                       if datas['music'].split(" ")[0] in url['data'][a]['title']:
                        URL = url['data'][a]['link']
                        break
                except IndexError:
                   raise TrackNotFound("Track not found: " + song)
             extension, qualit = self.download(URL, dir, quality, recursive)
          name += " (" + qualit + ")" + extension
          os.rename(dir + URL.split("/")[-1], dir + name)
          self.write_tags(dir + name, datas)
          return dir + name
      def download_albumdee(self, URL, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          datas = {}
          array = []
          music = []
          artist = []
          album = []
          tracknum = []
          discnum = []
          year = []
          genre = []
          ar_album = []
          urls = []
          names = []
          if "?utm" in URL:
           URL, a = URL.split("?utm")
          URL1 = "https://www.deezer.com/album/" + URL.split("/")[-1]
          URL2 = "https://api.deezer.com/album/" + URL.split("/")[-1]
          url = self.request(URL2, True).json()
          try:
             image = url['cover_xl'].replace("1000x1000", "1200x1200")
          except AttributeError:
             image = self.request(URL1).text
             image = BeautifulSoup(image, "html.parser").find("img", class_="img_main").get("src").replace("120x120", "1200x1200")
          image = self.request(image).content
          if len(image) == 13:
           image = self.request("https://e-cdns-images.dzcdn.net/images/cover/1200x1200-000000-80-0-0.jpg").content
          datas['image'] = image
          for a in url['tracks']['data']:
              del array[:]
              music.append(a['title'])
              urls.append(a['link'])
              ur = self.request("https://api.deezer.com/track/" + str(a['id']), True).json()
              tracknum.append(str(ur['track_position']))
              discnum.append(str(ur['disk_number']))
              for a in ur['contributors']:
                  array.append(a['name'])
              if len(array) > 1:
               for a in array:
                   for b in array:
                       if a in b and a != b:
                        array.remove(b)
              while len(", ".join(array)) + len(max(music)) >= 240:
                  del array[-1]
              if len(array) == 0:
               array.append("Unknown")
              artist.append(", ".join(OrderedDict.fromkeys(array)))
          datas['album'] = url['title']
          datas['year'] = url['release_date']
          datas['genre'] = []
          try:
             for a in url['genres']['data']:
                 datas['genre'].append(a['name'])
          except KeyError:
             pass
          datas['ar_album'] = url['artist']['name']
          dir = str(output) + "/" + datas['album'].replace("/", "").replace("$", "S") + "/"
          try:
             os.makedirs(dir)
          except FileExistsError:
             pass
          for a in tqdm(range(len(urls))):
              name = artist[a].replace("/", "").replace("$", "S") + " " + music[a].replace("/", "").replace("$", "S")
              if os.path.isfile(dir + name):
               if check == False:
                continue
               print(dir + name)
               ans = input("Song already exist do you want to redownload it?(y or n):")
               if not ans == "y":
                return
              try:
                 extension, qualit = self.download(urls[a], dir, quality, recursive)
              except TrackNotFound:
                 url = self.request("https://api.deezer.com/search/track/?q=" + music[a].replace("#", "") + " + " + artist[a].replace("#", ""), True).json()
                 try:
                    for b in range(url['total'] + 1):
                        if url['data'][b]['title'] == music[a] or url['data'][b]['title_short'] in music[a]:
                         URL = url['data'][b]['link']
                         break
                 except IndexError:
                    try:
                       url = self.request("https://api.deezer.com/search/track/?q=" + music[a].replace("#", "").split(" ")[0] + " + " + artist[a].replace("#", ""), True).json()
                       for b in range(url['total'] + 1):
                           if music[a].split(" ")[0] in url['data'][b]['title']:
                            URL = url['data'][b]['link']
                            break
                    except IndexError:
                       print("\nTrack not found: " + music[a] + " - " + artist[a])
                       continue
                 extension, qualit = self.download(URL, dir, quality, recursive)
                 urls[a] = URL
              name += " (" + qualit + ")" + extension
              names.append(dir + name)
              os.rename(dir + urls[a].split("/")[-1], dir + name)
              datas['artist'] = artist[a]
              datas['music'] = music[a]
              datas['tracknum'] = tracknum[a]
              datas['discnum'] = discnum[a]
              self.write_tags(names[a], datas)
          return names
      def download_playlistdee(self, URL, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          array = []
          if "?utm" in URL:
           URL, a = URL.split("?utm")
          url = self.request("https://api.deezer.com/playlist/" + URL.split("/")[-1], True).json()
          for a in url['tracks']['data']:
              try:
                 array.append(self.download_trackdee(a['link'], output, check, quality, recursive))
              except TrackNotFound:
                 print("\nTrack not found " + a['title'])
                 array.append(output + a['title'] + "/" + a['title'])
          return array
      def download_trackspo(self, URL, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          global spo
          if "?" in URL:
           URL,a = URL.split("?")
          try:
             url = spo.track(URL)
          except Exception as a:
             if not "The access token expired" in str(a):
              raise InvalidLink("Invalid link ;)")
             token = generate_token()
             spo = spotipy.Spotify(auth=token)
             url = spo.track(URL)
          try:
             isrc = url['external_ids']['isrc']
          except KeyError:
             raise TrackNotFound("Cannot convert to a Deezer link :(")
          url = self.request("https://api.deezer.com/track/isrc:" + isrc, True).json()
          try:
             name = self.download_trackdee(url['link'], output, check, quality, recursive)
             return name
          except KeyError:
             raise TrackNotFound("Track not found :(")
      def download_albumspo(self, URL, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          global spo
          if "?" in URL:
           URL,a = URL.split("?")
          try:
             tracks = spo.album(URL)
          except Exception as a:
             if not "The access token expired" in str(a):
              raise InvalidLink("Invalid link ;)")
             token = generate_token()
             spo = spotipy.Spotify(auth=token)
             tracks = spo.album(URL)
          upc = tracks['external_ids']['upc']
          while upc[0] == "0":
              upc = upc[1:]
          url = self.request("https://api.deezer.com/album/upc:" + upc).json()
          try:
             names = self.download_albumdee(url['link'], output, check, quality, recursive)
             return names
          except KeyError:
             raise AlbumNotFound("Album not found :(")
      def download_playlistspo(self, URL, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          global spo
          array = []
          if "?" in URL:
           URL,a = URL.split("?")
          URL = URL.split("/")
          try:
             tracks = spo.user_playlist_tracks(URL[-3], playlist_id=URL[-1])
          except Exception as a:
             if not "The access token expired" in str(a):
              raise InvalidLink("Invalid link ;)")
             token = generate_token()
             spo = spotipy.Spotify(auth=token)
             tracks = spo.user_playlist_tracks(URL[-3], playlist_id=URL[-1])
          for a in tracks['items']:
              try:
                 array.append(self.download_trackspo(a['track']['external_urls']['spotify'], output, check, quality, recursive))
              except TrackNotFound:
                 print("\nTrack not found " + a['track']['name'])
                 array.append(output + a['track']['name'] + "/" + a['track']['name'])
          if tracks['total'] != 100:
           for a in range(tracks['total'] // 100):
               try:
                  tracks = spo.next(tracks)
               except:
                  token = generate_token()
                  spo = spotipy.Spotify(auth=token)
                  tracks = spo.next(tracks)
               for a in tracks['items']:
                   try:
                      array.append(self.download_trackspo(a['track']['external_urls']['spotify'], output, check, quality, recursive))
                   except:
                      print("\nTrack not found " + a['track']['name'])
                      array.append(output + a['track']['name'] + "/" + a['track']['name'])
          return array
      def download_name(self, artist, song, output=localdir + "/Songs/", check=True, quality="MP3_320", recursive=True):
          global spo
          try:
             search = spo.search(q="track:" + song + " artist:" + artist)
          except:
             token = generate_token()
             spo = spotipy.Spotify(auth=token)
             search = spo.search(q="track:" + song + " artist:" + artist)
          try:
             return self.download_trackspo(search['tracks']['items'][0]['external_urls']['spotify'], output, check, quality=quality, recursive=recursive)
          except IndexError:
             raise TrackNotFound("Track not found: " + artist + " - " + song)