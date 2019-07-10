#!/usr/bin/python3
import os
import zipfile
import requests
from tqdm import tqdm
from spotipy import Spotify, oauth2
from collections import OrderedDict
from deezloader.utils import decryptfile, genurl, calcbfkey, write_tags, var_excape
localdir = os.getcwd()
qualities = {"FLAC":{
                     "quality": "9",
                     "extension": ".flac",
                     "qualit": "FLAC"
                    },
             "MP3_320": {
                         "quality": "3",
                         "extension": ".mp3",
                         "qualit": "320"
             },
             "MP3_256": {
                         "quality": "5",
                         "extension": ".mp3",
                         "qualit": "256"
             },
             "MP3_128": {
                         "quality": "1",
                         "extension": ".mp3",
                         "qualit": "128"
             }
            }
header = {"Accept-Language": "en-US,en;q=0.5"}
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
def generate_token():
    return oauth2.SpotifyClientCredentials(client_id="c6b23f1e91f84b6a9361de16aba0ae17", client_secret="237e355acaa24636abc79f1a089e6204").get_access_token()
def request(url, control=False):
    try:
       thing = requests.get(url, headers=header)
    except:
       thing = requests.get(url, headers=header)
    if control:
     try:
        if thing.json()['error']['message'] == "no data":
         raise TrackNotFound("Track not found :(")
     except KeyError:
        pass
     try:
        if thing.json()['error']['message'] == "Quota limit exceeded":
         raise QuotaExceeded("Too much requests limit yourself")
     except KeyError:
        pass
     try:
        if thing.json()['error']:
         raise InvalidLink("Invalid link ;)")
     except KeyError:
        pass
    return thing
class Login:
      def __init__(self, mail, password, token=None):
          self.spo = Spotify(auth=generate_token())
          self.req = requests.Session()
          check = self.get_api("deezer.getUserData")['checkFormLogin']
          post_data = {
                       "type": "login",
                       "mail": mail,
                       "password": password,
                       "checkFormLogin": check
          }
          end = self.req.post("https://www.deezer.com/ajax/action.php", post_data).text
          if "success" == end:
           print("Success, you are in :)")
          else:
              if not token:
               raise BadCredentials(end + ", and no token provided")
              self.req.cookies["arl"] = token
              if self.req.get("https://www.deezer.com/").text.split("'deezer_user_id': ")[1].split(",")[0] == "0":
               raise BadCredentials("Wrong token :(")
      def get_api(self, method=None, api_token="null", json=None):
          params = {
                    "api_version": "1.0",
                    "api_token": api_token,
                    "input": "3",
                    "method": method
          }
          try:
             return self.req.post("http://www.deezer.com/ajax/gw-light.php", params=params, json=json).json()['results']
          except:
             return self.req.post("http://www.deezer.com/ajax/gw-light.php", params=params, json=json).json()['results']
      def download(self, link, name, quality, recursive_quality, recursive_download, datas, create_zip=False):
          if not quality in qualities:
           raise QualityNotFound("The qualities have to be FLAC or MP3_320 or MP3_256 or MP3_128")
          def login(method, json):
              infos = ""
              while not "MD5_ORIGIN" in str(infos):
                  self.token = self.get_api("deezer.getUserData")['checkForm']
                  infos = self.get_api(method, self.token, json)
              return infos
          def ultimatum(infos, name, datas, quality, recursive_download, recursive_quality):
              extension = ".mp3"
              ids = infos['SNG_ID']
              if int(infos['FILESIZE_' + quality]) > 0 and quality == "FLAC":
               quality = "9"
               extension = ".flac"
               qualit = "FLAC"
              elif int(infos['FILESIZE_' + quality]) > 0 and quality == "MP3_320":
               quality = "3"
               qualit = "320"
              elif int(infos['FILESIZE_' + quality]) > 0 and quality == "MP3_256":
               quality = "5"
               qualit = "256"
              elif int(infos['FILESIZE_' + quality]) > 0 and quality == "MP3_128":
               quality = "1"
               qualit = "128"
              else:
                  if recursive_quality:
                   raise QualityNotFound("The quality chosen can't be downloaded")
                  for a in qualities:
                      if int(infos['FILESIZE_' + a]) > 0:
                       quality = qualities[a]['quality']
                       extension = qualities[a]['extension']
                       qualit = qualities[a]['qualit']
                       break
                      else:
                          if a == "MP3_128":
                           raise TrackNotFound("There isn't any quality avalaible for download this song")
              name += " (" + qualit + ")" + extension
              if os.path.isfile(name):
               if not recursive_download:
                return name 
               ans = input("Track " + name + " already exists, do you want to redownload it?(y or n):")
               if ans != "y":
                return name
              try:
                 md5 = infos['FALLBACK']['MD5_ORIGIN']
              except KeyError:
                 md5 = infos['MD5_ORIGIN']
              hashs = genurl(md5, quality, ids, infos['MEDIA_VERSION'])
              try:
                 crypt = request("https://e-cdns-proxy-%s.dzcdn.net/mobile/1/%s" % (md5[0], hashs))
              except IndexError:
                 raise TrackNotFound("Track not found :(")
              if len(crypt.content) == 0:
               raise TrackNotFound("Error with this track :(")
              open(name, "wb").write(crypt.content)
              decry = open(name, "wb")
              decryptfile(crypt.iter_content(2048), calcbfkey(ids), decry)
              datas = add_more_tags(datas, infos, ids)
              write_tags(name, datas)
              return name
          def add_more_tags(datas, infos, ids):
              try:
                 datas['author'] = " & ".join(infos['SNG_CONTRIBUTORS']['author'])
              except:
                 datas['author'] = ""
              try:   
                 datas['composer'] = " & ".join(infos['SNG_CONTRIBUTORS']['composer'])
              except:
                 datas['composer'] = ""
              try:
                 datas['lyricist'] = " & ".join(infos['SNG_CONTRIBUTORS']['lyricist'])
              except:
                 datas['lyricist'] = ""
              try:
                 datas['version'] = infos['VERSION']
              except KeyError:
                 datas['version'] = ""
              need = self.get_api("song.getLyrics", self.token, {"sng_id": ids})
              try:
                 datas['lyric'] = need['LYRICS_TEXT']
                 datas['copyright'] = need['LYRICS_COPYRIGHTS']
                 datas['lyricist'] = need['LYRICS_WRITERS']
              except KeyError:
                 datas['lyric'] = ""
                 datas['copyright'] = ""
                 datas['lyricist'] = ""
              return datas
          ids = link.split("/")[-1]
          zip_name = ""
          quali = ""
          if "track" in link:
           method = "song.getData"
           json = {"sng_id": ids}
           infos = login(method, json)
           image = request("https://e-cdns-images.dzcdn.net/images/cover/" + infos['ALB_PICTURE'] + "/1200x1200-000000-80-0-0.jpg").content
           if len(image) == 13:
            image = request("https://e-cdns-images.dzcdn.net/images/cover/1200x1200-000000-80-0-0.jpg").content
           datas['image'] = image
           song = datas['music'] + " - " + datas['artist']
           print("\nDownloading:" + song)
           try:
              nams = ultimatum(infos, name, datas, quality, recursive_download, recursive_quality)
           except TrackNotFound:
              url = request("https://api.deezer.com/search/track/?q=" + datas['music'].replace("#", "") + " + " + datas['artist'].replace("#", ""), True).json()
              try:
                 for b in range(url['total'] + 1):
                     if url['data'][b]['title'] == datas['music'] or datas['music'] in url['data'][b]['title_short']:
                      URL = url['data'][b]['link']
                      break
              except IndexError:
                 raise TrackNotFound("Track not found: " + song)
              json = {"sng_id": URL.split("/")[-1]}
              infos = login(method, json)
              nams = ultimatum(infos, name, datas, quality, recursive_download, recursive_quality)
          else:
              nams = []
              detas = {}
              method = "song.getListByAlbum"
              json = {
                      "alb_id": ids,
                      "nb": -1
                     }
              infos = login(method, json)['data']
              image = request("https://e-cdns-images.dzcdn.net/images/cover/" + infos[0]['ALB_PICTURE'] + "/1200x1200-000000-80-0-0.jpg").content
              if len(image) == 13:
               image = request("https://e-cdns-images.dzcdn.net/images/cover/1200x1200-000000-80-0-0.jpg").content
              detas['image'] = image
              detas['album'] = datas['album']
              detas['year'] = datas['year']
              detas['genre'] = datas['genre']
              detas['ar_album'] = datas['ar_album']
              detas['label'] = datas['label']
              for a in tqdm(range(len(name))):
                  detas['music'] = datas['music'][a]
                  detas['artist'] = datas['artist'][a]
                  detas['tracknum'] = datas['tracknum'][a]
                  detas['discnum'] = datas['discnum'][a]
                  detas['bpm'] = datas['bpm'][a]
                  detas['gain'] = datas['gain'][a]
                  detas['duration'] = datas['duration'][a]
                  detas['isrc'] = datas['isrc'][a]
                  try:
                     nams.append(ultimatum(infos[a], name[a], detas, quality, recursive_download, recursive_quality))
                  except TrackNotFound:
                     url = request("https://api.deezer.com/search/track/?q=" + detas['music'].replace("#", "") + " + " + detas['artist'].replace("#", ""), True).json()
                     try:
                        for b in range(url['total'] + 1):
                            if url['data'][b]['title'] == detas['music'] or detas['music'] in url['data'][b]['title_short']:
                             URL = url['data'][b]['link']
                             break
                     except IndexError:
                        nams.append(name[a])
                        print("\nTrack not found: " + detas['music'] + " - " + detas['artist'])
                        continue
                     try:
                        method = "song.getData"
                        json = {"sng_id": URL.split("/")[-1]}
                        nams.append(ultimatum(login(method, json), name[a], detas, quality, recursive_download, recursive_quality))
                     except TrackNotFound:
                        nams.append(name[a])
                        print("\nTrack not found: " + detas['music'] + " - " + detas['artist'])
                        continue
                  quali = nams[a].split("(")[-1].split(")")[0]
              if create_zip:
               dir = "/".join(name[a].split("/")[:-1]) + "/"
               if len(nams) > 0:
                zip_name = dir + dir.split("/")[-2] + " (" + quali + ").zip"
                z = zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED)
                for a in nams:
                    b = a.split("/")[-1]
                    try:
                       z.write(a, b)
                    except FileNotFoundError:
                       pass
                z.close()
          return nams, zip_name
      def download_trackdee(self, URL, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True):
          datas = {}
          if "?utm" in URL:
           URL, a = URL.split("?utm")
          URL1 = "https://www.deezer.com/track/" + URL.split("/")[-1]
          URL2 = "https://api.deezer.com/track/" + URL.split("/")[-1]
          url = request(URL2, True).json()
          url1 = request("http://api.deezer.com/album/" + str(url['album']['id']), True).json()
          datas['music'] = url['title']
          array = []
          for a in url['contributors']:
              array.append(a['name'])
          array.append(url['artist']['name'])
          if len(array) > 1:
           for a in array:
               for b in array:
                   if a in b and a != b:
                    array.remove(b)
          datas['artist'] = ", ".join(OrderedDict.fromkeys(array))
          datas['album'] = url1['title']
          datas['tracknum'] = str(url['track_position'])
          datas['discnum'] = str(url['disk_number'])
          datas['year'] = url['release_date']
          datas['genre'] = []
          try:
             for a in url1['genres']['data']:
                 datas['genre'].append(a['name'])
          except KeyError:
             pass
          datas['genre'] = " & ".join(datas['genre'])
          datas['ar_album'] = []
          for a in url1['contributors']:
              if a['role'] == "Main":
               datas['ar_album'].append(a['name'])
          datas['ar_album'] = " & ".join(datas['ar_album'])
          datas['label'] = url1['label']
          datas['bpm'] = str(url['bpm'])
          datas['gain'] = str(url['gain'])
          datas['duration'] = str(url['duration'])
          datas['isrc'] = url['isrc']
          album = var_excape(datas['album'])
          dir = output + album + " " + url1['upc'] + "/"
          try:
             os.makedirs(dir)
          except FileExistsError:
             pass
          name = dir + album + " CD " + datas['discnum'] + " TRACK " + datas['tracknum']
          name, a = self.download(URL, name, quality, recursive_quality, recursive_download, datas)
          return name
      def download_albumdee(self, URL, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True, create_zip=False):
          datas = {}
          datas['music'] = []
          datas['artist'] = []
          datas['tracknum'] = []
          datas['discnum'] = []
          datas['bpm'] = []
          datas['gain'] = []
          datas['duration'] = []
          datas['isrc'] = []
          names = []
          array = []
          if "?utm" in URL:
           URL, a = URL.split("?utm")
          URL1 = "https://www.deezer.com/album/" + URL.split("/")[-1]
          URL2 = "https://api.deezer.com/album/" + URL.split("/")[-1]
          url = request(URL2, True).json()
          datas['album'] = url['title']
          datas['label'] = url['label']
          datas['year'] = url['release_date']
          datas['genre'] = []
          try:
             for a in url['genres']['data']:
                 datas['genre'].append(a['name'])
          except KeyError:
             pass
          datas['genre'] = " & ".join(datas['genre'])
          datas['ar_album'] = []
          for a in url['contributors']:
              if a['role'] == "Main":
               datas['ar_album'].append(a['name'])
          datas['ar_album'] = " & ".join(datas['ar_album'])
          album = var_excape(datas['album'])
          dir = output + "/" + album + " " + url['upc'] + "/"
          for a in url['tracks']['data']:
              del array[:]
              datas['music'].append(a['title'])
              ur = request("https://api.deezer.com/track/" + str(a['id']), True).json()
              discnum = str(ur['disk_number'])
              tracknum = str(ur['track_position'])
              names.append(dir + album + " CD " + discnum + " TRACK " + tracknum)
              datas['tracknum'].append(tracknum)
              datas['discnum'].append(discnum)
              datas['bpm'].append(str(ur['bpm']))
              datas['gain'].append(str(ur['gain']))
              datas['duration'].append(str(ur['duration']))
              datas['isrc'].append(ur['isrc'])
              for a in ur['contributors']:
                  array.append(a['name'])
              array.append(ur['artist']['name'])
              if len(array) > 1:
               for a in array:
                   for b in array:
                       if a in b and a != b:
                        array.remove(b)
              datas['artist'].append(", ".join(OrderedDict.fromkeys(array)))
          try:
             os.makedirs(dir)
          except FileExistsError:
             pass
          names, zip_name = self.download(URL, names, quality, recursive_quality, recursive_download, datas, create_zip)
          if create_zip:
           return names, zip_name
          return names
      def download_playlistdee(self, URL, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True):
          array = []
          if "?utm" in URL:
           URL, a = URL.split("?utm")
          url = request("https://api.deezer.com/playlist/" + URL.split("/")[-1], True).json()
          for a in url['tracks']['data']:
              try:
                 array.append(self.download_trackdee(a['link'], output, quality, recursive_quality, recursive_download))
              except TrackNotFound:
                 print("\nTrack not found " + a['title'])
                 array.append("None")
          return array
      def download_trackspo(self, URL, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True):
          if "?" in URL:
           URL,a = URL.split("?")
          try:
             url = self.spo.track(URL)
          except Exception as a:
             if not "The access token expired" in str(a):
              raise InvalidLink("Invalid link ;)")
             self.spo = Spotify(auth=generate_token())
             url = self.spo.track(URL)
          isrc = url['external_ids']['isrc']
          url = request("https://api.deezer.com/track/isrc:" + isrc, True).json()
          name = self.download_trackdee(url['link'], output, quality, recursive_quality, recursive_download)
          return name
      def download_albumspo(self, URL, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True, create_zip=False):
          if "?" in URL:
           URL,a = URL.split("?")
          try:
             tracks = self.spo.album(URL)
          except Exception as a:
             if not "The access token expired" in str(a):
              raise InvalidLink("Invalid link ;)")
             self.spo = Spotify(auth=generate_token())
             tracks = self.spo.album(URL)
          try:
             upc = tracks['external_ids']['upc']
             while upc[0] == "0":
                 upc = upc[1:]
             url = request("https://api.deezer.com/album/upc:" + upc).json()
             names = self.download_albumdee(url['link'], output, quality, recursive_quality, recursive_download, create_zip)
          except KeyError:
             search = len(tracks['tracks']['items']) // 8
             try:
                url = self.spo.track(tracks['tracks']['items'][search]['external_urls']['spotify'])
             except:
                self.spo = Spotify(auth=generate_token())
                url = self.spo.track(tracks['tracks']['items'][search]['external_urls']['spotify'])
             isrc = url['external_ids']['isrc']
             try:
                url = request("https://api.deezer.com/track/isrc:" + isrc, True).json()
                names = self.download_albumdee(url['album']['link'], output, quality, recursive_quality, recursive_download, create_zip)
             except TrackNotFound:
                raise AlbumNotFound("Album not found :(")
          return names
      def download_playlistspo(self, URL, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True):
          array = []
          if "?" in URL:
           URL,a = URL.split("?")
          URL = URL.split("/")
          try:
             tracks = self.spo.user_playlist_tracks(URL[-3], playlist_id=URL[-1])
          except Exception as a:
             if not "The access token expired" in str(a):
              raise InvalidLink("Invalid link ;)")
             self.spo = Spotify(auth=generate_token())
             tracks = self.spo.user_playlist_tracks(URL[-3], playlist_id=URL[-1])
          for a in tracks['items']:
              try:
                 array.append(self.download_trackspo(a['track']['external_urls']['spotify'], output, quality, recursive_quality, recursive_download))
              except:
                 print("\nTrack not found :(")
                 array.append("None")
          if tracks['total'] != 100:
           for a in range(tracks['total'] // 100):
               try:
                  tracks = self.spo.next(tracks)
               except:
                  self.spo = Spotify(auth=generate_token())
                  tracks = self.spo.next(tracks)
               for a in tracks['items']:
                   try:
                      array.append(self.download_trackspo(a['track']['external_urls']['spotify'], output, quality, recursive_quality, recursive_download))
                   except:
                      print("\nTrack not found :(")
                      array.append("None")
          return array
      def download_name(self, artist, song, output=localdir + "/Songs/", quality="MP3_320", recursive_quality=True, recursive_download=True):
          try:
             search = self.spo.search(q="track:" + song + " artist:" + artist)
          except:
             self.spo = Spotify(auth=generate_token())
             search = self.spo.search(q="track:" + song + " artist:" + artist)
          try:
             return self.download_trackspo(search['tracks']['items'][0]['external_urls']['spotify'], output, quality, recursive_quality, recursive_download)
          except IndexError:
             raise TrackNotFound("Track not found: " + artist + " - " + song)