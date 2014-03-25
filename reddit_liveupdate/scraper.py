import json
import re
import requests
from pylons import g

from r2.lib.hooks import HookRegistrar
from r2.lib.media import Scraper, MediaEmbed
from r2.lib.utils import UrlParser


hooks = HookRegistrar()
_EMBED_TEMPLATE = """
<!doctype html>
<html>
<head>
<style>
iframe {{
    border: 1px solid black;
}}
</style>
</head>
<body>
<iframe src="//{domain}/live/{event_id}/embed"
        width="{width}" height="{height}">
</iframe>
</body>
</html>
"""


class _LiveUpdateScraper(Scraper):
    def __init__(self, event_id):
        self.event_id = event_id

    def _make_media_object(self):
        return {
            "type": "liveupdate",
            "event_id": self.event_id,
        }

    def scrape(self):
        return (
            None,
            self._make_media_object(),
            self._make_media_object(),
        )

    @classmethod
    def media_embed(cls, media_object):
        width = 710
        height = 500

        content = _EMBED_TEMPLATE.format(
            event_id=media_object["event_id"],
            domain=g.media_domain,
            width=width,
            height=height,
        )

        return MediaEmbed(
            height=height,
            width=width,
            content=content,
        )


class _TwitterScraper(Scraper):
    OEMBED_ENDPOINT = "https://api.twitter.com/1/statuses/oembed.json"
    URL_MATCH = re.compile(r"""https?:
                               //(www\.)?twitter\.com
                               /\w{1,20}
                               /status(es)?
                               /\d+
                            """, re.X)

    def __init__(self, url, maxwidth=600, omit_script=False):
        self.url = url
        self.maxwidth = maxwidth
        self.omit_script = False

    @classmethod
    def matches(cls, url):
        return cls.URL_MATCH.match(url)

    def _fetch_from_twitter(self):
        params = {
            "url": self.url,
            "format": "json",
            "maxwidth": self.maxwidth,
            "omit_script": self.omit_script,
        }

        content = requests.get(self.OEMBED_ENDPOINT, params=params).content
        return json.loads(content)

    def _make_media_object(self, oembed):
        if oembed.get("type") in ("video", "rich"):
            return {
                "type": "twitter.com",
                "oembed": oembed,
            }
        return None

    def scrape(self):
        oembed = self._fetch_from_twitter()
        if not oembed:
            return None, None, None

        media_object = self._make_media_object(oembed)

        return (
            None,  # no thumbnails for twitter
            media_object,
            media_object,  # Twitter's response is ssl ready by default
        )

    @classmethod
    def media_embed(cls, media_object):
        oembed = media_object["oembed"]

        html = oembed.get("html")
        width = oembed.get("width")

        # Right now Twitter returns no height, so we get ''.
        # We'll reset the height with JS dynamically, but if they support
        # height in the future, this should work transparently.
        height = oembed.get("height") or 0

        if not html and width:
            return

        return MediaEmbed(
            width=width,
            height=height,
            content=html,
        )


@hooks.on("scraper.factory")
def make_scraper(url):
    parsed = UrlParser(url)

    if parsed.is_reddit_url():
        if parsed.path.startswith("/live/"):
            try:
                event_id = parsed.path.split("/")[2]
            except IndexError:
                return
            else:
                return _LiveUpdateScraper(event_id)

    if (_TwitterScraper.matches(url)):
        return _TwitterScraper(url)


@hooks.on("scraper.media_embed")
def make_media_embed(media_object):
    media_type = media_object.get("type")

    if media_type == "liveupdate":
        return _LiveUpdateScraper.media_embed(media_object)

    if media_type == "twitter.com":
        return _TwitterScraper.media_embed(media_object)
