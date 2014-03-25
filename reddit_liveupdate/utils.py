import datetime
import itertools

import pytz

from babel.dates import format_time, format_datetime
from pylons import c, g
from r2.lib import websockets
from r2.lib.media import Scraper
from r2.lib.utils import extract_urls_from_markdown, domain


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


def pretty_time(dt):
    display_tz = pytz.timezone(c.liveupdate_event.timezone)
    today = datetime.datetime.now(display_tz).date()
    date = dt.astimezone(display_tz).date()

    if date == today:
        return format_time(
            time=dt,
            tzinfo=display_tz,
            format="HH:mm z",
            locale=c.locale,
        )
    elif today - date < datetime.timedelta(days=365):
        return format_datetime(
            datetime=dt,
            tzinfo=display_tz,
            format="dd MMM HH:mm z",
            locale=c.locale,
        )
    else:
        return format_datetime(
            datetime=dt,
            tzinfo=display_tz,
            format="dd MMM YYYY HH:mm z",
            locale=c.locale,
        )


def send_event_broadcast(event_id, type, payload):
    """ Send a liveupdate broadcast for a specific event. """
    websockets.send_broadcast(namespace="/live/" + event_id,
                              type=type,
                              payload=payload)


def embeddable_urls(md):
    """ Given some markdown, return a list of all URLs that are from
        liveupdate-embeddable domains.
    """
    return [u for u in extract_urls_from_markdown(md)
            if domain(u) in g.liveupdate_embeddable_domains]


def generate_media_objects(urls, maxwidth=485, max_embeds=15):
    """ Given a list of embed URLs, scrape and return their media objects. """
    media_objects = []
    for url in urls:
        scraper = Scraper.for_url(url)
        scraper.maxwidth = maxwidth

        # TODO: Is there a situation in which we would need the secure media
        # object? Are twitter/youtube/imgur appropriately protocol agnostic?
        thumbnail, media_object, secure_media_object = scraper.scrape()
        if media_object and 'oembed' in media_object:
            # Use our exact passed URL to ensure matching in markdown.
            # Some scrapers will canonicalize a URL to something we
            # haven't seen yet.
            media_object['oembed']['url'] = url
            media_objects.append(media_object)

        if len(media_objects) > max_embeds:
            break

    return media_objects
