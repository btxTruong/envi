#! /usr/bin/python3

import argparse
import random
import re
import appdirs
import requests
from bs4 import BeautifulSoup
from cachelib import FileSystemCache

URL = 'http://tratu.soha.vn/dict/en_vn/{}'

CACHE_DIR = appdirs.user_cache_dir('envi')
CACHE_MAX_SIZE = 1024

cache = FileSystemCache(CACHE_DIR, CACHE_MAX_SIZE, default_timeout=0)


def _random_user_agent():
    user_agents = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) "
        "Gecko/20100101 Firefox/64.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/12.0.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) "
        "Gecko/20100101 Firefox/65.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) "
        "Gecko/20100101 Firefox/64.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/12.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:64.0) "
        "Gecko/20100101 Firefox/64.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:65.0) "
        "Gecko/20100101 Firefox/65.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
    )
    return random.choice(user_agents)


def _get_result(word):
    headers = {
        'User-Agent': _random_user_agent()
    }

    with requests.Session() as envi_session:
        return envi_session.get(URL.format(word), headers=headers).text


def _get_all_meaning(html):
    tree = BeautifulSoup(html, 'html.parser')
    return [str(mean) for mean in tree.select('div#show-alter.section-h2 > div#content-3.section-h3')]


def _necessary_classifier(all_meaning):
    unnecessary_classifier = re.compile(r'Cấu trúc từ|Hình Thái Từ', re.IGNORECASE)

    return [mean for mean in all_meaning if not unnecessary_classifier.search(mean)]


def _get_classifier(html):
    """get word class e.g Noun, Adj, Verb"""
    result = {}

    classifier = re.compile(r'<h3>\s*<span class="mw-headline">(.*?)</span></h3>')
    classifier = classifier.search(html).group(1)

    mean_in_classifier = re.compile(r'<h5>\s*<span class="mw-headline">(.*?)</span></h5>')
    means = []
    for mean in mean_in_classifier.findall(html):
        means.append(mean)

    result[classifier] = means

    return result


def _pretty_output(meaning):
    space = ' '
    fmt_classifier = '\n{}+ {}'
    fmt_meaning = '{}- {}'
    for classifier, means in meaning.items():
        print(fmt_classifier.format(space * 5, classifier))
        for mean in means:
            print(fmt_meaning.format(space * 8, mean))


def envi(word):
    word = str(word)
    mean = cache.get(word)
    if mean:
        _pretty_output(mean)
    else:
        meaning_of_word = {
            word: {}
        }

        html = _get_result(word)
        all_meaning = _get_all_meaning(html)
        if not all_meaning:
            print("Can't find meaning of the {}".format(word))
            return

        necessary_classifier = _necessary_classifier(all_meaning)

        for mean in necessary_classifier:
            meaning_of_word[word].update(_get_classifier(mean))

        cache.set(word, meaning_of_word[word])

        _pretty_output(meaning_of_word[word])


def _clear_cache():
    global cache
    if not cache:
        cache = FileSystemCache(CACHE_DIR, CACHE_MAX_SIZE, 0)

    return cache.clear()


def command_line():
    parser = argparse.ArgumentParser(description='Translate en-vi via cli')
    parser.add_argument('word', help='Word to be needed translate', nargs='?')
    parser.add_argument('-C', '--clear_cache', help='Clear cache', action='store_true')

    args = vars(parser.parse_args())

    if args['clear_cache']:
        if _clear_cache():
            print('Cache clear successfully')
        else:
            print('Clear cache failed')
        return

    envi(args['word'])


if __name__ == '__main__':
    command_line()
