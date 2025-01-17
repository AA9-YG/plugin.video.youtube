# -*- coding: utf-8 -*-
"""

    Copyright (C) 2014-2016 bromix (plugin.video.youtube)
    Copyright (C) 2016-2018 plugin.video.youtube

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only for more information.
"""

import xbmcgui
import requests

from ... import kodion
from ...kodion.utils import datetime_parser
from ...kodion.items import DirectoryItem, UriItem
from ...youtube.helper import v3, tv, extract_urls, UrlResolver, UrlToItemConverter
from . import utils


def _process_related_videos(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
    result = []

    page_token = context.get_param('page_token', '')
    video_id = context.get_param('video_id', '')
    if video_id:
        json_data = provider.get_client(context).get_related_videos(video_id=video_id, page_token=page_token)
        if not v3.handle_error(provider, context, json_data):
            return False
        result.extend(v3.response_to_items(provider, context, json_data, process_next_page=False))

    return result


def _process_parent_comments(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.FILES)
    result = []

    page_token = context.get_param('page_token', '')
    video_id = context.get_param('video_id', '')
    if video_id:
        json_data = provider.get_client(context).get_parent_comments(video_id=video_id, page_token=page_token)
        if not v3.handle_error(provider, context, json_data):
            return False
        result.extend(v3.response_to_items(provider, context, json_data))

    return result


def _process_child_comments(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.FILES)
    result = []

    page_token = context.get_param('page_token', '')
    parent_id = context.get_param('parent_id', '')
    if parent_id:
        json_data = provider.get_client(context).get_child_comments(parent_id=parent_id, page_token=page_token)
        if not v3.handle_error(provider, context, json_data):
            return False
        result.extend(v3.response_to_items(provider, context, json_data))

    return result


def _process_recommendations(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
    result = []

    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_activities('home', page_token=page_token)
    if not v3.handle_error(provider, context, json_data):
        return False
    result.extend(v3.response_to_items(provider, context, json_data))
    return result


def _process_popular_right_now(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
    result = []

    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_popular_videos(page_token=page_token)
    if not v3.handle_error(provider, context, json_data):
        return False
    result.extend(v3.response_to_items(provider, context, json_data))

    return result


def _process_browse_channels(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.FILES)
    result = []

    # page_token = context.get_param('page_token', '')
    guide_id = context.get_param('guide_id', '')
    client = provider.get_client(context)

    if guide_id:
        json_data = client.get_guide_category(guide_id)
        if not v3.handle_error(provider, context, json_data):
            return False
        result.extend(v3.response_to_items(provider, context, json_data))
    else:
        json_data = context.get_function_cache().get(kodion.utils.FunctionCache.ONE_MONTH, client.get_guide_categories)
        if not v3.handle_error(provider, context, json_data):
            return False
        result.extend(v3.response_to_items(provider, context, json_data))

    return result


def _process_disliked_videos(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
    result = []

    page_token = context.get_param('page_token', '')
    json_data = provider.get_client(context).get_disliked_videos(page_token=page_token)
    if not v3.handle_error(provider, context, json_data):
        return False
    result.extend(v3.response_to_items(provider, context, json_data))
    return result


def _process_live_events(provider, context, event_type='live'):
    def _sort(x):
        return x.get_aired()

    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
    result = []

    # TODO: cache result
    page_token = context.get_param('page_token', '')
    location = str(context.get_param('location', False)).lower() == 'true'

    json_data = provider.get_client(context).get_live_events(event_type=event_type, page_token=page_token, location=location)
    if not v3.handle_error(provider, context, json_data):
        return False
    result.extend(v3.response_to_items(provider, context, json_data, sort=_sort, reverse_sort=True))

    return result


def _process_video_stats(provider, context):
    dialog = xbmcgui.Dialog()
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
    dur = yt_item.get('contentDetails', {}).get('duration', '')
    dur_parse = kodion.utils.datetime_parser.parse(dur)
    
    if datetime.hour < 10:
        hour = '0%s' % datetime.hour
    else:
        hour = datetime.hour
     
    if datetime.minute < 10:
        minute = '0%s' % datetime.minute
    else:
        minute = datetime.minute
        
    dt_string = '%s/%s/%s @ %s:%s' % (datetime.month, datetime.day, datetime.year, hour, minute)

    stats = response.json()
    channel_stats = response2.json()
    
    view_count = "{:,}".format(stats['viewCount'])
    like_count = "{:,}".format(stats['likes'])
    dislike_count = "{:,}".format(stats['dislikes'])
    context.log_debug('Channel Stats: %s' % channel_stats)
    c_stats = channel_stats['items'][0]['statistics']['subscriberCount']
    context.log_debug('Sub Count: %s' % c_stats)
    
    try:
        c_stats2 = int(c_stats)
        context.log_debug('Sub count after int conversion: %s' % c_stats)
    except (TypeError, ValueError):
        sub_count = 'No Subscribers or Hidden'
        context.log_debug('This sub count is in the exception block')
    else:
        if c_stats2 > 0:
            sub_count = "{:,}".format(c_stats2)
            context.log_debug('Sub count is greater than zero')
        else:
            sub_count = 'No Subscribers or Hidden'
            context.log_debug('Sub count is not greater than zero')
        
            
    vid_title = '[B]Video Title: %s[/B]\n' % snippet['title']
    ch_title = '[B]Channel: %s[/B]\n' % snippet.get('channelTitle', '')
    subscribers = '[B]Subscribers: %s[/B]\n' % sub_count
    views = '[B]Views: [COLOR cyan]%s[/COLOR][/B]\n' % view_count 
    likes = '[B]Likes: [COLOR lime]%s[/COLOR][/B]\n' % like_count
    dislikes = '[B]Dislikes: [COLOR red]%s[/COLOR][/B]\n' % dislike_count
    date = '[B]Published Date: %s[/B]\n' % dt_string
    duration = '[B]Duration: %s[/B]\n' % dur_parse
    vid_id = '[B]Video ID: %s\n[/B]' % video_id
    ch_id = '[B]Channel ID: %s\n[/B]' % channel_id
    description = '[B]\nDescription:[/B] %s' % kodion.utils.strip_html_from_text(snippet['description'])
    
    vid_info = vid_title + ch_title + subscribers + views + likes + dislikes + date + duration + vid_id + ch_id + description
    result = dialog.textviewer('Video Information', vid_info)
    
    return result


def _process_description_links(provider, context):
    incognito = str(context.get_param('incognito', False)).lower() == 'true'
    addon_id = context.get_param('addon_id', '')

    def _extract_urls(_video_id):
        provider.set_content_type(context, kodion.constants.content_type.VIDEOS)
        url_resolver = UrlResolver(context)

        result = []

        progress_dialog = \
            context.get_ui().create_progress_dialog(heading=context.localize(kodion.constants.localize.COMMON_PLEASE_WAIT),
                                                    background=False)

        resource_manager = provider.get_resource_manager(context)

        video_data = resource_manager.get_videos([_video_id])
        yt_item = video_data[_video_id]
        snippet = yt_item['snippet']  # crash if not conform
        description = kodion.utils.strip_html_from_text(snippet['description'])

        urls = context.get_function_cache().get(kodion.utils.FunctionCache.ONE_WEEK, extract_urls, description)

        progress_dialog.set_total(len(urls))

        res_urls = []
        for url in urls:
            context.log_debug('Resolving url "%s"' % url)
            progress_dialog.update(steps=1, text=url)
            resolved_url = url_resolver.resolve(url)
            context.log_debug('Resolved url "%s"' % resolved_url)
            res_urls.append(resolved_url)

            if progress_dialog.is_aborted():
                context.log_debug('Resolving urls aborted')
                progress_dialog.close()
                break

            context.sleep(50)

        url_to_item_converter = UrlToItemConverter()
        url_to_item_converter.add_urls(res_urls, provider, context)

        result.extend(url_to_item_converter.get_items(provider, context))

        progress_dialog.close()

        if len(result) == 0:
            progress_dialog.close()
            context.get_ui().on_ok(title=context.localize(provider.LOCAL_MAP['youtube.video.description.links']),
                                   text=context.localize(
                                       provider.LOCAL_MAP['youtube.video.description.links.not_found']))
            return False

        return result

    def _display_channels(_channel_ids):
        _channel_id_dict = {}

        item_params = {}
        if incognito:
            item_params.update({'incognito': incognito})
        if addon_id:
            item_params.update({'addon_id': addon_id})

        for channel_id in _channel_ids:
            item_uri = context.create_uri(['channel', channel_id], item_params)
            channel_item = DirectoryItem('', item_uri)
            channel_item.set_fanart(provider.get_fanart(context))
            _channel_id_dict[channel_id] = channel_item

        _channel_item_dict = {}
        utils.update_channel_infos(provider, context, _channel_id_dict, channel_items_dict=_channel_item_dict)

        # clean up - remove empty entries
        _result = []
        for key in _channel_id_dict:
            _channel_item = _channel_id_dict[key]
            if _channel_item.get_name():
                _result.append(_channel_item)
        return _result

    def _display_playlists(_playlist_ids):
        _playlist_id_dict = {}

        item_params = {}
        if incognito:
            item_params.update({'incognito': incognito})
        if addon_id:
            item_params.update({'addon_id': addon_id})

        for playlist_id in _playlist_ids:
            item_uri = context.create_uri(['playlist', playlist_id], item_params)
            playlist_item = DirectoryItem('', item_uri)
            playlist_item.set_fanart(provider.get_fanart(context))
            _playlist_id_dict[playlist_id] = playlist_item

        _channel_item_dict = {}
        utils.update_playlist_infos(provider, context, _playlist_id_dict, _channel_item_dict)
        utils.update_fanarts(provider, context, _channel_item_dict)

        # clean up - remove empty entries
        _result = []
        for key in _playlist_id_dict:
            _playlist_item = _playlist_id_dict[key]
            if _playlist_item.get_name():
                _result.append(_playlist_item)

        return _result

    video_id = context.get_param('video_id', '')
    if video_id:
        return _extract_urls(video_id)

    channel_ids = context.get_param('channel_ids', '')
    if channel_ids:
        channel_ids = channel_ids.split(',')
        if len(channel_ids) > 0:
            return _display_channels(channel_ids)

    playlist_ids = context.get_param('playlist_ids', '')
    if playlist_ids:
        playlist_ids = playlist_ids.split(',')
        if len(playlist_ids) > 0:
            return _display_playlists(playlist_ids)

    context.log_error('Missing video_id or playlist_ids for description links')

    return False


def _process_new_uploaded_videos_tv(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)

    result = []
    next_page_token = context.get_param('next_page_token', '')
    offset = int(context.get_param('offset', 0))
    json_data = provider.get_client(context).get_my_subscriptions(page_token=next_page_token, offset=offset)
    result.extend(tv.my_subscriptions_to_items(provider, context, json_data))

    return result


def _process_new_uploaded_videos_tv_filtered(provider, context):
    provider.set_content_type(context, kodion.constants.content_type.VIDEOS)

    result = []
    next_page_token = context.get_param('next_page_token', '')
    offset = int(context.get_param('offset', 0))
    json_data = provider.get_client(context).get_my_subscriptions(page_token=next_page_token, offset=offset)
    result.extend(tv.my_subscriptions_to_items(provider, context, json_data, do_filter=True))

    return result


def process(category, provider, context):
    _ = provider.get_client(context)  # required for provider.is_logged_in()
    if not provider.is_logged_in() and category in ['new_uploaded_videos_tv', 'new_uploaded_videos_tv_filtered', 'disliked_videos']:
        return UriItem(context.create_uri(['sign', 'in']))

    if category == 'related_videos':
        return _process_related_videos(provider, context)
    elif category == 'popular_right_now':
        return _process_popular_right_now(provider, context)
    elif category == 'recommendations':
        return _process_recommendations(provider, context)
    elif category == 'browse_channels':
        return _process_browse_channels(provider, context)
    elif category == 'new_uploaded_videos_tv':
        return _process_new_uploaded_videos_tv(provider, context)
    elif category == 'new_uploaded_videos_tv_filtered':
        return _process_new_uploaded_videos_tv_filtered(provider, context)
    elif category == 'disliked_videos':
        return _process_disliked_videos(provider, context)
    elif category == 'live':
        return _process_live_events(provider, context)
    elif category == 'upcoming_live':
        return _process_live_events(provider, context, event_type='upcoming')
    elif category == 'completed_live':
        return _process_live_events(provider, context, event_type='completed')
    elif category == 'description_links':
        return _process_description_links(provider, context)
    elif category == 'parent_comments':
        return _process_parent_comments(provider, context)
    elif category == 'child_comments':
        return _process_child_comments(provider, context)
    elif category == 'descriptions':
        return _process_video_stats(provider, context)
    else:
        raise kodion.KodionException("YouTube special category '%s' not found" % category)
