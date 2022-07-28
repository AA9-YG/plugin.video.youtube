import math
import requests 

from ... import kodion
from ...kodion.utils import datetime_parser
#from ...kodion.items import DirectoryItem, UriItem
#from ...youtube.helper import v3, tv, extract_urls, UrlResolver, UrlToItemConverter
from . import utils


def num_fmt(num):
    i_offset = 15 # change this if you extend the symbols!!!
    prec = 3
    fmt = '.{p}g'.format(p=prec)
    symbols = ['q', 'T', 'B', 'M', 'k', '', 'm', 'u', 'n']

    e = math.log10(abs(num))
    if e >= i_offset + 3:
        return '{:{fmt}}'.format(num, fmt=fmt)
    for i, sym in enumerate(symbols):
        e_thresh = i_offset - 3 * i
        if (num >= 995) and (num < 1000):
            return '1k'
        elif (num >= 999500) and (num < 1000000):
            return '1M'
        elif (num >= 999500000) and (num < 1000000000):
            return '1B'
        elif (num >= 999500000000) and (num < 1000000000000):
            return '1T'
        elif (num >= 999500000000000) and (num < 1000000000000000):
            return '1q' 
        if e >= e_thresh:
            return '{:{fmt}}{sym}'.format(num/10.**e_thresh, fmt=fmt, sym=sym)
    
    return '{:{fmt}}'.format(num, fmt=fmt)


def get_play_info(provider, context):
    video_id = context.get_param('video_id', '')
    channel_id = context.get_param('channel_id', '')
    channel_name = context.get_param('channel_name', '')
    key = "AIzaSyAT-LCjBFiQdRdYTO0XL312EIFx6SKm1lU"
    vid_url = 'https://returnyoutubedislikeapi.com/votes?videoId=' + str(video_id)
    vid_url2 = "https://www.googleapis.com/youtube/v3/channels?part=statistics&id=" + channel_id + "&key=" + key
    
    response = requests.get(vid_url)
    response2 = requests.get(vid_url2)
    
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
    resource_manager = provider.get_resource_manager(context)
    
    video_data = resource_manager.get_videos([video_id])
    yt_item = video_data[video_id]
    snippet = yt_item['snippet']  # crash if not conform
    
    dt = snippet['publishedAt']
    datetime = kodion.utils.datetime_parser.strptime(dt, fmt='%Y-%m-%dT%H:%M:%S.%fZ')
        
    dt_string = '%s/%s/%s' % (datetime.month, datetime.day, datetime.year)

    stats = response.json()
    channel_stats = response2.json()
    
    v_count = int(stats['viewCount'])
    view_count = num_fmt(v_count)
    l_count = int(stats['likes'])
    like_count = num_fmt(l_count)
    d_count = int(stats['dislikes'])
    dislike_count = num_fmt(d_count)
    c_stats = channel_stats['items'][0]['statistics']['subscriberCount']
    
    try:
        c_stats2 = int(c_stats)
        context.log_debug('Sub count after int conversion: %s' % c_stats)
    except (TypeError, ValueError):
        sub_count = 'None/Hidden'
    else:
        if c_stats2 > 0:
            sub_count = num_fmt(c_stats2)
        else:
            sub_count = 'None/Hidden'
        
    subscribers = '\t[B]Subscribers: %s[/B]\t' % sub_count
    views = '[B]Views: [COLOR cyan]%s[/COLOR][/B]\t' % view_count 
    likes = '[B]Likes: [COLOR lime]%s[/COLOR][/B]\t' % like_count
    dislikes = '[B]Dislikes: [COLOR red]%s[/COLOR][/B]\t' % dislike_count
    date = '[B]Date: %s[/B]\t' % dt_string
    
    vid_info = subscribers + views + likes + dislikes + date
    
    return vid_info
