# -*- coding: utf-8 -*-
"""
QQ NT 聊天记录导出工具 - WebSocket 服务器版 (CLI功能增强)

将原有的命令行工具改造为WebSocket服务器，以便通过Web界面进行控制。
此版本已整合群聊导出功能，并增加了自定义字段的JSON/CSV导出能力。
最新更新：集成了 group_info.db, 实现群名片精准显示、群成员导出等高级功能。
V6.7 (Compatibility Fix): 修复了因 text_factory 参数在旧版Python中不兼容导致的启动崩溃问题。
"""

import sqlite3
import os
import base64
from datetime import datetime
import re
import json
import argparse
import warnings
import hashlib
import html
import asyncio
import websockets
import csv
import sys
import webbrowser
import threading
from aiohttp import web
import socket
import textwrap
import shlex
import logging
import time
import subprocess

# --- 日志记录器设置 ---
logger = logging.getLogger('ARK-1')

# --- 路径适配: 检查是否在打包环境中 ---
def get_resource_path(relative_path):
    """ 获取资源的绝对路径, 兼容开发环境和 PyInstaller 打包环境 """
    if getattr(sys, 'frozen', False):
        # 如果是打包后的 exe
        base_path = sys._MEIPASS
    else:
        # 如果是正常的 .py 文件
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- WebSocket & Server Globals ---
connected_clients = set()
PROFILE_MGR = None
CONFIG_MGR = None
DB_CON, GROUP_INFO_DB_CON, PROFILE_DB_CON = None, None, None
DB_CONNECTIONS = {}
WORK_DIR = "."
LOG_TO_CONSOLE = False # 控制WebSocket日志是否在控制台打印
global_args = None
DB_FIELDS_CACHE = []
GROUP_UID_TO_UIN_MAP = {}
GROUP_UIN_TO_UID_MAP = {}

# --- 字段描述字典 ---
FIELD_DESCRIPTIONS = {
    # nt_msg.db fields
    "40001": "消息ID", "40002": "消息随机值", "40003": "消息序号(Seq)", "40005": "未知标志", "40006": "元素ID?",
    "40010": "聊天类型", "40011": "消息类型", "40012": "子消息类型(PB)", "40013": "发送类型", "40020": "发送者UID",
    "40021": "会话ID(UID)", "40027": "会话UIN", "40030": "QQ号/群号", "40033": "发送者QQ号", "40041": "发送状态",
    "40050": "消息时间戳", "40058": "当日零点时间戳", "40060": "群聊退出标志", "40062": "详细表态(PB)", "40083": "表态总数1",
    "40084": "表态总数2", "40090": "发送者群名片(缓存)", "40093": "发送者昵称(缓存)", "40094": "消息来源", "40095": "发送者备注",
    "40100": "@状态", "40600": "状态标志(PB)", "40800": "核心消息内容(PB)", "40801": "未知(PB)", "40850": "回复消息序号",
    "40900": "扩展消息(PB)", "41103": "置顶时间", "41110": "群头像路径", "41135": "群聊中带的昵称","1005":"已删除好友UID","49740":"删除时间",
    "41145":"群临时会话id","41103":"群临时会话时间","40051":"临时对话内容(PB)","41110":"文件本地存储路径","100210":"本地搜索序列号","100211":"本地搜索内容(PB)",
    # group_info.db - group_member3
    "1000": "成员UID", "1002": "成员QQ号(uin)", "20002": "成员QQ昵称", "64003": "成员群名片", "64007": "入群时间",
    "64008": "最后发言时间", "64009": "禁言解封时间", "64010": "管理员标志", "64016": "是否为群成员", "64023": "自定义头衔",
    "64035": "群成员等级","64029":"群成员私聊备注",
    # group_info.db - group_list / group_detail_info_ver1
    "60001": "群号(uin)", "60007": "群名称", "60216": "最新群公告(纯文本)", "60217": "群描述(PB)", "60026": "群备注",
    "60002": "群主UID", "60004": "建群时间", "60005": "群规模(最大人数)", "60006": "成员总数", "60218": "群标签",
    "60221": "纯数字群号(用于关联)", "60224": "入群问题", "60340": "本人退群标志","60240":"群描述(纯文本)",
    # group_info.db - group_essence
    "67501": "精华消息Seq", "67502": "精华消息Random", "67503": "精华消息发送者UIN", "67504": "精华消息发送者昵称",
    "67505": "精华设置状态", "67506": "操作者UIN", "67507": "操作者昵称", "67508": "操作时间",
    # group_info.db - group_notify_list
    "61001": "通知时间戳(毫秒)", "61002": "通知类型", "61003": "通知验证状态", "61004": "群组信息(PB)", "61005": "被操作者(PB)",
    "61006": "操作者(PB)", "61007": "操作人信息(PB)", "61008": "操作时间戳", "61010": "附加说明", "61011": "系统说明",
    "61025": "成员变动详情(XML)",

    # profile_info.db - profile_info_v6
    "1001":"QID","20009":"备注","20011":"个性签名","20004":"头像链接",

    # profile_info.db - profile_info_adelie
    "320001":"QQ智能体名称","320002":"QQ智能体头像链接","320003":"QQ智能体描述","320004":"QQ智能体开始语","320007":"@QQ智能体名称","320061":"QQ智能体类别",

    # profile_info.db - buddy_list
    "25007":"好友分组号",

    # group_info.db - group_bulletin
    "64205":"QQ群公告(PB)",

    # group_info.db - group_capsule
    "48902":"群公告图片链接(PB)",

    # group_info.db - group_ext_list
    "66732":"群聊UID","66723":"群聊聊天字符",

    # group_info.db - group_member_level_info
    "67103":"群等级头衔列表(PB)"
}

# 忽略 google.protobuf 的 pkg_resources DEPRECATED 警告
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf')

try:
    import blackboxprotobuf
except ImportError:
    print("错误：缺少 'blackboxprotobuf' 库。")
    print("请使用 'pip install blackboxprotobuf' 命令进行安装。")
    exit(1)

# --- 常量定义 ---
_DB_FILENAME = "nt_msg.decrypt.db"
_PROFILE_DB_FILENAME = "profile_info.decrypt.db"
_GROUP_INFO_DB_FILENAME = "group_info.decrypt.db"
_OUTPUT_DIR_NAME = "output_chats"
_CONFIG_FILENAME = "export_config.json"
_TEMPLATE_DIR_NAME = "html_templates"
_NON_FRIENDS_CACHE_FILENAME = "non_friends_cache.json"
_TIMELINE_FILENAME_BASE = "chat_logs_timeline"
_LIB_DIR_NAME = "lib"

DB_PATH, PROFILE_DB_PATH, GROUP_INFO_DB_PATH = "", "", ""
OUTPUT_DIR, CONFIG_PATH, TEMPLATE_DIR_PATH, NON_FRIENDS_CACHE_PATH = "", "", "", ""

SALVAGE_CACHE, MESSAGE_CONTENT_CACHE = {}, {}

# --- 数据库表与字段常量 ---
TABLE_NAME_C2C, TABLE_NAME_GROUP = "c2c_msg_table", "group_msg_table"
COL_C2C_PEER_UID, COL_GROUP_ID_UID, COL_GROUP_ID_UIN = "40021", "40021", "40030"
COL_SENDER_UID, COL_TIMESTAMP, COL_MSG_CONTENT = "40020", "40050", "40800"
CATEGORY_LIST_TABLE, BUDDY_LIST_TABLE, PROFILE_INFO_TABLE = "category_list_v2", "buddy_list", "profile_info_v6"
PROF_COL_UID, PROF_COL_QQ, PROF_COL_GROUP_ID = "1000", "1002", "25007"
PROF_COL_GROUP_LIST_PB, PROF_COL_NICKNAME, PROF_COL_REMARK = "25011", "20002", "20009"
GROUP_MEMBER_TABLE, GROUP_DETAIL_TABLE = "group_member3", "group_detail_info_ver1"
GROUP_ESSENCE_TABLE, GROUP_NOTIFY_TABLE = "group_essence", "group_notify_list"
GROUP_LIST_TABLE = "group_list"

# Protobuf and other constants...
PB_GROUP_ID = "25007"; PB_GROUP_NAME = "25008"; PB_MSG_CONTAINER = "40800"; PB_MSG_TYPE = "45002"; PB_MSG_SUBTYPE = "45003"; PB_EMOJI_DESC = "47602"; PB_STICKER_DESC = "45815"; PB_APOLLO_TEXT = "45824"; PB_TEXT_CONTENT = "45101"; PB_ARK_JSON = "47901"; PB_RECALLER_NAME = "47705"; PB_RECALLER_UID = "47703"; PB_RECALL_SUFFIX = "47713"; PB_FILE_NAME = "45402"; PB_IMG_WIDTH = "45411"; PB_IMG_HEIGHT = "45412"; PB_VID_DURATION = "45410"; PB_VID_WIDTH = "45413"; PB_VID_HEIGHT = "45414"; PB_CALL_STATUS = "48153"; PB_CALL_TYPE = "48154"; PB_MARKET_FACE_TEXT = "80900"; PB_IMAGE_IS_FLASH = "45829"; PB_REDPACKET_TYPE = "48412"; PB_REDPACKET_TITLE = "48443"; PB_VOICE_DURATION = "45005"; PB_VOICE_TO_TEXT = "45923"; PB_GIFT_TEXT = "52138"; PB_LOCATION_SHARE_TEXT = "52152"; PB_INTERACTIVE_EMOJI_ID = "47611"; PB_INTERACTIVE_EMOJI_ID_IN_QUOTE = "47601"; PB_REPLY_ORIGIN_SENDER_UID = "40020"; PB_REPLY_ORIGIN_RECEIVER_UID = "40021"; PB_REPLY_ORIGIN_TS = "47404"; PB_REPLY_ORIGIN_SUMMARY_TEXT = "47413"; PB_REPLY_ORIGIN_OBJ = "47423"; PB_GRAYTIP_INTERACTIVE_XML = "48214"
MSG_TYPE_MAP = {1:"文本",2:"图片",3:"文件",4:"语音",5:"视频",6:"QQ表情",7:"引用",8:"灰字提示",9:"红包",10:"卡片",11:"商城表情",14:"Markdown",21:"通话",27:"礼物",28:"位置共享提示"}
INTERACTIVE_EMOJI_MAP = {1:"戳一戳",2:"比心",3:"点赞",4:"心碎",5:"666",6:"放大招"}
NOTIFY_TYPE_MAP = {1:"申请加群",3:"被设为管理员",6:"被移出群聊",11:"被管理员拒绝加入",13:"自主退出群聊",15:"被取消管理员权限"}
NOTIFY_STATUS_MAP = {1:"过滤",0:"正常",2:"同意",3:"拒绝",4:"忽略"}

# --- 核心类与函数 ---

class ConfigManager:
    """负责加载、管理和保存在 `export_config.json` 中的导出配置。"""
    def __init__(self, config_path):
        self.config_path = config_path
        self.default_config = {
            'show_recall': True, 'show_recall_suffix': True, 'show_poke': True,
            'show_voice_to_text': True, 'export_non_friends': True, 'export_format': 'md',
            'html_template': 'default.html', 'show_media_info': False, 'name_style': 'default',
            'name_format': '', 'add_file_header': True, 'parse_protobuf_fields': True,
            'api_export_action': 'save'  # 'save' or 'download'
        }
        self.config = self.load_config()

    def load_config(self):
        config_file_path = self.config_path
        if not os.path.exists(config_file_path):
            if getattr(sys, 'frozen', False):
                config_file_path = os.path.join(os.path.dirname(sys.executable), _CONFIG_FILENAME)
        
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                config = self.default_config.copy()
                config.update(loaded_config)
                return config
            except (json.JSONDecodeError, TypeError):
                print(f"警告: 配置文件 '{config_file_path}' 格式错误，将使用默认配置。")
                logger.warning(f"配置文件 '{config_file_path}' 格式错误，将使用默认配置。")
        else:
             print(f"提示: 未找到配置文件 '{_CONFIG_FILENAME}', 将使用默认配置并尝试在程序目录创建。")
             logger.info(f"未找到配置文件 '{_CONFIG_FILENAME}', 将使用默认配置并尝试在程序目录创建。")
        return self.default_config

    def save_config(self, new_config=None):
        if new_config: self.config.update(new_config)
        save_path = self.config_path
        if getattr(sys, 'frozen', False):
            save_path = os.path.join(os.path.dirname(sys.executable), _CONFIG_FILENAME)
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print(f"配置已保存到: {save_path}")
            logger.info(f"配置已保存到: {save_path}")
        except IOError as e:
            print(f"错误: 无法保存配置文件到 '{save_path}'。 {e}")
            logger.error(f"无法保存配置文件到 '{save_path}'。 {e}")

class ProfileManager:
    """
    负责从profile_info.db和group_info.db加载和管理所有用户、好友、群聊和分组信息。
    """
    def __init__(self, profile_db_path, group_info_db_path):
        self.profile_db_path = f"file:{profile_db_path}?mode=ro"
        self.group_info_db_path = f"file:{group_info_db_path}?mode=ro" if group_info_db_path else None
        self.my_uid, self.my_qq = "", ""
        self.all_users, self.friend_uids, self.non_friend_uids = {}, set(), []
        self.friend_groups, self.chat_groups = {}, {}
        self.qq_to_uid_map = {}
        self.uin_to_uid_map = {}

    def load_data(self):
        msg = f"\n正在从 '{os.path.basename(self.profile_db_path.replace('file:', '').split('?')[0])}' 加载用户信息..."
        print(msg); logger.info(msg.strip())
        con = None
        try:
            # V6.7 FIX: Set text_factory after connection for compatibility with older Python versions.
            con = sqlite3.connect(self.profile_db_path, uri=True)
            con.text_factory = lambda b: b.decode('utf-8', 'ignore')
            cur = con.cursor()
            self._load_my_uid(cur)
            self._load_friend_groups(cur)
            self._load_all_profiles(cur)
            self._enrich_friends_info(cur)
            if self.my_uid in self.all_users:
                self.my_qq = self.all_users[self.my_uid].get('qq', 'master')
            print("用户信息加载完毕。"); logger.info("用户信息加载完毕。")
        except sqlite3.Error as e:
            err_msg = f"\n读取身份数据库时发生严重错误: {e}"
            print(err_msg); logger.critical(err_msg.strip())
        finally:
            if con:
                con.close()
        
        self.discover_chat_groups_from_map()
        
        if self.group_info_db_path and GROUP_INFO_DB_CON:
            msg = f"正在从 '{os.path.basename(self.group_info_db_path.replace('file:', '').split('?')[0])}' 加载群组信息..."
            print(msg); logger.info(msg)
            try:
                self._load_group_data(GROUP_INFO_DB_CON.cursor())
                print("群组信息加载完毕。"); logger.info("群组信息加载完毕。")
            except sqlite3.Error as e:
                 err_msg = f"\n读取群组数据库时发生错误: {e}"
                 print(err_msg); logger.error(err_msg.strip())

    def discover_chat_groups_from_map(self):
        for uid, uin in GROUP_UID_TO_UIN_MAP.items():
            if uid not in self.chat_groups:
                 self.chat_groups[uid] = {
                     'id': uid, 'uin': uin, 'name': f"群聊({uin})", 'members': {},
                     'essences':[], 'bulletins':[], 'notifications':[]
                }
            self.uin_to_uid_map[str(uin)] = uid


    def _parse_notify_pb(self, pb_bytes):
        if not pb_bytes: return '未知', '未知'
        try:
            decoded, _ = blackboxprotobuf.decode_message(pb_bytes)
            uid = decoded.get('1', b'').decode('utf-8', 'ignore')
            name = decoded.get('2', b'').decode('utf-8', 'ignore')
            return uid or '未知', name or '未知'
        except Exception: return '解析失败', '解析失败'

    def _load_group_data(self, cur):
        """ V6重构：从 group_info.db 加载所有群聊数据，并遵循优先级原则。"""
        try:
            cur.execute(f'SELECT "60001", "60007" FROM {GROUP_DETAIL_TABLE}')
            for group_uin, name in cur.fetchall():
                group_uid = GROUP_UIN_TO_UID_MAP.get(group_uin)
                if group_uid and group_uid in self.chat_groups:
                    self.chat_groups[group_uid].update({'uin': group_uin, 'name': name or f"群聊({group_uin})"})
        except sqlite3.Error as e:
            warn_msg = f"警告：无法从主群信息表 '{GROUP_DETAIL_TABLE}' 加载数据: {e}"
            print(warn_msg); logger.warning(warn_msg)

        try:
            query = f'SELECT "1000", "1002", "20002", "64003", "64007", "64008", "64010", "64016", "64035", "64023", "60001" FROM {GROUP_MEMBER_TABLE}'
            cur.execute(query)
            for uid, uin, nick, card, join, last_speak, is_admin, is_member, level, title, group_uin in cur.fetchall():
                group_uid = GROUP_UIN_TO_UID_MAP.get(group_uin)
                if group_uid and group_uid in self.chat_groups:
                    self.chat_groups[group_uid]['members'][uid] = {
                        'uid': uid, 'qq': uin, 'nickname': nick, 'card_name': card, 'join_time': join,
                        'last_speak_time': last_speak, 'is_admin': is_admin == 1,
                        'is_member': is_member == 0, 'level': level, 'title': title
                    }
        except sqlite3.Error as e:
            warn_msg = f"警告：无法加载群成员信息: {e}"
            print(warn_msg); logger.warning(warn_msg)
        
        try:
            cur.execute(f'SELECT "60221", "60216", "60005", "60006" FROM {GROUP_LIST_TABLE}')
            active_uins = set()
            for uin, announcement, max_members, current_members in cur.fetchall():
                active_uins.add(uin)
                group_uid = GROUP_UIN_TO_UID_MAP.get(uin)
                if group_uid and group_uid in self.chat_groups:
                    self.chat_groups[group_uid].update({
                        'max_members': max_members,
                        'current_members': current_members,
                        'bulletins': [{'content': announcement}] if announcement else []
                    })
            for group in self.chat_groups.values():
                if group.get('uin') not in active_uins:
                    group['is_left'] = True
        except sqlite3.Error as e:
            warn_msg = f"警告: 无法从 '{GROUP_LIST_TABLE}' 表加载补充群信息: {e}"
            print(warn_msg); logger.warning(warn_msg)

        try:
            cur.execute(f'SELECT "60001", "67501", "67503", "67504", "67505", "67506", "67507", "67508" FROM {GROUP_ESSENCE_TABLE}')
            for group_uin, msg_seq, sender_uin, sender_nick, status, op_uin, op_nick, op_time in cur.fetchall():
                group_uid = GROUP_UIN_TO_UID_MAP.get(group_uin)
                if group_uid in self.chat_groups:
                    if 'essences' not in self.chat_groups[group_uid]: self.chat_groups[group_uid]['essences'] = []
                    self.chat_groups[group_uid]['essences'].append({
                        "group_uin": group_uin, "msg_seq": msg_seq, "sender_uin": sender_uin, "sender_nick": sender_nick,
                        "status": "设为精华" if status == 1 else "取消精华", "op_uin": op_uin, "op_nick": op_nick, "op_time": op_time
                    })
        except sqlite3.Error as e:
            warn_msg = f"警告：无法加载精华消息: {e}"
            print(warn_msg); logger.warning(warn_msg)

        try:
            cur.execute(f'SELECT * FROM {GROUP_NOTIFY_TABLE}')
            cols = [description[0] for description in cur.description]
            for row in cur.fetchall():
                row_dict = dict(zip(cols, row))
                group_info_pb = row_dict.get("61004")
                if not group_info_pb: continue
                
                try:
                    decoded, _ = blackboxprotobuf.decode_message(group_info_pb)
                    group_uin = decoded.get('1')
                except Exception: continue

                group_uid = GROUP_UIN_TO_UID_MAP.get(group_uin)
                if group_uid in self.chat_groups:
                    op_uid, op_name = self._parse_notify_pb(row_dict.get("61006"))
                    target_uid, target_name = self._parse_notify_pb(row_dict.get("61005"))
                    raw_xml = row_dict.get("61025", b'').decode('utf-8', 'ignore') if isinstance(row_dict.get("61025"), bytes) else row_dict.get("61025")
                    
                    if 'notifications' not in self.chat_groups[group_uid]: self.chat_groups[group_uid]['notifications'] = []
                    
                    self.chat_groups[group_uid]['notifications'].append({
                        "msg_time": int(row_dict.get("61001", 0) / 1000),
                        "state": NOTIFY_TYPE_MAP.get(row_dict.get("61002"), f"未知({row_dict.get('61002')})"),
                        "verify_status": NOTIFY_STATUS_MAP.get(row_dict.get("61003"), f"未知({row_dict.get('61003')})"),
                        "operator_uid": op_uid, "operator_name": op_name,
                        "target_uid": target_uid, "target_name": target_name,
                        "op_time": row_dict.get("61008"),
                        "reason": row_dict.get("61010"),
                        "system_msg": row_dict.get("61011"),
                        "raw_xml_details": raw_xml
                    })
        except sqlite3.Error as e:
            warn_msg = f"警告：无法加载群通知: {e}"
            print(warn_msg); logger.warning(warn_msg)


    def _load_my_uid(self, cur):
        cur.execute(f'SELECT "{PROF_COL_UID}" FROM {CATEGORY_LIST_TABLE} LIMIT 1')
        result = cur.fetchone()
        if not result or not result[0]:
            err_msg = f"错误: 无法在 '{CATEGORY_LIST_TABLE}' 表中找到主人UID。"
            print(err_msg); logger.critical(err_msg)
        self.my_uid = result[0]

    def _load_friend_groups(self, cur):
        cur.execute(f'SELECT "{PROF_COL_GROUP_LIST_PB}" FROM {CATEGORY_LIST_TABLE} LIMIT 1')
        pb_data = cur.fetchone()
        if not pb_data or not pb_data[0]: return
        decoded, _ = blackboxprotobuf.decode_message(pb_data[0])
        group_list_data = decoded.get(PROF_COL_GROUP_LIST_PB)
        if not group_list_data: return
        groups = group_list_data if isinstance(group_list_data, list) else [group_list_data]
        for group in groups:
            group_id = group.get(PB_GROUP_ID)
            group_name = group.get(PB_GROUP_NAME, b'').decode('utf-8', 'ignore')
            if group_id is not None and group_name:
                self.friend_groups[group_id] = group_name

    def _load_all_profiles(self, cur):
        query = f'SELECT "{PROF_COL_UID}", "{PROF_COL_QQ}", "{PROF_COL_NICKNAME}", "{PROF_COL_REMARK}" FROM {PROFILE_INFO_TABLE}'
        cur.execute(query)
        for uid, qq, nickname, remark in cur.fetchall():
            self.all_users[uid] = {
                'uid': uid, 'qq': qq or uid, 'nickname': nickname or '', 'remark': remark or '',
                'is_friend': False, 'group_id': -1
            }
            if qq:
                self.qq_to_uid_map[str(qq)] = uid

    def _enrich_friends_info(self, cur):
        query = f'SELECT "{PROF_COL_UID}", "{PROF_COL_QQ}", "{PROF_COL_GROUP_ID}" FROM {BUDDY_LIST_TABLE}'
        cur.execute(query)
        for friend_uid, friend_qq, friend_group_id in cur.fetchall():
            self.friend_uids.add(friend_uid)
            if friend_uid in self.all_users:
                self.all_users[friend_uid]['is_friend'] = True
                self.all_users[friend_uid]['group_id'] = friend_group_id if friend_group_id is not None else -1
                if friend_qq: self.all_users[friend_uid]['qq'] = friend_qq

    def load_non_friends(self, config_mgr):
        if not config_mgr.config.get('export_non_friends', True):
            self.non_friend_uids = []; return
        msg_db_hash = _calculate_sha256(DB_PATH)
        try:
            if os.path.exists(NON_FRIENDS_CACHE_PATH):
                with open(NON_FRIENDS_CACHE_PATH, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    if cache_data.get('msg_db_hash') == msg_db_hash:
                        self.non_friend_uids = cache_data.get('uids', [])
                        msg = f"已从缓存加载 {len(self.non_friend_uids)} 个非好友/临时会话用户。"
                        print(msg); logger.info(msg)
                        return
        except (json.JSONDecodeError, IOError) as e:
            warn_msg = f"警告：读取非好友缓存文件失败: {e}"
            print(warn_msg); logger.warning(warn_msg)

        msg = "正在扫描消息数据库以识别非好友/临时会话..."
        print(msg); logger.info(msg)
        if not os.path.exists(DB_PATH):
            err_msg = f"错误: 消息数据库文件 '{DB_PATH}' 不存在。"
            print(err_msg); logger.error(err_msg)
            return
        all_peer_uids = set()
        con = None
        try:
            # V6.7 FIX: Set text_factory after connection for compatibility.
            con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            con.text_factory = lambda b: b.decode('utf-8', 'ignore')
            cur = con.cursor()
            cur.execute(f"SELECT DISTINCT `{COL_C2C_PEER_UID}` FROM {TABLE_NAME_C2C}")
            for row in cur.fetchall():
                if row[0]: all_peer_uids.add(row[0])
        except sqlite3.Error as e:
            err_msg = f"错误: 扫描消息数据库时出错: {e}"
            print(err_msg); logger.error(err_msg)
            return
        finally:
            if con:
                con.close()

        potential_non_friends = all_peer_uids - self.friend_uids - {self.my_uid}
        valid_non_friends = [uid for uid in potential_non_friends if self.all_users.get(uid, {}).get('nickname')]
        self.non_friend_uids = sorted(list(valid_non_friends))
        msg = f"扫描完成，发现 {len(self.non_friend_uids)} 个有效的非好友/临时会话用户。"
        print(msg); logger.info(msg)
        try:
            with open(NON_FRIENDS_CACHE_PATH, 'w', encoding='utf-8') as f:
                json.dump({'msg_db_hash': msg_db_hash, 'uids': self.non_friend_uids}, f, ensure_ascii=False)
        except IOError as e:
            warn_msg = f"警告: 无法写入非好友缓存文件: {e}"
            print(warn_msg); logger.warning(warn_msg)

    def get_display_name(self, uid, style='default', custom_format="", group_uid=None):
        if group_uid and uid:
            group_info = self.chat_groups.get(str(group_uid))
            if group_info:
                member_info = group_info.get('members', {}).get(uid)
                if member_info and member_info.get('card_name'):
                    return member_info['card_name']
        user = self.all_users.get(uid)
        if not user: return uid
        qq, nickname, remark = user.get('qq', uid), user.get('nickname', ''), user.get('remark', '')
        default_name = remark or nickname or str(qq)
        if style == 'default': return default_name
        if style == 'nickname': return nickname or str(qq)
        if style == 'qq': return str(qq)
        if style == 'uid': return uid
        if style == 'custom':
            return custom_format.format(nickname=nickname or "N/A", remark=remark or "N/A", qq=str(qq), uid=uid)
        return default_name

    def get_filename(self, uid, timestamp_str, export_format='md'):
        ext = f".{export_format}"
        user = self.all_users.get(uid)
        if not user: return f"{uid}{timestamp_str}{ext}"
        qq, nickname, remark = str(user.get('qq', uid)), user.get('nickname', ''), user.get('remark', '')
        name_part, remark_part = nickname or qq, f"(备注-{remark})" if remark else ""
        is_non_friend_tag = "_[非好友]" if not user.get('is_friend', False) else ""
        safe_name_part = re.sub(r'[\\/*?:"<>|]', "_", name_part) or qq
        safe_remark_part = re.sub(r'[\\/*?:"<>|]', "_", remark_part)
        return f"{qq}{is_non_friend_tag}_{safe_name_part}{safe_remark_part}{timestamp_str}{ext}"

# --- Utility Functions ---
def _calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception: return "N/A"
def get_placeholder(value, placeholder="N/A"): return value if value and str(value) != "0" else placeholder
def format_timestamp(ts, fmt="%Y-%m-%d %H:%M:%S"):
    try: return datetime.fromtimestamp(ts).strftime(fmt)
    except (TypeError, ValueError): return f"时间戳({ts})"
def _sanitize_newlines(text: str): return str(text).replace("\n", "[%\\n%]")
def is_port_in_use(port: int, host: str = '127.0.0.1') -> bool:
    """检查指定端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def _parse_flexible_timestamp(time_str, is_end_time=False):
    """
    解析 'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DD' 格式的时间字符串。
    如果只提供日期，则自动附加一天的开始/结束时间。
    """
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        try:
            dt_obj = datetime.strptime(time_str, "%Y-%m-%d")
            if is_end_time:
                dt_obj = dt_obj.replace(hour=23, minute=59, second=59)
            return dt_obj.timestamp()
        except ValueError:
            err_msg = f"错误: 无效的日期时间格式 '{time_str}'. 请使用 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS'。"
            print(err_msg); logger.error(err_msg)
            return None

def get_db_fields():
    all_cols = set()
    for db_con in DB_CONNECTIONS.values():
        if not db_con: continue
        try:
            cur = db_con.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            for table in tables:
                cur.execute(f"PRAGMA table_info('{table}')")
                all_cols.update(row[1] for row in cur.fetchall())
        except sqlite3.Error as e:
            err_msg = f"错误: 扫描数据库字段失败: {e}"
            print(err_msg); logger.error(err_msg)
    sorted_cols = sorted(list(all_cols))
    return [{"name": col, "desc": FIELD_DESCRIPTIONS.get(col, '')} for col in sorted_cols]

def _scan_db_schema(db_con):
    if not db_con: return []
    try:
        cur = db_con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = []
        for row in cur.fetchall():
            table_name = row[0]
            cur.execute(f"PRAGMA table_info('{table_name}')")
            columns = [{"name": col[1], "desc": FIELD_DESCRIPTIONS.get(col[1], '')} for col in cur.fetchall()]
            tables.append({"name": table_name, "columns": columns})
        return tables
    except sqlite3.Error as e:
        err_msg = f"扫描数据库结构时出错: {e}"
        print(err_msg); logger.error(err_msg)
        return []

# --- 消息解析函数 ---
def _extract_readable_text(data: bytes) -> str or None:
    if not data: return None
    try:
        decoded_str = data.decode("utf-8", errors="replace")
        pattern = r"[a-zA-Z0-9\u4e00-\u9fa5\s.,!?;:\'\"()\[\]{}_\-+=*/\\|<>@#$%^&~]+"
        fragments = re.findall(pattern, decoded_str)
        return max(fragments, key=len).strip() if fragments else None
    except Exception: return None

def _parse_single_segment(segment: dict, export_config: dict) -> str:
    if not isinstance(segment, dict): return ""
    msg_type = segment.get(PB_MSG_TYPE)
    
    if msg_type == 6:
        is_interactive_from_subtype = (segment.get(PB_MSG_SUBTYPE) == 5)
        action_id = segment.get(PB_INTERACTIVE_EMOJI_ID) or segment.get(PB_INTERACTIVE_EMOJI_ID_IN_QUOTE)
        if is_interactive_from_subtype or (action_id in INTERACTIVE_EMOJI_MAP):
            action_text = INTERACTIVE_EMOJI_MAP.get(action_id, "未知互动")
            return f"[互动表情: {action_text}]"
        else:
            desc = segment.get(PB_EMOJI_DESC, b'').decode('utf-8', 'ignore')
            return f"[QQ表情: {desc.lstrip('/')}]" if desc else "[QQ表情]"
            
    if msg_type == 2:
        subtype = segment.get(PB_MSG_SUBTYPE)
        if subtype == 7:
            desc_list = segment.get(PB_STICKER_DESC, [])
            return desc_list[0].decode('utf-8', 'ignore') if desc_list else "[动画表情]"
        if subtype in [1, 2]:
            apollo_text = segment.get(PB_APOLLO_TEXT, b'').decode('utf-8', 'ignore')
            return f"[超级QQ秀: {apollo_text}]" if apollo_text else "[动画表情]"
        tag = "[闪照" if segment.get(PB_IMAGE_IS_FLASH) == 1 else "[图片"
        if export_config.get('show_media_info'):
            width, height = segment.get(PB_IMG_WIDTH), segment.get(PB_IMG_HEIGHT)
            if width and height: return f"{tag} {width}x{height}]"
        return f"{tag}]"

    if msg_type == 3:
        filename = segment.get(PB_FILE_NAME, b'').decode('utf-8', 'ignore')
        return f"[文件: {filename}]" if filename else "[文件]"
        
    if msg_type == 5:
        if export_config.get('show_media_info'):
            width, height, duration_sec = segment.get(PB_VID_WIDTH, 0), segment.get(PB_VID_HEIGHT, 0), segment.get(PB_VID_DURATION, 0)
            parts = [f"{width}x{height}"] if width > 0 and height > 0 else []
            if duration_sec > 0: parts.append(f"{duration_sec // 60:02d}:{duration_sec % 60:02d}")
            if parts: return f"[视频 {' '.join(parts)}]"
        return f"[视频]"

    if msg_type == 4:
        duration = segment.get(PB_VOICE_DURATION)
        return f'[语音] {duration}"' if isinstance(duration, int) and duration > 0 else "[语音]"
        
    if msg_type == 9:
        title = segment.get("48403", {}).get(PB_REDPACKET_TITLE, b"").decode("utf-8", "ignore")
        rp_type = segment.get(PB_REDPACKET_TYPE)
        rp_map = {2: "普通红包", 6: "口令红包", 15: "语音红包"}
        return f"[{rp_map.get(rp_type, '红包')}] {title}"
            
    if msg_type == 11 and PB_MARKET_FACE_TEXT in segment: return _sanitize_newlines(segment[PB_MARKET_FACE_TEXT].decode("utf-8", "ignore"))
    if msg_type == 27: return _sanitize_newlines(segment.get(PB_GIFT_TEXT, b'').decode('utf-8', 'ignore')) or "[礼物]"
    if msg_type == 28: return f"[{_sanitize_newlines(segment.get(PB_LOCATION_SHARE_TEXT, b'').decode('utf-8', 'ignore'))}]" or "[位置共享]"
    if PB_TEXT_CONTENT in segment: return _sanitize_newlines(segment.get(PB_TEXT_CONTENT, b"").decode("utf-8", "ignore"))
    return f"[{MSG_TYPE_MAP.get(msg_type, '消息')}]"

def _decode_interactive_gray_tip(segment: dict, profile_mgr, name_style, name_format) -> dict or None:
    try:
        xml = segment.get(PB_GRAYTIP_INTERACTIVE_XML, b"").decode("utf-8", "ignore")
        uids = re.findall(r'<qq uin="([^"]+)"', xml)
        texts = re.findall(r'<nor txt="([^"]*)"', xml)
        if len(uids) >= 2 and len(texts) >= 1:
            actor = profile_mgr.get_display_name(uids[0], name_style, name_format)
            target = profile_mgr.get_display_name(uids[1], name_style, name_format)
            verb = _sanitize_newlines(texts[0] or "戳了戳")
            suffix = _sanitize_newlines(texts[1]) if len(texts) > 1 else ""
            return {"type": "interactive_tip", "actor": actor, "target": target, "verb": verb, "suffix": suffix}
    except Exception: return None

def decode_gray_tip(segment: dict, profile_mgr, name_style, name_format, export_config) -> dict or str or None:
    interactive = _decode_interactive_gray_tip(segment, profile_mgr, name_style, name_format)
    if interactive: return interactive if export_config.get('show_poke') else None
    
    if PB_RECALLER_UID in segment:
        if not export_config.get('show_recall'): return None
        recaller_uid = (segment.get(PB_RECALLER_UID) or b'').decode('utf-8', 'ignore')
        display_name = profile_mgr.get_display_name(recaller_uid, name_style, name_format)
        if display_name == recaller_uid:
            display_name = (segment.get(PB_RECALLER_NAME) or b'').decode('utf-8', 'ignore') or recaller_uid
        recall_suffix = ""
        if export_config.get('show_recall_suffix'):
            recall_suffix = _sanitize_newlines((segment.get(PB_RECALL_SUFFIX) or b'').decode('utf-8', 'ignore'))
        return f"[{display_name} 撤回了一条消息{f' {recall_suffix}' if recall_suffix else ''}]"
    return None

def decode_ark_message(segment: dict) -> str or None:
    try:
        json_str = (segment.get(PB_ARK_JSON) or b'').decode("utf-8", "ignore")
        if not json_str: return None
        data = json.loads(json_str)
        app, prompt = data.get("app"), data.get("prompt", "")
        if app == "com.tencent.map" and data.get("view") == "LocationShare":
            loc_data = data.get('meta', {}).get('Location.Search', {})
            return f"[位置: {get_placeholder(loc_data.get('name'), '未知')} | 地址: {get_placeholder(loc_data.get('address'), '无')}]"
        if app == "com.tencent.music.lua" and data.get("view") == "music":
            music_data = data.get('meta', {}).get('music', {})
            return f"[分享] {get_placeholder(music_data.get('title'))} - {get_placeholder(music_data.get('desc'))}"
        if any(k in prompt for k in ["推荐联系人", "QQ小程序", "聊天记录"]): return _sanitize_newlines(prompt)
        return None
    except Exception: return "[卡片-解析失败]"

def decode_message_content(content, timestamp, profile_mgr, name_style, name_format, export_config, is_timeline=False) -> list or None:
    if not content: return None
    try:
        decoded, _ = blackboxprotobuf.decode_message(content)
        segments_data = decoded.get(PB_MSG_CONTAINER)
        if segments_data is None: return ["[结构错误: 未找到消息容器]"]
        segments = segments_data if isinstance(segments_data, list) else [segments_data]
        parts = []
        for seg in segments:
            if not isinstance(seg, dict): continue
            msg_type = seg.get(PB_MSG_TYPE)
            part = None
            if msg_type not in MSG_TYPE_MAP: continue
            
            if msg_type == 1: part = _sanitize_newlines(seg.get(PB_TEXT_CONTENT, b"").decode("utf-8", "ignore"))
            elif msg_type == 7:
                ts = seg.get(PB_REPLY_ORIGIN_TS)
                origin_content = MESSAGE_CONTENT_CACHE.get(ts) or SALVAGE_CACHE.get(ts)
                if not origin_content:
                    origin_content = _sanitize_newlines(seg.get(PB_REPLY_ORIGIN_SUMMARY_TEXT, b"").decode("utf-8", "ignore"))
                    if not origin_content and seg.get(PB_REPLY_ORIGIN_OBJ):
                        origin_objs = seg.get(PB_REPLY_ORIGIN_OBJ)
                        origin_objs = origin_objs if isinstance(origin_objs, list) else [origin_objs]
                        origin_content = " ".join(filter(None, [_parse_single_segment(o, export_config) for o in origin_objs]))
                s_uid = seg.get(PB_REPLY_ORIGIN_SENDER_UID, b"").decode("utf-8")
                sender = profile_mgr.get_display_name(get_placeholder(s_uid), name_style, name_format)
                if is_timeline:
                    r_uid = seg.get(PB_REPLY_ORIGIN_RECEIVER_UID, b"").decode("utf-8")
                    receiver_user = profile_mgr.all_users.get(r_uid)
                    if receiver_user:
                         receiver = profile_mgr.get_display_name(get_placeholder(r_uid), name_style, name_format)
                    else: 
                        receiver_group = profile_mgr.chat_groups.get(r_uid)
                        receiver = receiver_group.get('name', r_uid) if receiver_group else r_uid
                    part = f"[引用->{format_timestamp(ts)} {sender} -> {receiver}: {origin_content}]"
                else: part = f"[引用->{format_timestamp(ts)} {sender}: {origin_content}]"
            elif msg_type == 21:
                status = seg.get(PB_CALL_STATUS, b"").decode("utf-8", "ignore")
                call_type = "视频通话" if seg.get(PB_CALL_TYPE) == 2 else "语音通话"
                part = f"[{call_type}] {status}"
            elif msg_type == 4:
                text_raw = seg.get(PB_VOICE_TO_TEXT, b"").decode("utf-8", "ignore")
                part = f"[语音] 转文字：{_sanitize_newlines(text_raw)}" if text_raw and export_config.get('show_voice_to_text') else "[语音]"
            elif msg_type == 8: part = decode_gray_tip(seg, profile_mgr, name_style, name_format, export_config)
            elif msg_type == 10: part = decode_ark_message(seg)
            else: part = _parse_single_segment(seg, export_config)
            if part: parts.append(part)
        return parts or None
    except Exception:
        salvaged = _extract_readable_text(content)
        if salvaged:
            SALVAGE_CACHE[timestamp] = salvaged
            return [_sanitize_newlines(salvaged)]
        return [f"[解码失败-B64] {base64.b64encode(content).decode('ascii')}"]

# --- 文件写入函数 ---
def _generate_text_header(config: dict, rows: list, scope_info: dict) -> str:
    """根据导出配置和范围，动态生成用于TXT/MD的文件头字符串"""
    if not config['export_config'].get('add_file_header', False) or not rows:
        return ""
        
    profile_mgr = config['profile_mgr']
    
    msg_db_hash = _calculate_sha256(DB_PATH)
    profile_db_hash = _calculate_sha256(PROFILE_DB_PATH)
    gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    start_time, end_time = format_timestamp(rows[0][0]), format_timestamp(rows[-1][0])
    my_info = profile_mgr.all_users.get(profile_mgr.my_uid, {})
    master_name, master_qq = my_info.get('nickname', '未知'), my_info.get('qq', '未知')
    
    scope_text = "未知范围"
    scope_type = scope_info.get('type')
    if scope_type == 'individual':
        friend_uid = scope_info['friend_uid']
        friend_info = profile_mgr.all_users.get(friend_uid, {})
        friend_nick = friend_info.get('nickname', friend_uid)
        friend_remark = friend_info.get('remark')
        remark_str = f" ({friend_remark})" if friend_remark else ""
        scope_text = f"{master_name} 与 {friend_nick}{remark_str} 的聊天"
    elif scope_type == 'group':
        group_uid = scope_info['group_uid']
        group_info = profile_mgr.chat_groups.get(group_uid, {})
        group_name = group_info.get('name', group_uid)
        group_uin = group_info.get('uin', '未知群号')
        scope_text = f"群聊 \"{group_name}\" ({group_uin}) 的聊天记录"
    elif scope_type == 'timeline':
        title = scope_info.get('title', '多会话时间线')
        participants_details = "\n"
        if scope_info.get('friend_details'):
            participants_details += "包含的个人:\n"
            for user in scope_info['friend_details']:
                participants_details += f"- {user['name']} ({user['id']})\n"
        if scope_info.get('group_details'):
            participants_details += "包含的群聊:\n"
            for group in scope_info['group_details']:
                participants_details += f"- {group['name']} ({group['id']})\n"
        scope_text = f"{title}{participants_details}"

    style_map = {'default': "昵称/备注", 'nickname': "昵称", 'qq': "QQ号码", 'uid': "UID", 'custom': "组合标识"}
    identifier_style_text = style_map.get(config['name_style'], "未知")

    included_features = []
    cfg = config['export_config']
    if cfg.get('show_recall'): included_features.append("撤回提示")
    if cfg.get('show_poke'): included_features.append("拍一拍/戳一戳")
    if cfg.get('show_voice_to_text'): included_features.append("语音转文字")
    hint_text = "此文件由脚本自动生成。记录包含文本、图片、引用"
    if included_features:
        hint_text += f"、{'、'.join(included_features)}"
    hint_text += "等消息。部分Ark卡片、系统消息和未知类型的消息可能被简化或忽略，旨在尽可能还原原始对话顺序和内容。"

    header = (
        "QQ 聊天记录归档\n\n"
        "数据来源:\n"
        f"- nt_msg.decrypt.db (sha256): {msg_db_hash}\n"
        f"- profile_info.decrypt.db (sha256): {profile_db_hash}\n\n"
        f"文件生成时间: {gen_time}\n"
        f"记录开始时间: {start_time}\n"
        f"记录结束时间: {end_time}\n\n"
        f"主人账号: {master_name} ({master_qq})\n"
        f"聊天范围: {scope_text}\n"
        f"用户标识: {identifier_style_text}\n\n"
        f"提示: {hint_text}\n\n"
        f"{'-'*40}\n\n"
    )
    return header

def _generate_html_header(config: dict, rows: list, scope_info: dict) -> str:
    """根据导出配置和范围，动态生成文件头的HTML字符串"""
    if not config['export_config'].get('add_file_header', False) or not rows:
        return ""
        
    profile_mgr = config['profile_mgr']
    
    def safe_escape(value):
        return html.escape(html.unescape(str(value)))

    msg_db_hash = _calculate_sha256(DB_PATH)
    profile_db_hash = _calculate_sha256(PROFILE_DB_PATH)
    gen_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    start_time = format_timestamp(rows[0][0])
    end_time = format_timestamp(rows[-1][0])

    my_info = profile_mgr.all_users.get(profile_mgr.my_uid, {})
    master_name = my_info.get('nickname', '未知')
    master_qq = my_info.get('qq', '未知')
    
    scope_text = "未知范围"
    scope_type = scope_info.get('type')
    if scope_type == 'individual':
        friend_uid = scope_info['friend_uid']
        friend_info = profile_mgr.all_users.get(friend_uid, {})
        friend_nick = friend_info.get('nickname', friend_uid)
        friend_remark = friend_info.get('remark')
        remark_str = f" ({safe_escape(friend_remark)})" if friend_remark else ""
        scope_text = f"{safe_escape(master_name)} 与 {safe_escape(friend_nick)}{remark_str} 的聊天"
    elif scope_type == 'group':
        group_uid = scope_info['group_uid']
        group_info = profile_mgr.chat_groups.get(group_uid, {})
        group_name = group_info.get('name', group_uid)
        group_uin = group_info.get('uin', '未知群号')
        scope_text = f"群聊 \"{safe_escape(group_name)}\" ({group_uin}) 的聊天记录"
    elif scope_type == 'timeline':
        title = safe_escape(scope_info.get('title', '多会话时间线'))
        participants_details = "<div>"
        if scope_info.get('friend_details'):
            participants_details += "<strong>包含的个人:</strong><ul>"
            for user in scope_info['friend_details']:
                participants_details += f"<li>{safe_escape(user['name'])} ({safe_escape(user['id'])})</li>"
            participants_details += "</ul>"
        if scope_info.get('group_details'):
            participants_details += "<strong>包含的群聊:</strong><ul>"
            for group in scope_info['group_details']:
                participants_details += f"<li>{safe_escape(group['name'])} ({safe_escape(group['id'])})</li>"
            participants_details += "</ul>"
        participants_details += "</div>"
        scope_text = f"{title}{participants_details}"

    style_map = {'default': "昵称/备注", 'nickname': "昵称", 'qq': "QQ号码", 'uid': "UID", 'custom': "组合标识"}
    identifier_style_text = style_map.get(config['name_style'], "未知")

    included_features = []
    cfg = config['export_config']
    if cfg.get('show_recall'): included_features.append("撤回提示")
    if cfg.get('show_poke'): included_features.append("拍一拍/戳一戳")
    if cfg.get('show_voice_to_text'): included_features.append("语音转文字")
    hint_text = "此文件由脚本自动生成。记录包含文本、图片、引用"
    if included_features:
        hint_text += f"、{'、'.join(included_features)}"
    hint_text += "等消息。部分Ark卡片、系统消息和未知类型的消息可能被简化或忽略，旨在尽可能还原原始对话顺序和内容。"

    header_html = (
        '<div class="header">\n'
        '    <h1>QQ 聊天记录归档</h1>\n'
        '    <div class="header-group data-source">\n'
        '        <p><strong>数据来源:</strong></p>\n'
        f'        <p>- nt_msg.decrypt.db (sha256): code>{msg_db_hash}</code></p>\n'
        f'        <p>- profile_info.decrypt.db (sha256): <code>{profile_db_hash}</code></p>\n'
        '    </div>\n'
        '    <div class="header-group time-info">\n'
        f'        <p><strong>文件生成时间:</strong> {gen_time}</p>\n'
        f'        <p><strong>记录开始时间:</strong> {start_time}</p>\n'
        f'        <p><strong>记录结束时间:</strong> {end_time}</p>\n'
        '    </div>\n'
        '    <div class="header-group scope-info">\n'
        f'        <p><strong>主人账号:</strong> {safe_escape(master_name)} ({safe_escape(master_qq)})</p>\n'
        f'        <p><strong>聊天范围:</strong> {scope_text}</p>\n'
        f'        <p><strong>用户标识:</strong> {identifier_style_text}</p>\n'
        '    </div>\n'
        '    <div class="header-group hint-info">\n'
        f'        <p><strong>提示:</strong> {html.escape(hint_text)}</p>\n'
        '    </div>\n'
        '</div>'
    )
    return header_html

def _write_txt(f, rows, profile_mgr, config):
    """将聊天记录写入纯文本文件"""
    name_style = config.get('name_style', 'default')
    name_format = config.get('name_format', '')
    count = 0
    is_timeline = config['is_timeline']
    is_group = config.get('is_group', False)

    for row in rows:
        ts, s_uid, p_uid, content = row[:4]
        chat_type = row[4] if is_timeline else ('group' if is_group else 'c2c')
        group_uid = p_uid if chat_type == 'group' else None

        parts = decode_message_content(content, ts, profile_mgr, name_style, name_format, config['export_config'], is_timeline)
        if not parts: continue
        
        is_reply = isinstance(parts[0], str) and parts[0].startswith('[引用->')
        text = " ".join(str(p) for p in parts if not isinstance(p, dict))
        
        if not is_reply: MESSAGE_CONTENT_CACHE[ts] = text
        
        time = format_timestamp(ts)
        first_part = parts[0]

        if isinstance(first_part, dict) and first_part.get("type") == "interactive_tip":
            body = f"{first_part['actor']} {first_part['verb']} {first_part['target']}{first_part['suffix']}"
            line = f"[{time}] [系统提示]: {body}\n"
        else:
            sender = profile_mgr.get_display_name(get_placeholder(s_uid), name_style, name_format, group_uid=group_uid)
            if sender == "N/A": sender = "[系统提示]"
            
            if is_timeline:
                receiver_name = ""
                if chat_type == 'c2c':
                    receiver_uid = profile_mgr.my_uid if s_uid == p_uid else p_uid
                    receiver_name = profile_mgr.get_display_name(get_placeholder(receiver_uid), name_style, name_format)
                elif chat_type == 'group':
                    group = profile_mgr.chat_groups.get(p_uid)
                    receiver_name = f"群聊({group.get('name', p_uid)})" if group else f"群聊({p_uid})"
                line = f"[{time}] {sender} -> {receiver_name}: {text}\n"
            else:
                line = f"[{time}] {sender}: {text}\n"
        f.write(line)
        count += 1
    return count

def _write_md(f, rows, profile_mgr, config):
    """将聊天记录写入Markdown文件"""
    name_style = config.get('name_style', 'default')
    name_format = config.get('name_format', '')
    count = 0
    last_date = None
    last_sender_key = None
    last_element_was_quote = False
    is_timeline = config['is_timeline']
    is_group = config.get('is_group', False)

    for row in rows:
        ts, s_uid, p_uid, content = row[:4]
        chat_type = row[4] if is_timeline else ('group' if is_group else 'c2c')
        group_uid = p_uid if chat_type == 'group' else None
        
        parts = decode_message_content(content, ts, profile_mgr, name_style, name_format, config['export_config'], is_timeline)
        if not parts: continue
        
        dt_object = datetime.fromtimestamp(ts)
        current_date, current_time = dt_object.strftime("%Y-%m-%d"), dt_object.strftime("%H:%M:%S")

        sender_display = profile_mgr.get_display_name(get_placeholder(s_uid), name_style, name_format, group_uid=group_uid)
        if sender_display == "N/A":
            sender_key = "[系统提示]"
        elif is_timeline:
            receiver_name = ""
            if chat_type == 'c2c':
                receiver_uid = profile_mgr.my_uid if s_uid == p_uid else p_uid
                receiver_name = profile_mgr.get_display_name(get_placeholder(receiver_uid), name_style, name_format)
            elif chat_type == 'group':
                group = profile_mgr.chat_groups.get(p_uid)
                receiver_name = f"群聊({group.get('name', p_uid)})" if group else f"群聊({p_uid})"
            sender_key = f"{sender_display} -> {receiver_name}"
        else:
            sender_key = sender_display

        if current_date != last_date:
            if last_date and not last_element_was_quote: f.write("\n")
            f.write(f"# {current_date}\n")
            last_date, last_sender_key, last_element_was_quote = current_date, None, False
        
        if sender_key != last_sender_key:
            if not last_element_was_quote: f.write("\n")
            f.write(f"### {sender_key}\n")
            last_sender_key, last_element_was_quote = sender_key, False

        main_text_parts, quote_content = [], ""
        is_reply = isinstance(parts[0], str) and parts[0].startswith('[引用->')
        
        if not is_reply and isinstance(parts[0], dict) and parts[0].get("type") == "interactive_tip":
            tip = parts[0]
            main_text_parts.append(f"{tip['actor']} {tip['verb']} {tip['target']}{tip['suffix']}")
        else:
            for p in parts:
                p_str = str(p)
                match = re.search(r'\[引用->(.*)\]', p_str)
                if match: quote_content = match.group(1)
                else: main_text_parts.append(p_str)
        
        main_text = " ".join(main_text_parts)
        if not is_reply: MESSAGE_CONTENT_CACHE[ts] = main_text
        if sender_key == "[系统提示]" and main_text.startswith('[') and main_text.endswith(']'): main_text = main_text[1:-1]

        f.write(f"* {current_time} {main_text}\n")
        if quote_content:
            f.write(f"  > {quote_content}\n\n")
            last_element_was_quote = True
        else:
            last_element_was_quote = False
        
        count += 1
    return count

def _write_html(f, rows, profile_mgr, config, scope_info):
    """将聊天记录写入HTML文件"""
    template_filename = config['export_config'].get('html_template', 'default.html')
    template_path = os.path.join(TEMPLATE_DIR_PATH, template_filename)

    try:
        with open(template_path, 'r', encoding='utf-8') as tpl_f:
            template_str = tpl_f.read()
    except FileNotFoundError:
        f.write(f"<h1>错误</h1><p>HTML模板文件 '{template_filename}' 未在 '{TEMPLATE_DIR_PATH}' 文件夹中找到。</p>")
        return 0
    except Exception as e:
        f.write(f"<h1>错误</h1><p>读取HTML模板文件时出错: {e}</p>")
        return 0

    name_style, name_format = config.get('name_style', 'default'), config.get('name_format', '')
    def safe_escape(value): return html.escape(html.unescape(str(value)))
    
    header_html = _generate_html_header(config, rows, scope_info)
    content_html_parts, last_date, last_sender_key = [], None, None
    is_timeline = config['is_timeline']
    is_group = config.get('is_group', False)

    def close_open_tags():
        if last_sender_key: content_html_parts.append('</div></div>') 
        if last_date: content_html_parts.append('</div></details>')

    for row in rows:
        ts, s_uid, p_uid, content = row[:4]
        chat_type = row[4] if is_timeline else ('group' if is_group else 'c2c')
        group_uid = p_uid if chat_type == 'group' else None
        parts = decode_message_content(content, ts, profile_mgr, name_style, name_format, config['export_config'], is_timeline)
        if not parts: continue
        
        dt_object = datetime.fromtimestamp(ts)
        current_date, current_time = dt_object.strftime("%Y-%m-%d"), dt_object.strftime("%H:%M:%S")

        sender_display = profile_mgr.get_display_name(get_placeholder(s_uid), name_style, name_format, group_uid=group_uid)
        if sender_display == "N/A":
            sender_key = "[系统提示]"
        elif is_timeline:
            receiver_name = ""
            if chat_type == 'c2c':
                receiver_uid = profile_mgr.my_uid if s_uid == p_uid else p_uid
                receiver_name = profile_mgr.get_display_name(get_placeholder(receiver_uid), name_style, name_format)
            elif chat_type == 'group':
                group = profile_mgr.chat_groups.get(p_uid)
                receiver_name = f"群聊({group.get('name', p_uid)})" if group else f"群聊({p_uid})"
            sender_key = f"{sender_display} -> {receiver_name}"
        else:
            sender_key = sender_display

        if current_date != last_date:
            close_open_tags()
            content_html_parts.append(f'<details class="date-block" open><summary>{current_date}</summary><div class="chat-day-content">')
            last_date, last_sender_key = current_date, None
        
        if sender_key != last_sender_key:
            if last_sender_key: content_html_parts.append('</div></div>')
            speaker_class = "is-self" if s_uid == profile_mgr.my_uid else "is-other"
            if sender_key == "[系统提示]":
                content_html_parts.append('<div class="system-message-container"><div class="message-block">')
            else:
                content_html_parts.append(f'<div class="sender-message-group {speaker_class}">')
                content_html_parts.append(f'<div class="sender">{safe_escape(sender_key)}</div>')
                content_html_parts.append('<div class="message-block">')
            last_sender_key = sender_key

        main_text_parts, quote_content = [], ""
        is_reply = isinstance(parts[0], str) and parts[0].startswith('[引用->')

        if not is_reply and isinstance(parts[0], dict) and parts[0].get("type") == "interactive_tip":
            tip = parts[0]
            main_text_parts.append(f"{safe_escape(tip['actor'])} {safe_escape(tip['verb'])} {safe_escape(tip['target'])}{safe_escape(tip['suffix'])}")
        else:
            for p in parts:
                p_str = str(p)
                match = re.search(r'\[引用->(.*)\]', p_str)
                if match: quote_content = match.group(1)
                else: main_text_parts.append(p_str)
        
        main_text = " ".join(main_text_parts)
        if not is_reply: MESSAGE_CONTENT_CACHE[ts] = main_text
        escaped_main_text = safe_escape(main_text).replace('[%\\n%]', '<br>')
        
        if sender_key == "[系统提示]":
             if escaped_main_text.startswith('[') and escaped_main_text.endswith(']'): escaped_main_text = escaped_main_text[1:-1]
             content_html_parts.append(f'<div class="sys-message">{escaped_main_text}</div>')
        else:
            content_html_parts.append(f'<div class="message-item"><span class="timestamp">{current_time}</span><span class="message-content">{escaped_main_text}</span></div>')

        if quote_content:
            escaped_quote = safe_escape(quote_content).replace('[%\\n%]', '<br>')
            content_html_parts.append(f'<div class="reply-container"><blockquote>{escaped_quote}</blockquote></div>')

    close_open_tags()
    final_html = template_str.replace('{{file_header}}', header_html).replace('{{chat_content}}', '\n'.join(content_html_parts))
    f.write(final_html)
    return len(rows)

def process_and_write(output_path, rows, profile_mgr, config, scope_info):
    """处理并写入文件，返回 (写入的条目数, 文件路径)"""
    export_format = config.get('export_format', 'md')
    is_timeline = config.get('is_timeline', False)
    is_group = scope_info.get('type') == 'group'

    valid_rows = [row for row in rows if decode_message_content(row[3], row[0], profile_mgr, config['name_style'], config['name_format'], config['export_config'], is_timeline)]
    if not valid_rows:
        return 0, None

    write_config = {**config, 'is_group': is_group}

    with open(output_path, "w", encoding="utf-8-sig", newline='') as f:
        if export_format == 'html':
            count = _write_html(f, valid_rows, profile_mgr, write_config, scope_info)
        else:
            f.write(_generate_text_header(write_config, valid_rows, scope_info))
            if export_format == 'md':
                count = _write_md(f, valid_rows, profile_mgr, write_config)
            else:
                count = _write_txt(f, valid_rows, profile_mgr, write_config)
    
    return count, output_path

def _write_json(f, rows_as_dicts):
    """将字典列表写入JSON文件，并处理bytes类型。"""
    processed_rows = []
    for row in rows_as_dicts:
        processed_row = {}
        for key, value in row.items():
            if isinstance(value, bytes):
                processed_row[key] = base64.b64encode(value).decode('ascii')
            else:
                processed_row[key] = value
        processed_rows.append(processed_row)
    
    json.dump(processed_rows, f, indent=4, ensure_ascii=False)
    return len(processed_rows)

def _write_csv(f, rows_as_dicts, field_names):
    """将字典列表写入CSV文件。"""
    if not rows_as_dicts: return 0
    writer = csv.DictWriter(f, fieldnames=field_names)
    writer.writeheader()
    
    for row in rows_as_dicts:
        processed_row = {}
        for key, value in row.items():
            if isinstance(value, bytes):
                try:
                    processed_row[key] = value.decode('utf-8', 'ignore')
                except:
                    processed_row[key] = base64.b64encode(value).decode('ascii')
            else:
                processed_row[key] = value
        writer.writerow(processed_row)
    return len(rows_as_dicts)

# --- WebSocket Handlers ---
async def send_json(websocket, data):
    # Determine if it's a data-intensive message and prepare log content
    log_data_type = data.get("type")
    data_intensive_types = ["initial_data", "chat_history", "db_fields", "db_info"]
    is_intensive = log_data_type in data_intensive_types

    if is_intensive:
        summary = {k: v for k, v in data.items() if k not in ["history", "friends", "groups", "fields", "data"]}
        summary['...data omitted...'] = True
        log_message = json.dumps(summary, ensure_ascii=False)
        console_log_message = json.dumps(summary, ensure_ascii=False, indent=2)
    else:
        log_message = json.dumps(data, ensure_ascii=False)
        console_log_message = json.dumps(data, ensure_ascii=False, indent=2)

    # Log to file (level is handled by setup_logging)
    logger.debug(f"SEND -> {log_message}")

    # Log to console if --log is enabled
    if LOG_TO_CONSOLE:
        print(f"[LOG] SEND -> {console_log_message}")
    
    # Send the full, original data to the client
    await websocket.send(json.dumps(data, ensure_ascii=False))

async def handle_get_initial_data(websocket):
    if not PROFILE_MGR: await send_json(websocket, {"type": "error", "message": "Profile manager not initialized."}); return
    friend_groups = {gid: {"name": name, "users": []} for gid, name in PROFILE_MGR.friend_groups.items()}
    friend_groups[-1] = {"name": "默认分组", "users": []}
    for uid in PROFILE_MGR.friend_uids:
        user_info = PROFILE_MGR.all_users.get(uid)
        if user_info:
            gid = user_info.get('group_id', -1)
            if gid not in friend_groups: gid = -1
            friend_groups[gid]['users'].append(user_info)
    if PROFILE_MGR.non_friend_uids:
        friend_groups[-2] = {"name": "[非好友/临时会话]", "users": []}
        for uid in PROFILE_MGR.non_friend_uids:
            if uid in PROFILE_MGR.all_users: friend_groups[-2]['users'].append(PROFILE_MGR.all_users[uid])
    for gid in friend_groups: friend_groups[gid]['users'].sort(key=lambda u: u.get('remark') or u.get('nickname') or u.get('qq'))
    
    groups_for_frontend = []
    for g in PROFILE_MGR.chat_groups.values():
        groups_for_frontend.append({
            'id': g['id'],
            'uin': g.get('uin', g['id']),
            'name': g.get('name', f"群聊({g.get('uin', '未知')})"),
            'member_count': g.get('current_members', 'N/A'),
            'max_member_count': g.get('max_members', 'N/A')
        })

    await send_json(websocket, {
        "type": "initial_data", "my_uid": PROFILE_MGR.my_uid,
        "friends": dict(sorted(friend_groups.items())),
        "groups": sorted(groups_for_frontend, key=lambda g: g['name']),
        "config": CONFIG_MGR.config, "workdir": os.path.abspath(WORK_DIR)
    })

async def handle_get_db_fields(websocket): await send_json(websocket, {"type": "db_fields", "fields": DB_FIELDS_CACHE})

async def handle_get_db_info(websocket):
    db_info_payload = {}
    for name, con in DB_CONNECTIONS.items():
        if con:
            db_info_payload[name] = _scan_db_schema(con)
    await send_json(websocket, {"type": "db_info", "data": db_info_payload})

async def handle_get_chat_history(websocket, data):
    chat_type, chat_id = data.get("type"), data.get("id")
    before_ts, from_ts = data.get("before_ts"), data.get("from_ts")
    if not all([chat_type, chat_id, DB_CON]): return

    cur, history, params, prepend = DB_CON.cursor(), [], [chat_id], False
    table_name, peer_col, group_uid_for_name = (TABLE_NAME_C2C, COL_C2C_PEER_UID, None) if chat_type == 'friend' else (TABLE_NAME_GROUP, COL_GROUP_ID_UID, chat_id)
    query = f"SELECT `{COL_TIMESTAMP}`, `{COL_SENDER_UID}`, `{COL_MSG_CONTENT}` FROM {table_name} WHERE `{peer_col}` = ?"
    
    order_clause = f"ORDER BY `{COL_TIMESTAMP}` DESC"
    limit_clause = "LIMIT 200"

    if before_ts: 
        query += f" AND `{COL_TIMESTAMP}` < ?"
        params.append(before_ts)
        prepend = True
    elif from_ts:
        end_ts = from_ts + 86400 # 修复：获取一整天的数据
        query += f" AND `{COL_TIMESTAMP}` BETWEEN ? AND ?"
        params.extend([from_ts, end_ts])
        order_clause = f"ORDER BY `{COL_TIMESTAMP}` ASC"
        limit_clause = "LIMIT 2000" # 增加单日消息上限
    
    query += f" {order_clause} {limit_clause}"

    cur.execute(query, params)
    results = cur.fetchall()
    if order_clause.endswith("DESC"): results.reverse()
    
    for ts, s_uid, content in results:
        parts = decode_message_content(content, ts, PROFILE_MGR, 'default', '', CONFIG_MGR.config)
        if not parts: continue
        is_system_tip = isinstance(parts[0], dict) and parts[0].get('type') == 'interactive_tip'
        if is_system_tip: text_parts = [f"{parts[0]['actor']} {parts[0]['verb']} {parts[0]['target']}{parts[0]['suffix']}"]
        else: text_parts = [str(p) for p in parts if not isinstance(p, dict)]
        final_text = " ".join(text_parts)
        
        msg_obj = {
            "ts": ts, "s_uid": s_uid, "text": html.escape(final_text).replace('[%\\n%]', '<br>'),
            "sender_name": PROFILE_MGR.get_display_name(s_uid, group_uid=group_uid_for_name),
            "is_system_tip": is_system_tip
        }
        if group_uid_for_name:
             group_info = PROFILE_MGR.chat_groups.get(group_uid_for_name)
             if group_info and s_uid in group_info['members']:
                 member_info = group_info['members'][s_uid]
                 msg_obj['level'] = member_info.get('level')
                 msg_obj['title'] = member_info.get('title')
        history.append(msg_obj)
        
    await send_json(websocket, {"type": "chat_history", "history": history, "prepend": prepend, "is_date_jump": bool(from_ts)})

async def handle_save_config(websocket, data):
    new_config = data.get("config")
    if new_config and CONFIG_MGR:
        CONFIG_MGR.save_config(new_config)
        await send_json(websocket, {"type": "config_saved"})
        PROFILE_MGR.load_non_friends(CONFIG_MGR)
        await handle_get_initial_data(websocket)

async def handle_start_export(websocket, data): await asyncio.get_running_loop().run_in_executor(None, run_export_task_ws, asyncio.get_running_loop(), websocket, data.get("params", {}))
async def handle_export_extra_group_data(websocket, data): await asyncio.get_running_loop().run_in_executor(None, run_export_extra_task, asyncio.get_running_loop(), websocket, data)
async def handle_start_raw_export(websocket, data): await asyncio.get_running_loop().run_in_executor(None, run_raw_export_task, asyncio.get_running_loop(), websocket, data.get("params", {}))

# --- Export Tasks ---
def export_one_on_one(config, friend_uid, scope_info, send_status, out_dir=None):
    """导出一个好友的一对一聊天记录, 返回文件路径或None。"""
    profile_mgr, start_ts, end_ts = config['profile_mgr'], config['start_ts'], config['end_ts']
    friend_display_name = profile_mgr.get_display_name(friend_uid)
    
    send_status(f"正在处理: {friend_display_name}...")
    
    query = f"SELECT `{COL_TIMESTAMP}`, `{COL_SENDER_UID}`, `{COL_C2C_PEER_UID}`, `{COL_MSG_CONTENT}` FROM {TABLE_NAME_C2C}"
    clauses = [f"`{COL_C2C_PEER_UID}` = ?"]
    params = [friend_uid]

    if start_ts and start_ts > 0:
        clauses.append(f"`{COL_TIMESTAMP}` >= ?")
        params.append(start_ts)
    if end_ts and end_ts > 0:
        clauses.append(f"`{COL_TIMESTAMP}` <= ?")
        params.append(end_ts)
    query += f" WHERE {' AND '.join(clauses)} ORDER BY `{COL_TIMESTAMP}` ASC"
    
    cur = DB_CON.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    
    if not rows:
        send_status(f"处理完成: {friend_display_name} -> 指定时间内无聊天记录。")
        return None

    output_dir = out_dir or os.path.join(OUTPUT_DIR, "Individual")
    os.makedirs(output_dir, exist_ok=True)
    filename = profile_mgr.get_filename(friend_uid, config['run_timestamp'], config.get('export_format', 'md'))
    path = os.path.join(output_dir, filename)
        
    process_config = {**config, 'is_timeline': False}
    count, written_path = process_and_write(path, rows, profile_mgr, process_config, scope_info)
    
    if count > 0:
        send_status(f"处理完成: {friend_display_name} -> 共导出 {count} 条消息到 \"{os.path.abspath(path)}\"")
        return written_path
    else:
        send_status(f"处理完成: {friend_display_name} -> 指定时间内无有效消息可导出。")
        return None

def export_group_chat(config, group_uid, scope_info, send_status, output_dir_base=None):
    """导出一个群聊的聊天记录, 返回文件路径或None。"""
    profile_mgr, start_ts, end_ts = config['profile_mgr'], config['start_ts'], config['end_ts']
    group_info = profile_mgr.chat_groups.get(str(group_uid), {})
    group_name = group_info.get('name', group_uid)
    group_uin = group_info.get('uin', '未知群号')
    
    send_status(f"正在处理群聊: {group_name} ({group_uin})...")
    
    query = f"SELECT `{COL_TIMESTAMP}`, `{COL_SENDER_UID}`, `{COL_GROUP_ID_UID}`, `{COL_MSG_CONTENT}` FROM {TABLE_NAME_GROUP}"
    clauses = [f"`{COL_GROUP_ID_UID}` = ?"]
    params = [group_uid]
    
    if start_ts and start_ts > 0:
        clauses.append(f"`{COL_TIMESTAMP}` >= ?"); params.append(start_ts)
    if end_ts and end_ts > 0:
        clauses.append(f"`{COL_TIMESTAMP}` <= ?"); params.append(end_ts)
    query += f" WHERE {' AND '.join(clauses)} ORDER BY `{COL_TIMESTAMP}` ASC"

    cur = DB_CON.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    
    if not rows:
        send_status(f"处理完成: {group_name} -> 指定时间内无聊天记录。")
        return None
    
    base_dir = output_dir_base or OUTPUT_DIR
    output_dir = os.path.join(base_dir, "Individual", "Groups")
    os.makedirs(output_dir, exist_ok=True)
    
    safe_name = re.sub(r'[\\/*?:"<>|]', '_', str(group_name))
    filename = f"群聊_{safe_name}_{group_uin}{config['run_timestamp']}.{config.get('export_format', 'md')}"
    path = os.path.join(output_dir, filename)

    process_config = {**config, 'is_timeline': False}
    count, written_path = process_and_write(path, rows, profile_mgr, process_config, scope_info)

    if count > 0:
        send_status(f"处理完成: {group_name} -> 共导出 {count} 条消息到 \"{os.path.abspath(path)}\"")
        return written_path
    else:
        send_status(f"处理完成: {group_name} -> 指定时间内无有效消息可导出。")
        return None


def export_timeline(config, friend_uids, group_uids, scope_info, send_status, output_dir_base=None):
    """执行全局时间线导出, 返回文件路径或None。"""
    send_status("正在执行“全局时间线”导出...")
    start_ts, end_ts = config['start_ts'], config['end_ts']
    
    base_queries = []
    params = []
    
    time_clauses = []
    time_params = []
    if start_ts and start_ts > 0:
        time_clauses.append(f"`{COL_TIMESTAMP}` >= ?")
        time_params.append(start_ts)
    if end_ts and end_ts > 0:
        time_clauses.append(f"`{COL_TIMESTAMP}` <= ?")
        time_params.append(end_ts)
    time_where_sql = f"AND {' AND '.join(time_clauses)}" if time_clauses else ""

    if friend_uids:
        placeholders = ', '.join('?' for _ in friend_uids)
        c2c_query = f"SELECT `{COL_TIMESTAMP}`, `{COL_SENDER_UID}`, `{COL_C2C_PEER_UID}`, `{COL_MSG_CONTENT}`, 'c2c' as chat_type FROM {TABLE_NAME_C2C} WHERE `{COL_C2C_PEER_UID}` IN ({placeholders}) {time_where_sql}"
        base_queries.append(c2c_query)
        params.extend(friend_uids)
        params.extend(time_params)

    if group_uids:
        placeholders = ', '.join('?' for _ in group_uids)
        group_query = f"SELECT `{COL_TIMESTAMP}`, `{COL_SENDER_UID}`, `{COL_GROUP_ID_UID}`, `{COL_MSG_CONTENT}`, 'group' as chat_type FROM {TABLE_NAME_GROUP} WHERE `{COL_GROUP_ID_UID}` IN ({placeholders}) {time_where_sql}"
        base_queries.append(group_query)
        params.extend(group_uids)
        params.extend(time_params)
    
    if not base_queries:
        send_status("未选择任何会话，时间线导出中止。"); return None

    full_query = " UNION ALL ".join(base_queries)
    full_query += f" ORDER BY `{COL_TIMESTAMP}` ASC"
    
    cur = DB_CON.cursor()
    cur.execute(full_query, params)
    rows = cur.fetchall()
    
    if not rows: send_status("查询完成，但在指定范围内未能获取任何记录。"); return None
        
    ext = f".{config.get('export_format', 'md')}"
    base_dir = output_dir_base or OUTPUT_DIR
    timeline_dir = os.path.join(base_dir, "Timeline")
    os.makedirs(timeline_dir, exist_ok=True)
    count_str = f"_{len(friend_uids)}人_{len(group_uids)}群"
    filename = f"{_TIMELINE_FILENAME_BASE}{count_str}{config['run_timestamp']}{ext}"
    path = os.path.join(timeline_dir, filename)
    
    process_config = {**config, 'is_timeline': True}
    count, written_path = process_and_write(path, rows, PROFILE_MGR, process_config, scope_info)
    
    if count > 0:
        send_status(f"处理完成！共导出 {count} 条有效消息到 {os.path.abspath(path)}")
        return written_path
    else:
        send_status("处理完成，但在指定范围内未发现可导出的有效消息。")
        return None


def export_custom_format(config, targets, send_status, output_dir_base=None):
    """执行自定义格式导出, 返回生成的文件路径列表。"""
    profile_mgr = config['profile_mgr']
    start_ts, end_ts = config['start_ts'], config['end_ts']
    custom_fields = config['custom_fields']
    export_format = config['export_format'].replace('-custom', '') # json or csv
    parse_protobuf_fields = config.get('parse_protobuf_fields', False)
    
    if not custom_fields: send_status("错误：未提供自定义导出的字段列表。"); return []

    all_valid_field_names = {f['name'] for f in DB_FIELDS_CACHE}
    msg_db_fields = {f for f in custom_fields if f.startswith('4')}
    group_info_fields = {f for f in custom_fields if not f.startswith('4')}
    
    if not msg_db_fields and not group_info_fields: send_status("错误：提供的所有自定义字段均无效。"); return []

    fields_to_query = {f for f in msg_db_fields if f in all_valid_field_names}
    if parse_protobuf_fields and '40800' in fields_to_query:
        fields_to_query.add('40050'); fields_to_query.add('40020')
    
    written_files = []
    for target in targets:
        is_group, target_id = target['type'] == 'group', target['id']
        base_dir = output_dir_base or OUTPUT_DIR

        if is_group:
            table_name, peer_col = TABLE_NAME_GROUP, COL_GROUP_ID_UID
            group_info = profile_mgr.chat_groups.get(str(target_id), {})
            target_name = group_info.get('name', target_id)
            group_uin = group_info.get('uin', '未知群号')
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', str(target_name))
            filename = f"群聊_{safe_name}_{group_uin}{config['run_timestamp']}.{export_format}"
            output_dir = os.path.join(base_dir, "Custom", "Groups")
        else: # friend
            if group_info_fields:
                send_status(f"跳过: {profile_mgr.get_display_name(target_id)} -> 自定义导出中包含群聊专属字段，无法用于私聊。")
                continue
            table_name, peer_col = TABLE_NAME_C2C, COL_C2C_PEER_UID
            target_name = profile_mgr.get_display_name(target_id)
            filename = profile_mgr.get_filename(target_id, config['run_timestamp'], export_format)
            output_dir = os.path.join(base_dir, "Custom", "Friends")

        send_status(f"正在处理自定义导出: {target_name}...")
        
        field_str = ", ".join(f"`{f}`" for f in fields_to_query) if fields_to_query else "'placeholder' as placeholder"
        query = f"SELECT {field_str} FROM {table_name}"
        clauses, params = [f"`{peer_col}` = ?"], [target_id]

        if start_ts and start_ts > 0 and '40050' in fields_to_query: clauses.append(f"`{COL_TIMESTAMP}` >= ?"); params.append(start_ts)
        if end_ts and end_ts > 0 and '40050' in fields_to_query: clauses.append(f"`{COL_TIMESTAMP}` <= ?"); params.append(end_ts)
        query += f" WHERE {' AND '.join(clauses)} ORDER BY `{COL_TIMESTAMP}` ASC"
        
        cur = DB_CON.cursor(); cur.execute(query, params); rows = cur.fetchall()

        if not rows: send_status(f"处理完成: {target_name} -> 指定时间内无聊天记录。"); continue
            
        rows_as_dicts = [dict(zip(fields_to_query, row)) for row in rows]
        
        for row_dict in rows_as_dicts:
            if 'placeholder' in row_dict: del row_dict['placeholder']
            sender_uid = row_dict.get('40020')
            if parse_protobuf_fields and '40800' in row_dict and isinstance(row_dict['40800'], bytes):
                content, timestamp = row_dict['40800'], row_dict.get('40050', 0)
                parsed_parts = decode_message_content(content, timestamp, profile_mgr, 'default', '', config['export_config'])
                row_dict['40800'] = " ".join(str(p) for p in parsed_parts).replace('[%\\n%]', '\n') if parsed_parts else "[内容解析失败]"

            if is_group and group_info_fields and sender_uid:
                group_info = profile_mgr.chat_groups.get(str(target_id))
                if group_info and 'members' in group_info:
                    member_info = group_info['members'].get(sender_uid)
                    if member_info:
                        field_map = {
                            '1000': 'uid', '1002': 'qq', '20002': 'nickname',
                            '64003': 'card_name', '64007': 'join_time', '64008': 'last_speak_time',
                            '64010': 'is_admin', '64016': 'is_member', '64035': 'level',
                            '64023': 'title'
                        }
                        for field_code in group_info_fields:
                            if field_code in field_map:
                                row_dict[field_code] = member_info.get(field_map.get(field_code))

        final_rows = [{key: row.get(key) for key in custom_fields} for row in rows_as_dicts]
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, filename)

        try:
            with open(path, "w", encoding="utf-8-sig", newline='') as f:
                count = _write_json(f, final_rows) if export_format == 'json' else _write_csv(f, final_rows, custom_fields)
            send_status(f"处理完成: {target_name} -> 共导出 {count} 条记录到 \"{os.path.abspath(path)}\"")
            written_files.append(path)
        except Exception as e:
            send_status(f"错误: 写入文件 {filename} 时失败: {e}")
            
    return written_files

def run_export_extra_task(loop, websocket, data, output_location=None):
    """Router for exporting extra group data like members, bulletins, etc. Returns file path."""
    is_cli = not loop and not websocket
    def send_status_cli(message): print(message)
    def send_status_ws(message):
        asyncio.run_coroutine_threadsafe(send_json(websocket, {"type": "export_status", "message": message}), loop).result()
    
    send_status = send_status_cli if is_cli else send_status_ws
    
    try:
        group_id, data_type = data.get("group_id"), data.get("data_type")
        group_info = PROFILE_MGR.chat_groups.get(str(group_id))
        if not group_info:
            send_status(f"错误：无法找到群 {group_id} 的信息。"); return None
        
        group_name, uin = group_info.get('name', group_id), group_info.get('uin', group_id)
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', str(group_name))
        
        base_output_dir = output_location or OUTPUT_DIR
        output_dir = os.path.join(base_output_dir, "GroupData")
        os.makedirs(output_dir, exist_ok=True)
        
        export_map = {
            "members": ("成员列表", "members", ['uid', 'qq', 'nickname', 'card_name', 'join_time', 'last_speak_time', 'is_admin', 'is_member', 'level', 'title']),
            "bulletins": ("群公告", "bulletins", ['content']),
            "essences": ("精华消息", "essences", ['op_time', 'status', 'sender_uin', 'sender_nick', 'op_uin', 'op_nick', 'msg_seq']),
            "notifications": ("成员变更", "notifications", ['msg_time', 'state', 'verify_status', 'operator_name', 'target_name', 'reason', 'system_msg', 'raw_xml_details'])
        }
        
        if data_type not in export_map:
            send_status(f"错误：未知的导出数据类型 '{data_type}'。"); return None
            
        title, data_key, headers = export_map[data_type]
        send_status(f"正在导出群 '{group_name}' 的 {title}...")
        
        records = group_info.get(data_key, [])
        if data_type == 'members': records = list(records.values())

        if not records:
            send_status(f"群 '{group_name}' 中没有 {title} 可导出。"); return None

        filename = f"{title}_{safe_name}_{uin}.csv"
        path = os.path.join(output_dir, filename)

        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()
            sort_key = headers[0] if headers else ''
            for record in sorted(records, key=lambda r: r.get(sort_key, 0), reverse=True):
                r_copy = record.copy()
                for key, val in r_copy.items():
                    if 'time' in key and isinstance(val, (int, float)) and val > 1000000000:
                        r_copy[key] = format_timestamp(val)
                writer.writerow(r_copy)
        
        send_status(f"成功导出 {len(records)} 条 {title} 到 '{os.path.abspath(path)}'")
        return path

    except Exception as e:
        import traceback
        error_message = f"导出 {data.get('data_type')} 时发生严重错误: {e}\n{traceback.format_exc()}"
        send_status(error_message)
        return None
    finally:
        if not is_cli:
            asyncio.run_coroutine_threadsafe(send_json(websocket, {"type": "export_complete", "message": f"{data.get('data_type')} 导出任务完成！"}), loop).result()

def run_export_logic(params, status_callback, source="Unknown"):
    """
    核心导出逻辑，被Web UI, Web API 和CLI共用。
    返回一个包含所有生成文件路径的列表。
    """
    global OUTPUT_DIR
    output_location = params.get('location')
    if output_location:
        output_dir_base = os.path.abspath(os.path.expanduser(output_location))
    else:
        output_dir_base = OUTPUT_DIR
    
    exported_files = []
    
    # 混合状态更新函数：同时调用原始回调并记录到文件
    def hybrid_status_update(message):
        status_callback(message) # 调用原始回调 (print 或 websocket send)
        logger.info(f"[{source}] {message}")     # 始终记录到文件

    try:
        os.makedirs(output_dir_base, exist_ok=True)
        run_timestamp = f"_{int(datetime.now().timestamp())}"
        mode, targets, time_range, export_format = params.get("mode"), params.get("targets", []), params.get('time_range', {}), params.get('export_format', 'md')
        
        final_export_format = export_format or CONFIG_MGR.config.get('export_format', 'md')

        config = {
            "start_ts": time_range.get('start'), "end_ts": time_range.get('end'),
            "name_style": CONFIG_MGR.config.get('name_style', 'default'), "name_format": CONFIG_MGR.config.get('name_format', ''),
            "profile_mgr": PROFILE_MGR, "run_timestamp": run_timestamp, 
            "export_config": CONFIG_MGR.config,
            "export_format": final_export_format,
            "custom_fields": params.get('custom_fields'),
            "parse_protobuf_fields": params.get('parse_protobuf_fields', True)
        }
        
        if final_export_format in ['json-custom', 'csv-custom']:
             if not config.get('custom_fields'):
                 hybrid_status_update("错误: 使用 json-custom 或 csv-custom 格式时必须提供 --custom-fields 参数。")
                 return []
             hybrid_status_update(f"即将以自定义格式 ({final_export_format}) 导出 {len(targets)} 个会话...")
             paths = export_custom_format(config, targets, hybrid_status_update, output_dir_base=output_dir_base)
             if paths: exported_files.extend(paths)
        elif mode == 'individual':
            friend_uids = [t['id'] for t in targets if t['type'] == 'friend']
            group_uids = [t['id'] for t in targets if t['type'] == 'group']
            hybrid_status_update(f"即将以独立文件模式导出 {len(friend_uids)} 个私聊和 {len(group_uids)} 个群聊...")
            
            if friend_uids:
                base_friend_dir = os.path.join(output_dir_base, "Individual", "Friends")
                for uid in friend_uids:
                    out_dir = base_friend_dir
                    if params.get('create_group_dirs', False):
                        user_info = PROFILE_MGR.all_users.get(uid, {})
                        if not user_info.get('is_friend'): gname = "_非好友_"
                        else: gname = PROFILE_MGR.friend_groups.get(user_info.get('group_id', -1), f"分组_{user_info.get('group_id', -1)}")
                        safe_gname = re.sub(r'[\\/*?:"<>|]', "_", gname)
                        out_dir = os.path.join(base_friend_dir, safe_gname)
                    file_path = export_one_on_one(config, uid, {'type': 'individual', 'friend_uid': uid}, hybrid_status_update, out_dir=out_dir)
                    if file_path: exported_files.append(file_path)

            for uid in group_uids:
                file_path = export_group_chat(config, uid, {'type': 'group', 'group_uid': uid}, hybrid_status_update, output_dir_base=output_dir_base)
                if file_path: exported_files.append(file_path)
        elif mode == 'timeline':
            friend_uids = [t['id'] for t in targets if t['type'] == 'friend']
            group_uids = [t['id'] for t in targets if t['type'] == 'group']
            
            title = f"包含{len(friend_uids)}个私聊和{len(group_uids)}个群聊的合并时间线"
            friend_details = [{'name': PROFILE_MGR.all_users.get(u, {}).get('remark') or PROFILE_MGR.all_users.get(u, {}).get('nickname', u), 'id': PROFILE_MGR.all_users.get(u, {}).get('qq', u)} for u in friend_uids]
            group_details = [{'name': PROFILE_MGR.chat_groups.get(u, {}).get('name', u), 'id': PROFILE_MGR.chat_groups.get(u, {}).get('uin', u)} for u in group_uids]
                
            scope_info = {'type': 'timeline', 'title': title, 'friend_details': friend_details, 'group_details': group_details}
            file_path = export_timeline(config, friend_uids, group_uids, scope_info, hybrid_status_update, output_dir_base=output_dir_base)
            if file_path: exported_files.append(file_path)
        
        hybrid_status_update("所有导出任务已完成！")
    except Exception as e:
        import traceback
        error_message = f"导出过程中发生严重错误: {e}\n{traceback.format_exc()}"
        hybrid_status_update(error_message)
    
    return exported_files


def run_export_task_ws(loop, websocket, params):
    def send_status(message):
        msg_type = "export_error" if "错误" in message else "export_status"
        asyncio.run_coroutine_threadsafe(send_json(websocket, {"type": msg_type, "message": message}), loop).result()
    
    run_export_logic(params, send_status, source="WebSocket")
    asyncio.run_coroutine_threadsafe(send_json(websocket, {"type": "export_complete", "message": "所有导出任务已完成！"}), loop).result()


def run_raw_export_task(loop, websocket, params, is_cli=False, output_location=None, source="Unknown"):
    """执行原始数据导出, 返回文件路径或None。"""
    def send_status_ws(message):
        asyncio.run_coroutine_threadsafe(send_json(websocket, {"type": "export_status", "message": message}), loop).result()

    def hybrid_status_update(message):
        if is_cli:
            print(message)
        else:
            send_status_ws(message)
        logger.info(f"[{source}] {message}")
    
    send_status = hybrid_status_update
    
    try:
        db_name = params['db_name']
        table = params['table_name']
        cols = params['columns']
        fmt = params['format']
        parse_pb = params.get('parse_protobuf', False)

        db_con = DB_CONNECTIONS.get(db_name)
        if not db_con:
            send_status(f"错误: 数据库 '{db_name}' 未连接或名称错误。可用: {list(DB_CONNECTIONS.keys())}"); return None

        send_status(f"正在从 {db_name} 的 {table} 表中导出 {len(cols)} 列...")
        
        safe_cols = [f'"{c}"' for c in cols]
        query = f"SELECT {', '.join(safe_cols)} FROM '{table}'"
        
        cur = db_con.cursor()
        cur.execute(query)
        rows = cur.fetchall()

        if not rows:
            send_status("查询完成，但未找到任何数据。"); return None

        rows_as_dicts = [dict(zip(cols, row)) for row in rows]
        
        if parse_pb:
            send_status("正在解析Protobuf字段...")
            for i, row_dict in enumerate(rows_as_dicts):
                for key, val in row_dict.items():
                    if isinstance(val, bytes):
                        try:
                            decoded, _ = blackboxprotobuf.decode_message(val)
                            row_dict[key] = decoded
                        except Exception:
                            row_dict[key] = f"[PB解码失败] {base64.b64encode(val).decode('ascii')}"
                if (i+1) % 100 == 0: send_status(f"  已解析 {i+1}/{len(rows_as_dicts)} 行...")

        base_output_dir = output_location or OUTPUT_DIR
        output_dir = os.path.join(base_output_dir, "RawData")
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{db_name.replace('.decrypt.db', '')}_{table}_{int(datetime.now().timestamp())}.{fmt}"
        path = os.path.join(output_dir, filename)

        with open(path, "w", encoding="utf-8-sig", newline='') as f:
            if fmt == 'json':
                count = _write_json(f, rows_as_dicts)
            elif fmt == 'csv':
                count = _write_csv(f, rows_as_dicts, cols)
            else: # txt/md
                for row_dict in rows_as_dicts:
                    f.write(str(row_dict) + '\n')
                count = len(rows_as_dicts)
        
        send_status(f"成功导出 {count} 条记录到 '{os.path.abspath(path)}'")
        return path

    except Exception as e:
        import traceback
        error_message = f"高级导出过程中发生严重错误: {e}\n{traceback.format_exc()}"
        send_status(error_message) # Uses the hybrid logger
        return None
    finally:
        if not is_cli:
            asyncio.run_coroutine_threadsafe(send_json(websocket, {"type": "export_complete", "message": "高级数据导出任务完成！"}), loop).result()

# --- Web API Functions ---

def get_friends_data_for_api():
    """为API准备好友列表数据"""
    friend_groups = {gid: {"name": name, "users": []} for gid, name in PROFILE_MGR.friend_groups.items()}
    friend_groups[-1] = {"name": "默认分组", "users": []}
    for uid in PROFILE_MGR.friend_uids:
        user_info = PROFILE_MGR.all_users.get(uid)
        if user_info:
            gid = user_info.get('group_id', -1)
            if gid not in friend_groups: gid = -1
            friend_groups[gid]['users'].append(user_info)
    if PROFILE_MGR.non_friend_uids:
        friend_groups[-2] = {"name": "[非好友/临时会话]", "users": []}
        for uid in PROFILE_MGR.non_friend_uids:
            if uid in PROFILE_MGR.all_users: friend_groups[-2]['users'].append(PROFILE_MGR.all_users[uid])
    for gid in friend_groups: friend_groups[gid]['users'].sort(key=lambda u: u.get('remark') or u.get('nickname') or u.get('qq'))
    return dict(sorted(friend_groups.items()))

def get_groups_data_for_api():
    """为API准备群组列表数据"""
    groups_for_api = []
    for g in PROFILE_MGR.chat_groups.values():
        groups_for_api.append({
            'id': g['id'],
            'uin': g.get('uin', g['id']),
            'name': g.get('name', f"群聊({g.get('uin', '未知')})"),
            'member_count': g.get('current_members', 'N/A'),
            'max_member_count': g.get('max_members', 'N/A')
        })
    return sorted(groups_for_api, key=lambda g: g['name'])

def get_chat_history_for_api(params):
    """为API获取聊天记录"""
    chat_type, chat_id_str = params.get("type"), params.get("id")
    limit = int(params.get("limit", 200))
    before_ts_str = params.get("before_ts")
    from_ts_str = params.get("from_ts")

    if not all([chat_type, chat_id_str, DB_CON]):
        raise ValueError("缺少 'type' 或 'id' 参数，或数据库未连接。")

    # --- FIX START: Resolve ID and handle timestamps ---
    chat_id = None
    if chat_type == 'friend':
        # 尝试将ID解析为UID (可能是QQ号或UID)
        chat_id = PROFILE_MGR.qq_to_uid_map.get(chat_id_str) or (chat_id_str if chat_id_str in PROFILE_MGR.all_users else None)
        if not chat_id:
            raise ValueError(f"无法找到好友ID: {chat_id_str}")
        table_name, peer_col, group_uid_for_name = TABLE_NAME_C2C, COL_C2C_PEER_UID, None
    else: # group
        # 尝试将ID解析为UID (可能是群号或UID)
        chat_id = PROFILE_MGR.uin_to_uid_map.get(chat_id_str) or (chat_id_str if chat_id_str in PROFILE_MGR.chat_groups else None)
        if not chat_id:
            raise ValueError(f"无法找到群组ID: {chat_id_str}")
        table_name, peer_col, group_uid_for_name = TABLE_NAME_GROUP, COL_GROUP_ID_UID, chat_id

    cur, history, query_params = DB_CON.cursor(), [], [chat_id]
    query = f"SELECT `{COL_TIMESTAMP}`, `{COL_SENDER_UID}`, `{COL_MSG_CONTENT}` FROM {table_name} WHERE `{peer_col}` = ?"

    order_clause = f"ORDER BY `{COL_TIMESTAMP}` DESC"
    limit_clause = f"LIMIT {limit}"

    if before_ts_str:
        try:
            before_ts = int(before_ts_str)
            query += f" AND `{COL_TIMESTAMP}` < ?"
            query_params.append(before_ts)
        except (ValueError, TypeError):
            raise ValueError("无效的 'before_ts' 时间戳格式，应为数字。")
    elif from_ts_str:
        try:
            from_ts = int(from_ts_str)
            query += f" AND `{COL_TIMESTAMP}` >= ?"
            query_params.append(from_ts)
            order_clause = f"ORDER BY `{COL_TIMESTAMP}` ASC"
        except (ValueError, TypeError):
            raise ValueError("无效的 'from_ts' 时间戳格式，应为数字。")
    # --- FIX END ---

    query += f" {order_clause} {limit_clause}"

    cur.execute(query, query_params)
    results = cur.fetchall()
    if order_clause.endswith("DESC"): results.reverse()
    
    for ts, s_uid, content in results:
        parts = decode_message_content(content, ts, PROFILE_MGR, 'default', '', CONFIG_MGR.config)
        if not parts: continue
        is_system_tip = isinstance(parts[0], dict) and parts[0].get('type') == 'interactive_tip'
        if is_system_tip: text_parts = [f"{parts[0]['actor']} {parts[0]['verb']} {parts[0]['target']}{parts[0]['suffix']}"]
        else: text_parts = [str(p) for p in parts if not isinstance(p, dict)]
        final_text = " ".join(text_parts).replace('[%\\n%]', '\n')
        
        history.append({
            "ts": ts, "time": format_timestamp(ts), "s_uid": s_uid, "text": final_text,
            "sender_name": PROFILE_MGR.get_display_name(s_uid, group_uid=group_uid_for_name),
            "is_system_tip": is_system_tip
        })
    return history

def log_and_create_api_response(request, data, status=200, command=None):
    """为API响应生成详细日志并返回 web.json_response。"""
    cmd = command or request.query.get('command', 'unknown')
    
    # 创建响应数据的摘要
    summary = "No data"
    if data and 'status' in data:
        if data['status'] == 'success' and 'data' in data:
            response_data = data['data']
            if isinstance(response_data, list):
                summary = f"Sending list with {len(response_data)} items."
            elif isinstance(response_data, dict):
                summary = f"Sending object with {len(response_data)} keys."
            else:
                summary = "Sending single data item."
        elif data['status'] == 'error':
            summary = f"Sending error: {data.get('message', 'N/A')}"
        else: # 涵盖导出任务的 'completed' 状态
            summary = f"Status: {data['status']}. Log contains {len(data.get('log', []))} messages."

    log_message = f"[API] Response for '{cmd}' to {request.remote}. Status: {status}. Details: {summary}"
    logger.info(log_message)
    if LOG_TO_CONSOLE:
        print(f"[LOG] {log_message}")
        
    return web.json_response(data, status=status)

# --- WebSocket & HTTP Server Main Logic ---
async def ws_handler(websocket):
    connected_clients.add(websocket)
    msg = f"客户端已连接: {websocket.remote_address}"
    print(msg); logger.info(msg)
    try:
        async for message in websocket:
            log_message_for_file = message
            log_message_for_console = message
            
            try:
                # 尝试解析以检查如配置等大数据包
                data = json.loads(message)
                if data.get("command") == "save_config":
                    summary = {k:v for k,v in data.items() if k != 'config'}
                    summary['...config data omitted...'] = True
                    log_message_for_file = json.dumps(summary)
                    log_message_for_console = json.dumps(summary, indent=2)
            except (json.JSONDecodeError, TypeError):
                # 不是json或不是dict，按原样记录
                pass

            logger.debug(f"[WebSocket] RECV <- {log_message_for_file}")
            if LOG_TO_CONSOLE:
                print(f"[LOG] RECV <- {log_message_for_console}")

            try:
                data = json.loads(message)
                command = data.get("command")
                if command == "get_initial_data": await handle_get_initial_data(websocket)
                elif command == "get_db_fields": await handle_get_db_fields(websocket)
                elif command == "get_db_info": await handle_get_db_info(websocket)
                elif command == "get_chat_history": await handle_get_chat_history(websocket, data)
                elif command == "save_config": await handle_save_config(websocket, data)
                elif command == "start_export": await handle_start_export(websocket, data)
                elif command == "export_extra_group_data": await handle_export_extra_group_data(websocket, data)
                elif command == "start_raw_export": await handle_start_raw_export(websocket, data)
            except Exception as e:
                import traceback
                error_msg = f"处理命令 '{data.get('command')}' 时出错: {e}\n{traceback.format_exc()}"
                print(error_msg); logger.error(error_msg)
                await send_json(websocket, {"type": "error", "message": error_msg})
    except websockets.exceptions.ConnectionClosed:
        msg = f"客户端断开连接: {websocket.remote_address}"
        print(msg); logger.info(msg)
    finally:
        connected_clients.remove(websocket)

async def handle_api_request(request):
    """处理所有 /api GET 请求"""
    params = request.query
    command = params.get('command')
    # 首先记录接收到的请求
    logger.info(f"[API] Received command: '{command}' from {request.remote}. Params: {dict(params)}")
    if LOG_TO_CONSOLE:
        print(f"[LOG] [API] Received command: '{command}' from {request.remote}. Params: {dict(params)}")

    try:
        if not command:
            return log_and_create_api_response(request, 
                {'status': 'error', 'message': 'Missing "command" parameter.'}, 
                status=400, command='invalid_request')

        # 分发命令
        if command == 'list_friends':
            data = get_friends_data_for_api()
            return log_and_create_api_response(request, {'status': 'success', 'data': data}, command=command)
        
        elif command == 'list_groups':
            data = get_groups_data_for_api()
            return log_and_create_api_response(request, {'status': 'success', 'data': data}, command=command)

        elif command == 'list_schema':
            schema_data = {name: _scan_db_schema(con) for name, con in DB_CONNECTIONS.items() if con}
            return log_and_create_api_response(request, {'status': 'success', 'data': schema_data}, command=command)

        elif command == 'list_fields':
            return log_and_create_api_response(request, {'status': 'success', 'data': DB_FIELDS_CACHE}, command=command)

        elif command == 'get_chat_history':
            history = get_chat_history_for_api(params)
            return log_and_create_api_response(request, {'status': 'success', 'data': history}, command=command)
        
        elif command in ['export', 'export_extra', 'export_raw']:
            log_messages = []
            status_callback = lambda msg: log_messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
            loop = asyncio.get_running_loop()
            
            exported_files = []
            if command == 'export':
                friend_uids = _resolve_target_ids(params.get('friends'), 'friend') if params.get('friends') else []
                group_uids = _resolve_target_ids(params.get('groups'), 'group') if params.get('groups') else []
                targets = [{'type': 'friend', 'id': uid} for uid in friend_uids] + \
                          [{'type': 'group', 'id': uid} for uid in group_uids]
                start_ts = _parse_flexible_timestamp(params.get('start'), is_end_time=False)
                end_ts = _parse_flexible_timestamp(params.get('end'), is_end_time=True)
                export_params = {
                    'mode': params.get('mode', 'individual'), 'targets': targets,
                    'time_range': {'start': start_ts, 'end': end_ts},
                    'export_format': params.get('format', 'md'),
                    'custom_fields': params.get('custom_fields', '').split(',') if params.get('custom_fields') else None,
                    'create_group_dirs': params.get('group_dirs', 'false').lower() == 'true',
                    'location': params.get('location')
                }
                exported_files = await loop.run_in_executor(None, run_export_logic, export_params, status_callback, "API")
            
            elif command == 'export_extra':
                group_uid = _resolve_target_ids(params.get('group'), 'group')
                if not group_uid: raise ValueError(f"无法找到群 '{params.get('group')}'")
                extra_params = {"group_id": group_uid[0], "data_type": params.get('type')}
                file_path = await loop.run_in_executor(None, run_export_extra_task, None, None, extra_params, params.get('location'))
                if file_path: exported_files.append(file_path)

            elif command == 'export_raw':
                raw_params = {
                    'db_name': params.get('db'), 'table_name': params.get('table'),
                    'columns': params.get('columns', '').split(','),
                    'format': params.get('format', 'json'),
                    'parse_protobuf': params.get('parse_pb', 'false').lower() == 'true'
                }
                file_path = await loop.run_in_executor(None, run_raw_export_task, None, None, raw_params, True, params.get('location'), "API")
                if file_path: exported_files.append(file_path)

            # 每次导出请求都重新读取配置
            api_action = CONFIG_MGR.load_config().get('api_export_action', 'save')
            logger.info(f"[API] Export action determined as: '{api_action}'")
            
            if api_action == 'download':
                if not exported_files:
                    return log_and_create_api_response(request, 
                        {'status': 'completed', 'message': 'No files were generated for download.', 'log': log_messages}, 
                        command=command)
                if len(exported_files) > 1:
                    return log_and_create_api_response(request, 
                        {'status': 'error', 'message': 'API download mode only supports exporting a single file at a time. Multiple files were generated.', 'log': log_messages}, 
                        status=400, command=command)
                
                file_path = exported_files[0]
                if not os.path.exists(file_path):
                     return log_and_create_api_response(request, 
                         {'status': 'error', 'message': f'Generated file not found at path: {file_path}', 'log': log_messages}, 
                         status=500, command=command)
                
                try:
                    with open(file_path, 'rb') as f: content = f.read()
                    os.remove(file_path)
                    
                    log_message = f"[API] Response for '{command}' to {request.remote}. Status: 200. Details: Sending 1 file ('{os.path.basename(file_path)}') for download."
                    logger.info(log_message)
                    if LOG_TO_CONSOLE:
                        print(f"[LOG] {log_message}")

                    logger.info(f"[API] Download mode: Temporary export file {file_path} has been deleted.")
                    
                    headers = {'Content-Disposition': f'attachment; filename="{os.path.basename(file_path)}"'}
                    return web.Response(body=content, headers=headers)
                except Exception as e:
                    logger.error(f"[API] Error processing file for download: {e}")
                    return log_and_create_api_response(request, 
                        {'status': 'error', 'message': f'Error processing file for download: {e}', 'log': log_messages}, 
                        status=500, command=command)
            else: # 'save' action
                return log_and_create_api_response(request, 
                    {'status': 'completed', 'log': log_messages}, command=command)
        else:
            return log_and_create_api_response(request, 
                {'status': 'error', 'message': f'Unknown command: {command}'}, 
                status=400, command=command)

    except Exception as e:
        import traceback
        error_msg = f"API Error: {e}\n{traceback.format_exc()}"
        print(error_msg); logger.error(error_msg)
        return log_and_create_api_response(request, 
            {'status': 'error', 'message': 'An internal server error occurred.', 'details': str(e)}, 
            status=500, command=command)

async def handle_http_get_root(request):
    """HTTP GET handler to serve the main index.html file."""
    index_path = get_resource_path('index.html')
    try: return web.FileResponse(index_path)
    except FileNotFoundError: return web.Response(text="<h1>错误 404</h1><p>控制面板文件 (index.html) 未找到。</p>", status=404, content_type='text/html')

async def handle_http_get_ark_invest(request):
    """HTTP GET handler to serve the ark-invest.html file."""
    ark_path = get_resource_path('ark-invest.html')
    try: return web.FileResponse(ark_path)
    except FileNotFoundError: return web.Response(text="<h1>错误 404</h1><p>分析器文件 (ark-invest.html) 未找到。</p>", status=404, content_type='text/html')

async def handle_http_get_api_docs(request):
    """HTTP GET handler to serve the api_docs.html file."""
    api_docs_path = get_resource_path('api_docs.html')
    try: return web.FileResponse(api_docs_path)
    except FileNotFoundError: return web.Response(text="<h1>错误 404</h1><p>API文档文件 (api_docs.html) 未找到。</p>", status=404, content_type='text/html')

async def main_server(host, ws_port, http_port, no_browser=False):
    http_app = web.Application()
    
    # 添加核心路由
    http_app.router.add_get('/', handle_http_get_root)
    http_app.router.add_get('/ark-invest', handle_http_get_ark_invest)
    http_app.router.add_get('/api-docs', handle_http_get_api_docs)
    http_app.router.add_get('/api', handle_api_request)
    
    # 添加静态文件目录路由
    lib_path = get_resource_path(_LIB_DIR_NAME)
    http_app.router.add_static(f'/{_LIB_DIR_NAME}', lib_path, show_index=False)
    webfonts_path = get_resource_path(os.path.join(_LIB_DIR_NAME, 'webfonts'))
    if os.path.exists(webfonts_path):
        http_app.router.add_static('/webfonts', webfonts_path, show_index=False)

    runner = web.AppRunner(http_app)
    await runner.setup()
    http_site = web.TCPSite(runner, host, http_port)
    
    await http_site.start()
    ws_server = await websockets.serve(ws_handler, host, ws_port)
    
    control_panel_url = f"http://{host}:{http_port}"
    api_docs_url = f"http://{host}:{http_port}/api-docs"
    if not no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(control_panel_url)).start()
    
    print("-" * 50)
    print("ARK-1 System Loading...")
    print(f"WebSocket服务器已启动, 监听: ws://{host}:{ws_port}")
    print(f"HTTP服务器已启动, 请在浏览器中打开: {control_panel_url}")
    print(f"Web API 文档与测试器: {api_docs_url}")
    print("\n请将3个数据库文件放在本程序所在的文件夹内。")
    print("导出文件将保存在数据库所在的文件夹下的 output 子目录中。")
    print("要关闭程序, 请直接关闭此命令行窗口。")
    print("-" * 50)
    logger.info("Web UI 服务器启动成功。")

    await asyncio.Future()

def setup_logging(use_debug_log):
    """配置日志记录器，日志级别由 use_debug_log 控制，并存储在 'log' 文件夹中。"""
    global logger
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    log_dir = os.path.join(script_dir, 'log')
    os.makedirs(log_dir, exist_ok=True)

    log_filename = f"arklog-{time.strftime('%Y%m%d-%H%M%S')}.log"
    log_filepath = os.path.join(log_dir, log_filename)

    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    if use_debug_log:
        file_handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)
    
    logger.addHandler(file_handler)
    
    logger.info(f"日志系统已启动。日志将保存到: {log_filepath}")
    if use_debug_log:
        logger.info("调试日志模式已启用。")

def perform_decryption(workdir, force_overwrite=False):
    """
    使用外部的 sqlcipher.exe 和 sqlite3.exe 通过直接管道方式解密数据库。
    此函数会处理覆盖逻辑、错误容忍和最终验证。
    新版本通过 Popen 手动管理进程管道，并设置 'cwd' 参数来解决非ASCII路径问题。
    成功或部分成功返回 True，发生致命错误返回 False。
    """
    config_path = os.path.join(workdir, 'decrypt.config')
    sqlcipher_path = os.path.join(workdir, 'sqlcipher.exe')
    sqlite3_path = os.path.join(workdir, 'sqlite3.exe')

    if not os.path.exists(sqlcipher_path) or not os.path.exists(sqlite3_path):
        msg = f"错误: 缺少 'sqlcipher.exe' 或 'sqlite3.exe'。请确保它们都在工作目录中: {workdir}"
        print(msg)
        logger.error(msg)
        return False

    if not os.path.exists(config_path):
        msg = f"错误: 未找到 'decrypt.config' 文件，无法获取解密参数。"
        print(msg)
        logger.error(msg)
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            # 将所有PRAGMA命令合并为单行、分号分隔的字符串
            pragma_commands = "; ".join(line.strip() for line in f if line.strip())
    except Exception as e:
        msg = f"错误: 读取 'decrypt.config' 文件失败: {e}"
        print(msg)
        logger.error(msg)
        return False

    db_files_to_decrypt = [
        "nt_msg.clean.db",
        "profile_info.clean.db",
        "group_info.clean.db"
    ]
    
    overall_success = True

    for encrypted_db_name in db_files_to_decrypt:
        encrypted_path = os.path.join(workdir, encrypted_db_name)
        if not os.path.exists(encrypted_path):
            continue # 如果源数据库不存在则跳过

        decrypted_db_name = encrypted_db_name.replace('.clean.db', '.decrypt.db')
        decrypted_path = os.path.join(workdir, decrypted_db_name)

        if os.path.exists(decrypted_path) and not force_overwrite:
            overwrite = input(f"检测到已存在的解密后数据库 '{decrypted_db_name}'。是否要覆盖？ (y/N): ").strip().lower()
            if overwrite != 'y':
                print(f"跳过解密 '{encrypted_db_name}'，将使用现有文件。")
                logger.info(f"Skipping decryption for {encrypted_db_name}, using existing file.")
                continue
        
        if os.path.exists(decrypted_path):
             print(f"检测到已存在的 '{decrypted_db_name}'，将{'强制' if force_overwrite else ''}覆盖。")
             try:
                 os.remove(decrypted_path)
             except OSError as e:
                 msg = f"错误: 无法删除旧文件 '{decrypted_path}': {e}"
                 print(msg); logger.error(msg)
                 overall_success = False
                 continue

        print(f"正在使用管道解密 '{encrypted_db_name}'...")
        logger.info(f"Starting pipe decryption for {encrypted_db_name}...")
        
        # 修正：不再传递完整路径，而是使用相对文件名，并设置工作目录 (cwd)
        sqlcipher_args = ["sqlcipher.exe", encrypted_db_name, pragma_commands + ";", ".d"]
        sqlite3_args = ["sqlite3.exe", decrypted_db_name]

        proc1 = None
        proc2 = None
        try:
            # 在Windows下隐藏弹出的命令行窗口
            creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

            # 启动第一个进程 (sqlcipher)，使用二进制管道并设置工作目录
            proc1 = subprocess.Popen(
                sqlcipher_args,
                cwd=workdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )

            # 启动第二个进程 (sqlite3)，使用二进制管道并设置工作目录
            proc2 = subprocess.Popen(
                sqlite3_args,
                cwd=workdir,
                stdin=proc1.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )

            # 关键步骤: 允许proc1在proc2关闭管道时接收到信号并终止
            proc1.stdout.close()

            # 等待第二个进程完成，并获取其二进制错误输出
            _, stderr2_bytes = proc2.communicate()
            
            # proc2结束后, proc1也应该结束了。我们等待它并获取其错误输出。
            stderr1_bytes = proc1.stderr.read()
            proc1.wait()
            
            # 将二进制错误输出解码为字符串
            stderr1 = stderr1_bytes.decode('utf-8', 'replace') if stderr1_bytes else ""
            stderr2 = stderr2_bytes.decode('utf-8', 'replace') if stderr2_bytes else ""
            full_stderr = stderr1 + stderr2

            if full_stderr and "PRAGMA cipher is no longer supported" not in full_stderr:
                print(f"解密 '{encrypted_db_name}' 时出现错误/警告信息:")
                # 在控制台打印错误以帮助调试
                print(full_stderr.strip())
                logger.warning(f"Stderr during decryption of {encrypted_db_name}:\n{full_stderr}")

            if proc1.returncode != 0:
                print(f"警告: sqlcipher.exe 执行时返回了错误 (代码: {proc1.returncode})。")
                logger.warning(f"sqlcipher.exe for {encrypted_db_name} exited with code {proc1.returncode}.")

            if proc2.returncode != 0:
                print(f"警告: sqlite3.exe 执行时返回了错误 (代码: {proc2.returncode})。将继续检查输出文件。")
                logger.warning(f"sqlite3.exe for {encrypted_db_name} exited with code {proc2.returncode}.")

            # 最终验证：检查文件是否成功生成且不为空
            if os.path.exists(decrypted_path) and os.path.getsize(decrypted_path) > 0:
                print(f"成功创建解密后的数据库: '{decrypted_db_name}'")
                logger.info(f"Successfully created decrypted database: {decrypted_db_name}")
            else:
                msg = f"错误: 解密 '{encrypted_db_name}' 失败。输出文件未生成或为空。"
                print(msg)
                logger.error(msg)
                overall_success = False

        except FileNotFoundError as e:
            msg = f"致命错误: 找不到执行文件: {e}。请确保 sqlcipher.exe 和 sqlite3.exe 都在工作目录中。"
            print(msg); logger.critical(msg)
            return False # 这是致命错误
        except Exception as e:
            msg = f"解密过程中发生未知错误: {e}"
            print(msg); logger.critical(msg, exc_info=True)
            return False # 这也是致命错误
        finally:
            # 确保子进程被终止，以防万一
            if proc1 and proc1.poll() is None: proc1.kill()
            if proc2 and proc2.poll() is None: proc2.kill()
    
    return overall_success



def manage_decryption_on_startup(workdir):
    """
    在无特定参数启动时，检查数据库状态并在需要时提示用户。
    """
    has_clean_db = any(os.path.exists(os.path.join(workdir, f)) for f in ["nt_msg.clean.db", "profile_info.clean.db"])
    if not has_clean_db:
        return True # 没有需要解密的文件，正常进行

    has_decrypt_db = any(os.path.exists(os.path.join(workdir, f)) for f in [_DB_FILENAME, _PROFILE_DB_FILENAME, _GROUP_INFO_DB_FILENAME])

    choice = ''
    if has_decrypt_db:
        print("\n" + "="*25 + " 数据库源选择 " + "="*25)
        print("检测到两种类型的数据库文件:")
        print("  1. 使用已存在的解密后数据库 (.decrypt.db)")
        print("  2. 从原始加密数据库 (.clean.db) 重新解密")
        print("     (需要工作目录中存在 'sqlcipher.exe', 'sqlite3.exe' 和 'decrypt.config')")
        print("="*68)
        while choice not in ['1', '2']:
            choice = input("请选择要使用的数据库源 [默认: 1]: ") or '1'
    else:
        print("\n未找到已解密的数据库, 将自动从原始加密数据库 (.clean.db) 进行解密。")
        choice = '2'

    if choice == '1':
        print("--> 已选择: 使用已存在的解密后数据库。\n")
        return True
    elif choice == '2':
        print("--> 已选择: 从原始加密数据库进行解密。\n")
        return perform_decryption(workdir, force_overwrite=False)
    
    return False

def setup_environment(workdir, use_debug_log):
    global PROFILE_MGR, CONFIG_MGR, DB_CON, GROUP_INFO_DB_CON, PROFILE_DB_CON, DB_CONNECTIONS, WORK_DIR, OUTPUT_DIR, DB_PATH, PROFILE_DB_PATH, GROUP_INFO_DB_PATH, CONFIG_PATH, TEMPLATE_DIR_PATH, NON_FRIENDS_CACHE_PATH, DB_FIELDS_CACHE, GROUP_UID_TO_UIN_MAP, GROUP_UIN_TO_UID_MAP
    
    if getattr(sys, 'frozen', False):
        WORK_DIR = os.path.dirname(sys.executable)
        script_dir = WORK_DIR
    else:
        WORK_DIR = workdir
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    DB_PATH = os.path.join(WORK_DIR, _DB_FILENAME)
    PROFILE_DB_PATH = os.path.join(WORK_DIR, _PROFILE_DB_FILENAME)
    GROUP_INFO_DB_PATH = os.path.join(WORK_DIR, _GROUP_INFO_DB_FILENAME)
    CONFIG_PATH = get_resource_path(_CONFIG_FILENAME)
    TEMPLATE_DIR_PATH = get_resource_path(_TEMPLATE_DIR_NAME)
    NON_FRIENDS_CACHE_PATH = os.path.join(script_dir, _NON_FRIENDS_CACHE_FILENAME)
    
    print(f"程序运行目录: {os.path.abspath(script_dir)}")
    logger.info(f"程序运行目录: {os.path.abspath(script_dir)}")
    print(f"数据工作目录: {os.path.abspath(WORK_DIR)}")
    logger.info(f"数据工作目录: {os.path.abspath(WORK_DIR)}")

    if not all(os.path.exists(p) for p in [DB_PATH, PROFILE_DB_PATH]):
        err_msg = f"\n错误：请确保 '{_DB_FILENAME}' 和 '{_PROFILE_DB_FILENAME}' 文件在以下目录中: \n{os.path.abspath(WORK_DIR)}"
        print(err_msg)
        logger.critical(err_msg.strip())
        if getattr(sys, 'frozen', False):
            print("\n提示: 您需要将3个数据库文件和生成的exe文件放在同一个文件夹下再运行。")
        return False
    
    try:
        # V6.7 FIX: Set text_factory after connection for compatibility with older Python versions.
        text_factory = lambda b: b.decode('utf-8', 'ignore')

        DB_CON = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
        DB_CON.text_factory = text_factory
        DB_CONNECTIONS[_DB_FILENAME] = DB_CON

        PROFILE_DB_CON = sqlite3.connect(f"file:{PROFILE_DB_PATH}?mode=ro", uri=True, check_same_thread=False)
        PROFILE_DB_CON.text_factory = text_factory
        DB_CONNECTIONS[_PROFILE_DB_FILENAME] = PROFILE_DB_CON

        if os.path.exists(GROUP_INFO_DB_PATH):
            GROUP_INFO_DB_CON = sqlite3.connect(f"file:{GROUP_INFO_DB_PATH}?mode=ro", uri=True, check_same_thread=False)
            GROUP_INFO_DB_CON.text_factory = text_factory
            DB_CONNECTIONS[_GROUP_INFO_DB_FILENAME] = GROUP_INFO_DB_CON
        else:
            msg = f"提示: 未在工作目录中找到 '{_GROUP_INFO_DB_FILENAME}'，部分群组功能将不可用。"
            print(msg); logger.info(msg)
    except sqlite3.Error as e: 
        err_msg = f"数据库连接失败: {e}"
        print(err_msg); logger.critical(err_msg)
        return False

    try:
        cur = DB_CON.cursor()
        cur.execute(f'SELECT DISTINCT "{COL_GROUP_ID_UID}", "{COL_GROUP_ID_UIN}" FROM {TABLE_NAME_GROUP} WHERE "{COL_GROUP_ID_UID}" IS NOT NULL AND "{COL_GROUP_ID_UIN}" IS NOT NULL')
        for uid, uin in cur.fetchall():
            GROUP_UID_TO_UIN_MAP[uid] = uin
            GROUP_UIN_TO_UID_MAP[uin] = uid
        msg = f"成功建立 {len(GROUP_UID_TO_UIN_MAP)} 个群聊的ID映射。"
        print(msg); logger.info(msg)
    except Exception as e: 
        warn_msg = f"警告: 建立群聊ID映射失败: {e}"
        print(warn_msg); logger.warning(warn_msg)

    PROFILE_MGR = ProfileManager(PROFILE_DB_PATH, GROUP_INFO_DB_PATH if GROUP_INFO_DB_CON else None)
    CONFIG_MGR = ConfigManager(CONFIG_PATH)
    PROFILE_MGR.load_data()
    DB_FIELDS_CACHE = get_db_fields()
    msg = f"成功扫描到 {len(DB_FIELDS_CACHE)} 个可导出字段。"
    print(msg); logger.info(msg)
    PROFILE_MGR.load_non_friends(CONFIG_MGR)
    OUTPUT_DIR = os.path.join(WORK_DIR, f"{PROFILE_MGR.my_qq}_output")
    print(f"默认输出目录: {os.path.abspath(OUTPUT_DIR)}")
    logger.info(f"默认输出目录: {os.path.abspath(OUTPUT_DIR)}")
    return True

# --- Command Line Interface (CLI) ---

def _resolve_target_ids(id_str, target_type):
    """将用户输入的ID字符串（QQ号/群号/UID，逗号分隔）解析为UID列表。"""
    if not id_str: return []
    
    all_friends = {**{u['qq']: u['uid'] for u in PROFILE_MGR.all_users.values() if 'qq' in u and u['qq']},
                   **{u['uid']: u['uid'] for u in PROFILE_MGR.all_users.values()}}
    all_groups = {**{g['uin']: g['id'] for g in PROFILE_MGR.chat_groups.values() if 'uin' in g and g['uin']},
                  **{g['id']: g['id'] for g in PROFILE_MGR.chat_groups.values()}}

    if id_str.lower() == 'all':
        if target_type == 'friend':
            return list(PROFILE_MGR.friend_uids)
        elif target_type == 'group':
            return list(PROFILE_MGR.chat_groups.keys())
        return []

    resolved_uids = set()
    for item_id in id_str.split(','):
        item_id = item_id.strip()
        found_uid = None
        if target_type == 'friend':
            found_uid = all_friends.get(item_id) or PROFILE_MGR.qq_to_uid_map.get(item_id)
        elif target_type == 'group':
            found_uid = all_groups.get(item_id) or PROFILE_MGR.uin_to_uid_map.get(item_id)
        
        if found_uid:
            resolved_uids.add(found_uid)
        else:
            msg = f"警告：无法识别的ID '{item_id}'，将被忽略。"
            print(msg); logger.warning(msg)
            
    return list(resolved_uids)

def run_list_friends():
    logger.info("[CLI] Executing 'list friends' command.")
    print("\n--- 好友列表 ---")
    for group_id, group_name in {**PROFILE_MGR.friend_groups, -1:"默认分组", -2:"非好友/临时会话"}.items():
        if group_id == -2: 
            users_in_group = [PROFILE_MGR.all_users[uid] for uid in PROFILE_MGR.non_friend_uids if uid in PROFILE_MGR.all_users]
        else:
            users_in_group = [u for u in PROFILE_MGR.all_users.values() if u.get('group_id') == group_id and u['is_friend']]

        if users_in_group:
            print(f"\n--- {group_name} ---")
            for user in sorted(users_in_group, key=lambda x: x.get('remark') or x.get('nickname')):
                remark = f" (备注: {user['remark']})" if user['remark'] else ""
                print(f"  {user.get('nickname', '[无昵称]')}{remark}\n    QQ: {user.get('qq', 'N/A')} | UID: {user['uid']}")
                
def run_list_groups():
    logger.info("[CLI] Executing 'list groups' command.")
    print("\n--- 群聊列表 ---")
    for group in sorted(PROFILE_MGR.chat_groups.values(), key=lambda x: x.get('name')):
        print(f"  {group['name']} (成员: {group.get('current_members', 'N/A')})\n    群号: {group.get('uin', 'N/A')} | UID: {group['id']}")

def run_list_db_schema():
    logger.info("[CLI] Executing 'list schema' command.")
    print("\n--- 数据库结构 ---")
    for db_name, db_con in DB_CONNECTIONS.items():
        if db_con:
            print(f"\n--- 数据库: {db_name} ---")
            schema = _scan_db_schema(db_con)
            for table in schema:
                print(f"  表: {table['name']}")
                for col in table['columns']:
                    desc = f" ({col['desc']})" if col['desc'] else ""
                    print(f"    - {col['name']}{desc}")

def run_list_fields(args):
    filter_arg = args[0].lower() if args else 'all'
    logger.info(f"[CLI] Executing 'list fields' command with filter: {filter_arg}.")
    print("\n--- 可导出字段列表 ---")
    
    categories = {
        "通用消息": {"desc": "适用于私聊和群聊的消息核心字段 (来自 nt_msg.db)", "fields": {}},
        "个人资料": {"desc": "适用于私聊和群聊发送者的个人信息 (来自 profile_info.db)", "fields": {}},
        "群成员": {"desc": "仅适用于群聊中发送者的成员信息 (来自 group_info.db)", "fields": {}},
        "群信息": {"desc": "群聊的通用信息 (来自 group_info.db)", "fields": {}},
        "群通知": {"desc": "群通知/系统消息相关字段 (来自 group_info.db)", "fields": {}},
        "群精华": {"desc": "群精华消息相关字段 (来自 group_info.db)", "fields": {}},
    }

    # Categorize fields
    for code, desc in FIELD_DESCRIPTIONS.items():
        key = None
        if code.startswith('4'): key = "通用消息"
        elif code in ["1000", "1002", "20002", "64003", "64007", "64008", "64009", "64010", "64016", "64023", "64035", "64029"]: key = "群成员"
        elif code.startswith('61'): key = "群通知"
        elif code.startswith('675'): key = "群精华"
        elif code.startswith('60'): key = "群信息"
        elif code.startswith('1') or code.startswith('2') or code.startswith('3'): key = "个人资料"
        
        if key:
            categories[key]["fields"][code] = desc

    display_categories = []
    if filter_arg == 'all':
        display_categories = categories.keys()
    elif filter_arg == 'c2c':
        display_categories = ["通用消息", "个人资料"]
    elif filter_arg == 'group':
        display_categories = ["通用消息", "个人资料", "群成员", "群信息", "群通知", "群精华"]
    else:
        print(f"错误: 未知的筛选器 '{filter_arg}'. 可用: all, c2c, group")
        return

    for cat_name in display_categories:
        category = categories[cat_name]
        print(f"\n--- {cat_name}: {category['desc']} ---")
        if not category['fields']:
            print("  (无可用字段)")
            continue
        sorted_fields = sorted(category['fields'].items(), key=lambda item: int(item[0]))
        for code, desc in sorted_fields:
            print(f"  {code:<8} - {desc}")
    
    print("\n提示: 在使用 --custom-fields 时，请使用英文逗号分隔以上字段代码。")

def run_direct_export_cli(args):
    logger.info(f"[CLI] Executing direct export. Mode: {args.mode}, Format: {args.format}, Friends: {args.friends}, Groups: {args.groups}")
    print("\n--- 开始直接导出 ---")
    friend_uids = _resolve_target_ids(args.friends, 'friend') if args.friends else []
    group_uids = _resolve_target_ids(args.groups, 'group') if args.groups else []
    
    if not friend_uids and not group_uids:
        print("错误：未提供有效的好友或群聊ID。请使用 --friends 或 --groups 参数。")
        return

    targets = [{'type': 'friend', 'id': uid} for uid in friend_uids] + \
              [{'type': 'group', 'id': uid} for uid in group_uids]

    start_ts = _parse_flexible_timestamp(args.start, is_end_time=False)
    end_ts = _parse_flexible_timestamp(args.end, is_end_time=True)

    if (args.start and start_ts is None) or (args.end and end_ts is None):
        print("导出中止，因为提供了无效的时间格式。")
        return
    
    custom_fields = args.custom_fields.split(',') if args.custom_fields else None
    
    params = {
        'mode': args.mode,
        'targets': targets,
        'time_range': {'start': start_ts, 'end': end_ts},
        'export_format': args.format,
        'custom_fields': custom_fields,
        'create_group_dirs': args.group_dirs,
        'location': args.location
    }
    run_export_logic(params, print, source="CLI")

def run_export_group_extra_cli(args):
    logger.info(f"[CLI] Executing extra group data export. Group: {args.group}, Type: {args.type}")
    print("\n--- 开始导出群组附加数据 ---")
    group_uid = _resolve_target_ids(args.group, 'group')
    if not group_uid:
        print(f"错误：无法找到群 '{args.group}'。"); return
    
    run_export_extra_task(None, None, {"group_id": group_uid[0], "data_type": args.type}, output_location=args.location)

def run_raw_export_cli(args):
    logger.info(f"[CLI] Executing raw data export. DB: {args.db}, Table: {args.table}")
    print("\n--- 开始原始数据导出 ---")
    params = {
        'db_name': args.db,
        'table_name': args.table,
        'columns': args.columns.split(','),
        'format': args.raw_format,
        'parse_protobuf': args.parse_pb
    }
    run_raw_export_task(None, None, params, is_cli=True, output_location=args.location, source="CLI")


class CommandLineInterface:
    def __init__(self):
        self.prompt = "ARK-1 CLI> "

    def run(self):
        print("\n欢迎使用 ARK-1 交互式命令行界面。输入 'help' 查看可用命令。")
        while True:
            try:
                line = input(self.prompt)
                if not line: continue
                parts = shlex.split(line)
                command = parts[0].lower()
                args = parts[1:]
                
                cmd_func = getattr(self, f"do_{command}", None)
                if cmd_func:
                    logger.info(f"[CLI-Interactive] Command: {command}, Args: {' '.join(args)}")
                    cmd_func(args)
                else:
                    print(f"未知命令: '{command}'. 输入 'help' 获取帮助。")
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
            except Exception as e:
                print(f"处理命令时发生错误: {e}")
    
    def do_help(self, args):
        print("\n--- ARK-1 CLI 帮助 ---")
        help_text = {
            'help': "显示此帮助信息。",
            'list': "列出好友/群聊/数据库结构/可导出字段。\n  用法: list <friends|groups|schema|fields> [filter]\n"
                    "  [filter] for fields: c2c | group",
            'decrypt': "手动执行数据库解密流程。\n  用法: decrypt [--overwrite]",
            'export': "执行标准聊天记录导出。\n"
                      "  用法: export <mode> --friends <IDs> --groups <IDs> [--format <fmt>] [--group-dirs] [--location <path>]\n"
                      "  [--custom-fields <f1,f2,...>] [--start <time>] [--end <time>] [...]\n"
                      "  <IDs>: QQ号/群号或UID, 逗号分隔, 或 'all'\n"
                      "  <fmt>: md | txt | html | json-custom | csv-custom\n"
                      "  --start/--end: 'YYYY-MM-DD' 或 \"YYYY-MM-DD HH:MM:SS\"\n"
                      "  --custom-fields <f1,f2,...>: 自定义格式需指定字段",
            'export_extra': "导出群附加数据 (如成员列表)。\n"
                            "  用法: export_extra --group <ID> --type <type> [--location <path>]\n"
                            "  <type>: members | essences | notifications | bulletins",
            'export_raw': "从数据库原始导出。\n"
                          "  用法: export_raw --db <db> --table <table> --columns <c1,c2> [--format <fmt>] [--location <path>]\n  [--raw-format] [--parse-pb]\n"
                          "  <db>: " + " | ".join(DB_CONNECTIONS.keys()),
            'config': "查看或修改配置。\n  用法: config <key> [new_value]",
            'set': "设定工作目录或导出目录。\n  用法: set <workdir|outputdir> <路径>",
            'webui': "在当前CLI模式下，启动Web UI服务器。",
            'exit': "退出命令行界面。"
        }
        for cmd, desc in help_text.items():
            print(f"\n{cmd}:\n{textwrap.indent(desc, '  ')}")
        print("\n----------------------")
            
    def do_list(self, args):
        if not args:
            print("错误：请指定要列出的类型: 'friends', 'groups', 'schema', 或 'fields'."); return
        list_type = args[0].lower()
        if list_type == 'friends': run_list_friends()
        elif list_type == 'groups': run_list_groups()
        elif list_type == 'schema': run_list_db_schema()
        elif list_type == 'fields': run_list_fields(args[1:])
        else: print(f"错误: 未知的列表类型 '{list_type}'.")

    def do_decrypt(self, args):
        """手动触发数据库解密流程。"""
        force_overwrite = '--overwrite' in args
        print("正在手动执行数据库解密...")
        if perform_decryption(WORK_DIR, force_overwrite=force_overwrite):
            print("解密流程完成。您可能需要重启程序或使用 'set workdir' 重新加载数据。")
        else:
            print("解密流程失败。")
    
    def _parse_and_run(self, args, runner_func, prog_name):
        try:
            if prog_name == 'export':
                parser = argparse.ArgumentParser(prog=prog_name, description='导出命令')
                parser.add_argument('mode', choices=['individual', 'timeline'])
                parser.add_argument('--friends', type=str)
                parser.add_argument('--groups', type=str)
                parser.add_argument('--format', type=str, default='md')
                parser.add_argument('--start', type=str)
                parser.add_argument('--end', type=str)
                parser.add_argument('--custom-fields', type=str)
                parser.add_argument('--group-dirs', action='store_true')
                parser.add_argument('--location', type=str)
            elif prog_name == 'export_extra':
                parser = argparse.ArgumentParser(prog=prog_name)
                parser.add_argument('--group', required=True)
                parser.add_argument('--type', required=True, choices=['members','essences','notifications','bulletins'])
                parser.add_argument('--location', type=str)
            elif prog_name == 'export_raw':
                parser = argparse.ArgumentParser(prog=prog_name)
                parser.add_argument('--db', required=True)
                parser.add_argument('--table', required=True)
                parser.add_argument('--columns', required=True)
                parser.add_argument('--raw-format', default='json', choices=['json', 'csv'])
                parser.add_argument('--parse-pb', action='store_true')
                parser.add_argument('--location', type=str)
            
            parsed_args = parser.parse_args(args)
            runner_func(parsed_args)
        except SystemExit:
            print(f"{prog_name} 命令参数错误，请检查。")
        except Exception as e:
            import traceback
            print(f"执行 {prog_name} 时发生错误: {e}\n{traceback.format_exc()}")

    def do_export(self, args): self._parse_and_run(args, run_direct_export_cli, 'export')
    def do_export_extra(self, args): self._parse_and_run(args, run_export_group_extra_cli, 'export_extra')
    def do_export_raw(self, args): self._parse_and_run(args, run_raw_export_cli, 'export_raw')
    
    def do_config(self, args):
        if len(args) == 0:
            print("当前配置:"); [print(f"  {k}: {v}") for k, v in CONFIG_MGR.config.items()]
        elif len(args) == 1:
            key = args[0]
            print(f"{key}: {CONFIG_MGR.config.get(key, '未知配置项')}")
        elif len(args) >= 2:
            key, value_str = args[0], " ".join(args[1:])
            if key in CONFIG_MGR.config:
                original_type = type(CONFIG_MGR.config[key])
                try:
                    if original_type == bool: new_value = value_str.lower() in ['true', '1', 'yes']
                    else: new_value = original_type(value_str)
                    CONFIG_MGR.config[key] = new_value; CONFIG_MGR.save_config()
                    print(f"配置 '{key}' 已更新为 '{new_value}'.")
                except ValueError: print(f"错误: 无法将 '{value_str}' 转换为所需类型 ({original_type.__name__}).")
            else: print(f"错误: 未知的配置项 '{key}'")
    
    def do_set(self, args):
        global WORK_DIR, OUTPUT_DIR
        if len(args) < 2:
            print("错误: set 命令需要两个参数。 用法: set <workdir|outputdir> <路径>")
            return
        
        variable = args[0].lower()
        path = " ".join(args[1:])

        if variable == 'workdir':
            print(f"正在尝试将工作目录更改为: {path}...")
            previous_work_dir = WORK_DIR
            if setup_environment(path, global_args.log):
                print("工作目录已成功更新，所有数据已重新加载。")
            else:
                print("错误: 无法初始化新的工作目录。请确保路径正确且包含所需的数据库文件。")
                print("正在恢复到先前的工作目录...")
                if setup_environment(previous_work_dir, global_args.log):
                     print("已成功恢复。")
                else:
                     print("严重错误: 无法恢复到先前的工作目录，程序状态可能不稳定。")

        elif variable == 'outputdir':
            OUTPUT_DIR = os.path.abspath(os.path.normpath(path))
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"导出目录已更新为: {OUTPUT_DIR}")
        else:
            print(f"错误: 未知的变量 '{variable}'。可用: workdir, outputdir")

    def do_webui(self, args):
        print("正在启动 Web UI...")
        try:
            if is_port_in_use(global_args.ws_port, global_args.host) or is_port_in_use(global_args.http_port, global_args.host):
                print(f"\n错误: 端口 {global_args.ws_port} 或 {global_args.http_port} 已被占用。")
            else:
                asyncio.run(main_server(global_args.host, global_args.ws_port, global_args.http_port, global_args.no_browser))
        except KeyboardInterrupt:
            print("\n服务器已关闭。")
        except Exception as e:
            print(f"启动Web UI时发生错误: {e}")
        finally:
            print("正在退出程序...")
            sys.exit(0)

    def do_exit(self, args):
        print("再见！"); sys.exit(0)

def start_interactive_cli():
    cli = CommandLineInterface()
    cli.run()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="QQ NT 聊天记录导出工具 - Web UI & CLI. 默认启动 Web UI.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    # --- Mode Selection ---
    group_mode = parser.add_argument_group('运行模式')
    group_mode.add_argument('--cli', action='store_true', help='启动交互式命令行界面 (CLI)，不启动Web UI。')
    group_mode.add_argument('--sqlcipher', action='store_true', help='启动时强制执行SQLCipher解密流程。')
    group_mode.add_argument('--overwrite', action='store_true', help='与 --sqlcipher 配合使用，强制覆盖已存在的解密后数据库。')
    group_mode.add_argument('--no-browser', action='store_true', help='启动Web UI，但不自动打开浏览器。')
    group_mode.add_argument('--log', action='store_true', help='启用调试模式: 在控制台显示WebSocket通信,并记录详细的调试日志到文件。')
    
    # --- Listing ---
    group_list = parser.add_argument_group('列表与信息功能 (CLI模式)')
    group_list.add_argument('--list-friends', action='store_true', help='列出所有好友并退出。')
    group_list.add_argument('--list-groups', action='store_true', help='列出所有群聊并退出。')
    group_list.add_argument('--list-schema', action='store_true', help='列出所有数据库的表和字段结构并退出。')
    group_list.add_argument('--list-fields', nargs='?', const='all', default=None,
                            help='列出所有可导出的字段并退出。可选参数: c2c, group。')


    # --- Standard Export ---
    group_export = parser.add_argument_group('标准聊天记录导出 (CLI模式)')
    group_export.add_argument('--mode', choices=['individual', 'timeline'], help='导出模式: individual(独立文件) 或 timeline(时间线合并)。')
    group_export.add_argument('--friends', type=str, help='要导出的好友UID或QQ号, 多个用逗号分隔。使用 "all" 导出全部好友。')
    group_export.add_argument('--groups', type=str, help='要导出的群聊UID或群号, 多个用逗号分隔。使用 "all" 导出全部群聊。')
    group_export.add_argument('--format', type=str, default='md', help='导出格式 (md, txt, html, json-custom, csv-custom)。默认: md。')
    group_export.add_argument('--start', type=str, help="开始时间 (格式: 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS')。")
    group_export.add_argument('--end', type=str, help="结束时间 (格式: 'YYYY-MM-DD' 或 'YYYY-MM-DD HH:MM:SS')。")
    group_export.add_argument('--custom-fields', type=str, help="自定义导出格式(json-custom, csv-custom)所需的字段, 逗号分隔。")
    group_export.add_argument('--group-dirs', action='store_true', help='为每个好友分组创建独立的导出文件夹 (仅限 individual 模式)。')


    # --- Advanced Export ---
    group_adv_export = parser.add_argument_group('高级数据导出 (CLI模式)')
    group_adv_export.add_argument('--export-extra', action='store_true', help='触发群组附加数据导出模式。需搭配 --group 和 --type 使用。')
    group_adv_export.add_argument('--group', type=str, help='[附加导出] 指定目标群聊的ID (群号或UID)。')
    group_adv_export.add_argument('--type', choices=['members','essences','notifications','bulletins'], help='[附加导出] 指定要导出的数据类型。')
    
    group_adv_export.add_argument('--export-raw', action='store_true', help='触发数据库原始数据导出模式。需搭配 --db, --table, --columns 使用。')
    group_adv_export.add_argument('--db', type=str, help='[原始导出] 目标数据库文件名 (如 nt_msg.decrypt.db)。')
    group_adv_export.add_argument('--table', type=str, help='[原始导出] 目标数据表名。')
    group_adv_export.add_argument('--columns', type=str, help='[原始导出] 要导出的列名, 逗号分隔。')
    group_adv_export.add_argument('--raw-format', default='json', choices=['json', 'csv'], help='[原始导出] 原始数据导出格式。默认: json。')
    group_adv_export.add_argument('--parse-pb', action='store_true', help='[原始导出] 尝试解析Protobuf二进制字段。')
    
    # --- Web Server & Common ---
    group_web = parser.add_argument_group('Web 服务器与通用配置')
    group_web.add_argument('--host', type=str, default='localhost', help='主机地址。默认: localhost。')
    group_web.add_argument('--ws_port', type=int, default=8765, help='WebSocket服务器端口。默认: 8765。')
    group_web.add_argument('--http_port', type=int, default=9060, help='HTTP服务器端口。默认: 9060。')
    group_web.add_argument('--workdir', type=str, default='.', help='数据库文件所在的工作目录。默认: 当前目录。')
    group_web.add_argument('--location', type=str, help='指定一个自定义的根导出目录，覆盖默认位置。')


    args = parser.parse_args()
    global_args = args
    LOG_TO_CONSOLE = args.log
    
    workdir_to_use = args.workdir
    if getattr(sys, 'frozen', False) and args.workdir == '.':
        workdir_to_use = os.path.dirname(sys.executable)
    
    # 尽可能早地设置日志记录器
    setup_logging(args.log)

    action_args = [
        args.cli, args.list_friends, args.list_groups, args.list_schema, 
        args.list_fields, args.mode, args.export_extra, args.export_raw
    ]
    is_direct_action = any(arg for arg in action_args if arg is not None and arg is not False)

    # --- 解密流程处理 ---
    decryption_ok = True
    # 模式1: 使用 --sqlcipher 参数强制解密
    if args.sqlcipher:
        print("\n--> 已通过参数 --sqlcipher 启动解密流程。")
        logger.info("Decryption flow started via --sqlcipher flag.")
        if not perform_decryption(workdir_to_use, force_overwrite=args.overwrite):
            print("\n数据库解密流程失败。")
            logger.error("Decryption flow failed.")
            decryption_ok = False
        else:
            print("\n解密流程完成。")
            logger.info("Decryption flow completed.")
    # 模式2: 无任何操作参数（双击启动），进入交互式选择
    elif not is_direct_action:
        if not manage_decryption_on_startup(workdir_to_use):
            decryption_ok = False

    if not decryption_ok:
        input("按回车键退出...")
        sys.exit(1)

    # --- 环境设置与主程序启动 ---
    if not setup_environment(workdir_to_use, args.log):
        input("环境初始化失败, 按回车键退出...")
        sys.exit(1)

    # 根据参数执行相应操作
    if not is_direct_action:
        # 默认启动Web UI
        if args.location:
            OUTPUT_DIR = os.path.abspath(os.path.normpath(args.location))
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"导出目录已指定为: {OUTPUT_DIR}")
            logger.info(f"导出目录已指定为: {OUTPUT_DIR}")
        try:
            if is_port_in_use(args.ws_port, args.host) or is_port_in_use(args.http_port, args.host):
                 msg = f"\n错误: 端口 {args.ws_port} 或 {args.http_port} 已被占用。"
                 print(msg); logger.critical(msg.strip())
                 input("按回车键退出...")
            else: asyncio.run(main_server(args.host, args.ws_port, args.http_port, args.no_browser))
        except KeyboardInterrupt:
            msg = "\n服务器正在关闭..."
            print(msg); logger.info(msg.strip())
        except OSError as e:
            if e.errno in (10048, 98):
                msg = f"\n错误: 端口 {args.ws_port} 或 {args.http_port} 已被占用。"
                print(msg); logger.critical(msg.strip())
                input("按回车键退出...")
            else: raise
    else:
        # 执行CLI指定的直接操作
        if args.location:
            OUTPUT_DIR = os.path.abspath(os.path.normpath(args.location))
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"导出目录已指定为: {OUTPUT_DIR}")
            logger.info(f"导出目录已指定为: {OUTPUT_DIR}")

        if args.list_friends: run_list_friends()
        elif args.list_groups: run_list_groups()
        elif args.list_schema: run_list_db_schema()
        elif args.list_fields is not None: run_list_fields([args.list_fields])
        elif args.mode: run_direct_export_cli(args)
        elif args.export_extra:
            if not all([args.group, args.type]):
                print("错误: --export-extra 必须与 --group 和 --type 参数一同使用。"); sys.exit(1)
            ns = argparse.Namespace(group=args.group, type=args.type, location=args.location)
            run_export_group_extra_cli(ns)
        elif args.export_raw:
            if not all([args.db, args.table, args.columns]):
                print("错误: --export-raw 必须与 --db, --table, --columns 参数一同使用。"); sys.exit(1)
            ns = argparse.Namespace(db=args.db, table=args.table, columns=args.columns, raw_format=args.raw_format, parse_pb=args.parse_pb, location=args.location)
            run_raw_export_cli(ns)
        elif args.cli: start_interactive_cli()
    
    for con in DB_CONNECTIONS.values():
        if con: con.close()
    msg = "数据库连接已关闭。程序退出。"
    print(msg); logger.info(msg)
