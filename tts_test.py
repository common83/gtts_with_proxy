# -*- coding: utf-8 -*-
#! /usr/bin/python
import re, requests
from gtts_token.gtts_token import Token
import sys
import argparse
import os
import string

reload(sys)  
sys.setdefaultencoding("utf-8")  

proxies = {
	'http': 'http://web-proxyhk.oa.com:8080',
	'https': 'http://web-proxyhk.oa.com:8080',
}

class gTTS:
    """ gTTS (Google Text to Speech): an interface to Google's Text to Speech API """

    GOOGLE_TTS_URL = 'https://translate.google.com/translate_tts'
    MAX_CHARS = 100 # Max characters the Google TTS API takes at a time

    LANGUAGES = {
        'af' : 'Afrikaans',
        'sq' : 'Albanian',
        'ar' : 'Arabic',
        'hy' : 'Armenian',
        'bn' : 'Bengali',
        'ca' : 'Catalan',
        'zh' : 'Chinese',
        'zh-cn' : 'Chinese (Mandarin/China)',
        'zh-tw' : 'Chinese (Mandarin/Taiwan)',
        'zh-yue' : 'Chinese (Cantonese)',
        'hr' : 'Croatian',
        'cs' : 'Czech',
        'da' : 'Danish',
        'nl' : 'Dutch',
        'en' : 'English',
        'en-au' : 'English (Australia)',
        'en-uk' : 'English (United Kingdom)',
        'en-us' : 'English (United States)',
        'eo' : 'Esperanto',
        'fi' : 'Finnish',
        'fr' : 'French',
        'de' : 'German',
        'el' : 'Greek',
        'hi' : 'Hindi',
        'hu' : 'Hungarian',
        'is' : 'Icelandic',
        'id' : 'Indonesian',
        'it' : 'Italian',
        'ja' : 'Japanese',
        'ko' : 'Korean',
        'la' : 'Latin',
        'lv' : 'Latvian',
        'mk' : 'Macedonian',
        'no' : 'Norwegian',
        'pl' : 'Polish',
        'pt' : 'Portuguese',
        'pt-br' : 'Portuguese (Brazil)',
        'ro' : 'Romanian',
        'ru' : 'Russian',
        'sr' : 'Serbian',
        'sk' : 'Slovak',
        'es' : 'Spanish',
        'es-es' : 'Spanish (Spain)',
        'es-us' : 'Spanish (United States)',
        'sw' : 'Swahili',
        'sv' : 'Swedish',
        'ta' : 'Tamil',
        'th' : 'Thai',
        'tr' : 'Turkish',
        'vi' : 'Vietnamese',
        'cy' : 'Welsh'
    }

    def __init__(self, text, lang = 'en', debug = False, ttsspeed = 1):
        self.debug = debug

        if lang.lower() not in self.LANGUAGES:
            raise Exception('Language not supported: %s' % lang)
        else:
            self.lang = lang.lower()

        if not text:
            raise Exception('No text to speak')
        else:
            self.text = text

        # Split text in parts
        if len(text) <= self.MAX_CHARS: 
            text_parts = [text]
        else:
            text_parts = self._tokenize(text, self.MAX_CHARS)           

        # Clean
        def strip(x): return x.replace('\n', '').strip()
        text_parts = [strip(x) for x in text_parts]
        text_parts = [x for x in text_parts if len(x) > 0]
        self.text_parts = text_parts
        
        # Google Translate token
        self.token = Token()
        #tts speed
        self.ttsspeed = ttsspeed
		
    def save(self, savefile):
		""" Do the Web request and save to `savefile` """
		with open((savefile+'.mp3').decode('utf-8'), 'wb') as f:
			self.write_to_fp(f)
			f.close()


    def write_to_fp(self, fp):
        """ Do the Web request and save to a file-like object """
        for idx, part in enumerate(self.text_parts):
            payload = { 'ie' : 'UTF-8',
                        'q' : part,
                        'tl' : self.lang,
                        'total' : len(self.text_parts),
                        'idx' : idx,
                        'client' : 'tw-ob',
                        'textlen' : len(part),
                        'tk' : self.token.calculate_token(part),
						'ttsspeed' : self.ttsspeed}
            headers = {
                "Referer" : "http://translate.google.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"
            }
            if self.debug: print(payload)
            try:
                r = requests.get(self.GOOGLE_TTS_URL, params=payload,proxies=proxies,headers=headers)
                if self.debug:
                    print("Headers: {}".format(r.request.headers))
                    print("Reponse: {}, Redirects: {}".format(r.status_code, r.history))
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=1024):
                    fp.write(chunk)
            except Exception as e:
                raise

    def _tokenize(self, text, max_size):
        """ Tokenizer on basic roman punctuation """ 
        
        punc = "¡!()[]¿?.,;:—«»\n"
        punc_list = [re.escape(c) for c in punc]
        pattern = '|'.join(punc_list)
        parts = re.split(pattern, text)

        min_parts = []
        for p in parts:
            min_parts += self._minimize(p, " ", max_size)
        return min_parts

    def _minimize(self, thestring, delim, max_size):
        """ Recursive function that splits `thestring` in chunks
        of maximum `max_size` chars delimited by `delim`. Returns list. """ 
        
        if len(thestring) > max_size:
            idx = thestring.rfind(delim, 0, max_size)
            return [thestring[:idx]] + self._minimize(thestring[idx:], delim, max_size)
        else:
            return [thestring]

def languages():
    """Sorted pretty printed string of supported languages"""
    return ", ".join(sorted("{}: '{}'".format(gTTS.LANGUAGES[k], k) for k in gTTS.LANGUAGES))

# Args
desc = "Creates an mp3 file from spoken text via the Google Text-to-Speech API ({v})".format(v='1.1.5')
parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawTextHelpFormatter)

text_group = parser.add_mutually_exclusive_group(required=True)
text_group.add_argument('text', nargs='?', help="text to speak")      
text_group.add_argument('-f', '--file', help="file to speak")

parser.add_argument("-o", '--destination', help="destination mp3 file", action='store')
parser.add_argument('-l', '--lang', default='zh-cn', help="ISO 639-1/IETF language tag to speak in:\n" + languages())
parser.add_argument('--debug', default=False, action="store_true")
parser.add_argument('--ttsspeed', default=1 ,required=False, help='specify the speed of tts voice,value scope: 0 ~1 ,default value is 1.')

args = parser.parse_args()
print args


line_text = []
try:
    if args.text:
        text = args.text
    else:
        with open(args.file, "r") as f:
            line_text = f.readlines()

    for sentences in line_text:
		# TTSTF (Text to Speech to File)
		sentences=sentences.strip('\n')
		sentences = sentences.decode('utf-8','replace')
		tts = gTTS(text=sentences, lang=args.lang, debug=args.debug, ttsspeed=args.ttsspeed)
		tts.save(sentences)

#    if args.destination:
#        tts.save(args.destination)
#    else:
#        tts.write_to_fp(os.fdopen(sys.stdout.fileno(), "wb"))

except Exception as e:
    if args.destination:
        print(str(e))
    else:
        print("ERROR: ", e)
        
