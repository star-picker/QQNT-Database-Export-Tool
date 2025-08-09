"""
Relating everything takes time......
"""

from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, LargeBinary, Text

from .man import DatabaseManager


__all__ = [
    "PrivateMessage",
    "GroupMessage",
    "NTUIDMapping",
    "SystemEmoji",
    "BottomEmoji",
    "EmojiConfig",
    "EmojiGroup",
    "EmojiMiscData",
    "FavEmojiInfo",
    "StickerPackage",
    "StickerMapping",
    "DoubtGroupNotifyList",
    "GroupBulletin",
    "GroupDetailInfo",
    "GroupEssence",
    "GroupList",
    "GroupMember",
    "GroupLevelBadge",
    "GroupNotify",
    "Buddy",
    "BuddyRequest",
    "BuddyCategory",
    "BotProfile",
    "BuddyProfile",
]


class Model(DeclarativeBase):
    ...


@DatabaseManager.register_model("nt_msg")
class PrivateMessage(Model):
    """
    Private Message Table
    nt_msg.db -> c2c_msg_table
    """
    __tablename__ = "c2c_msg_table"
    ID: Mapped[int] = mapped_column("40001", primary_key=True)
    UNK_01: Mapped[int] = mapped_column("40002")
    seq: Mapped[int] = mapped_column("40003")
    UNK_03: Mapped[int] = mapped_column("40010")
    UNK_04: Mapped[int] = mapped_column("40011")
    UNK_05: Mapped[int] = mapped_column("40012")
    UNK_06: Mapped[int] = mapped_column("40013")
    UNK_07: Mapped[str] = mapped_column("40020", String(24))  # Tencent internal UID
    UNK_08: Mapped[int] = mapped_column("40026")
    contact_uid: Mapped[str] = mapped_column("40021", String(24))  # Tencent internal UID
    UNK_10: Mapped[int] = mapped_column("40027")
    UNK_11: Mapped[int] = mapped_column("40040")
    UNK_12: Mapped[int] = mapped_column("40041")
    timestamp: Mapped[int] = mapped_column("40050")  # time message sent
    UNK_14: Mapped[int] = mapped_column("40052")
    UNK_15: Mapped[str] = mapped_column("40090", Text)  # empty
    nick_name: Mapped[str] = mapped_column("40093", Text)  # only self, otherwise basically empty
    message_body: Mapped[bytes] = mapped_column("40800", LargeBinary)  # protobuf
    # protobuf, the message replied to
    reply_body: Mapped[bytes] = mapped_column("40900", LargeBinary)
    UNK_19: Mapped[int] = mapped_column("40105")
    UNK_20: Mapped[int] = mapped_column("40005")
    # time of the day the message was sent, in sec
    timestamp_day: Mapped[int] = mapped_column("40058")
    UNK_22: Mapped[int] = mapped_column("40006")
    UNK_23: Mapped[int] = mapped_column("40100")
    # protobuf, seem to be related to reply, idk
    UNK_24: Mapped[bytes] = mapped_column("40600", LargeBinary)
    UNK_25: Mapped[int] = mapped_column("40060")
    UNK_26: Mapped[int] = mapped_column("40850")
    UNK_27: Mapped[int] = mapped_column("40851")
    UNK_28: Mapped[bytes] = mapped_column("40601", LargeBinary)  # always null
    UNK_29: Mapped[bytes] = mapped_column("40801", LargeBinary)  # protobuf
    # protobuf, insufficient resource, related with file?
    UNK_30: Mapped[bytes] = mapped_column("40605", LargeBinary)
    contact_qq: Mapped[int] = mapped_column("40030")  # qq num
    sender_qq: Mapped[int] = mapped_column("40033")  # qq num
    UNK_33: Mapped[int] = mapped_column("40062")
    UNK_34: Mapped[int] = mapped_column("40083")
    UNK_35: Mapped[int] = mapped_column("40084")


@DatabaseManager.register_model("nt_msg")
class GroupMessage(Model):
    """
    Group Message Table
    nt_msg.db -> group_msg_table
    """
    __tablename__ = "group_msg_table"
    msgId: Mapped[int] = mapped_column("40001", primary_key=True)
    msgRandom: Mapped[int] = mapped_column("40002")
    msgSeq: Mapped[int] = mapped_column("40003")
    chatType: Mapped[int] = mapped_column("40010")  # TODO: Enum
    msgType: Mapped[int] = mapped_column("40011")
    subMsgType: Mapped[int] = mapped_column("40012")
    sendType: Mapped[int] = mapped_column("40013")
    senderUid: Mapped[str] = mapped_column("40020", String(24))
    UNK_08: Mapped[int] = mapped_column("40026")
    peerUid: Mapped[str] = mapped_column("40021", String(24))
    peerUin: Mapped[int] = mapped_column("40027")
    UNK_11: Mapped[int] = mapped_column("40040")
    sendStatus: Mapped[int] = mapped_column("40041")
    msgTime: Mapped[int] = mapped_column("40050")  # UTC+8
    UNK_14: Mapped[int] = mapped_column("40052")
    sendMemberName: Mapped[str] = mapped_column("40090", Text)
    sendNickName: Mapped[str] = mapped_column("40093", Text)
    msgBody: Mapped[bytes] = mapped_column("40800", LargeBinary)  # protobuf
    refBody: Mapped[bytes] = mapped_column("40900", LargeBinary)
    UNK_19: Mapped[int] = mapped_column("40105")
    UNK_20: Mapped[int] = mapped_column("40005")
    msgTimeDay: Mapped[int] = mapped_column("40058")  # UTC+8
    elemId: Mapped[int] = mapped_column("40006")
    atFlag: Mapped[int] = mapped_column("40100")
    msgStatus: Mapped[bytes] = mapped_column("40600", LargeBinary)
    groupState: Mapped[int] = mapped_column("40060")
    refSeq: Mapped[int] = mapped_column("40850")
    UNK_27: Mapped[int] = mapped_column("40851")
    UNK_28: Mapped[bytes] = mapped_column("40601", LargeBinary)  # always null
    UNK_29: Mapped[bytes] = mapped_column("40801", LargeBinary)  # protobuf
    # protobuf, insufficient resource, related with file?
    UNK_30: Mapped[bytes] = mapped_column("40605", LargeBinary)
    groupUin: Mapped[int] = mapped_column("40030")  # qq num
    senderUin: Mapped[int] = mapped_column("40033")  # qq num
    UNK_33: Mapped[int] = mapped_column("40062")
    UNK_34: Mapped[int] = mapped_column("40083")
    UNK_35: Mapped[int] = mapped_column("40084")


@DatabaseManager.register_model("nt_msg")
class NTUIDMapping(Model):
    """
    qqnt uid mapping table
    nt_msg.db -> nt_uid_mapping_table
    """
    __tablename__ = "nt_uid_mapping_table"
    ID: Mapped[int] = mapped_column("48901", primary_key=True)
    uid: Mapped[str] = mapped_column("48902", String(24))
    UNK: Mapped[str] = mapped_column("48912", nullable=True)  # always null
    qq: Mapped[int] = mapped_column("1002")


@DatabaseManager.register_model("emoji")
class SystemEmoji(Model):
    """
    QQ 默认表情数据
    emoji.db -> base_sys_emoji_table
    """
    __tablename__ = "base_sys_emoji_table"
    ID: Mapped[str] = mapped_column("81211", primary_key=True)
    desc: Mapped[str] = mapped_column("81212")
    UNK_01: Mapped[str] = mapped_column("81213")
    UNK_02: Mapped[int] = mapped_column("81214")
    UNK_03: Mapped[int] = mapped_column("81215")
    UNK_04: Mapped[int] = mapped_column("81216")
    UNK_05: Mapped[int] = mapped_column("81217")
    download_link: Mapped[bytes] = mapped_column("81218")
    UNK_06: Mapped[str] = mapped_column("81219")
    UNK_07: Mapped[bytes] = mapped_column("81220")
    special: Mapped[int] = mapped_column("81221")
    UNK_08: Mapped[int] = mapped_column("81222")
    UNK_09: Mapped[int] = mapped_column("81223")
    UNK_10: Mapped[int] = mapped_column("81224")
    UNK_11: Mapped[int] = mapped_column("81225")
    emoji_type: Mapped[int] = mapped_column("81226")
    type_desc: Mapped[str] = mapped_column("81266")
    static_download_link: Mapped[str] = mapped_column("81229")
    apng_link: Mapped[str] = mapped_column("81230")


@DatabaseManager.register_model("emoji")
class BottomEmoji(Model):
    """
    收藏的原创表情
    emoji.db -> bottom_emoji_table
    """
    __tablename__ = "bottom_emoji_table"
    ID: Mapped[int] = mapped_column("80830", primary_key=True)
    data: Mapped[bytes] = mapped_column("81322")


@DatabaseManager.register_model("emoji")
class EmojiConfig(Model):
    """
    QQ 表情配置
    emoji.db -> emoji_config_storage_table
    """
    __tablename__ = "emoji_config_storage_table"
    ID: Mapped[int] = mapped_column("80401", primary_key=True)
    UNK: Mapped[int] = mapped_column("80402")
    data: Mapped[str] = mapped_column("80403")


@DatabaseManager.register_model("emoji")
class EmojiGroup(Model):
    """
    QQ 表情分组
    emoji.db -> emoji_group_table
    """
    __tablename__ = "emoji_group_table"
    data: Mapped[bytes] = mapped_column("81387", primary_key=True)


@DatabaseManager.register_model("emoji")
class EmojiMiscData(Model):
    """
    QQ 表情杂项数据
    emoji.db -> emoji_misc_data_table
    """
    __tablename__ = "emoji_misc_data_table"
    ID: Mapped[str] = mapped_column("81388", primary_key=True)
    data: Mapped[bytes] = mapped_column("81398")


@DatabaseManager.register_model("emoji")
class FavEmojiInfo(Model):
    """
    QQ 收藏表情信息
    emoji.db -> fav_emoji_info_storage_table
    """
    __tablename__ = "fav_emoji_info_storage_table"
    filename: Mapped[str] = mapped_column("80002", primary_key=True)
    order: Mapped[int] = mapped_column("80001")
    uin: Mapped[str] = mapped_column("1002")
    local_path: Mapped[str] = mapped_column("80012")
    download_url: Mapped[str] = mapped_column("80010")
    md5: Mapped[str] = mapped_column("80011")
    UNK_01: Mapped[str] = mapped_column("80013")
    UNK_02: Mapped[str] = mapped_column("80014")
    UNK_03: Mapped[str] = mapped_column("80211")
    UNK_04: Mapped[int] = mapped_column("80212")
    original: Mapped[int] = mapped_column("80213")
    original_id_1: Mapped[str] = mapped_column("80201")
    original_id_2: Mapped[str] = mapped_column("80202")
    UNK_05: Mapped[str] = mapped_column("80221")
    UNK_06: Mapped[str] = mapped_column("80222")
    UNK_07: Mapped[int] = mapped_column("80021")
    UNK_08: Mapped[int] = mapped_column("80022")
    desc_1: Mapped[str] = mapped_column("80223")
    desc_2: Mapped[str] = mapped_column("80225")


@DatabaseManager.register_model("emoji")
class StickerPackage(Model):
    """
    market sticker package table
    emoji.db -> market_emoticon_package_table
    """
    __tablename__ = "market_emoticon_package_table"
    ID: Mapped[str] = mapped_column("80943", primary_key=True)
    UNK_01: Mapped[int] = mapped_column("80944")
    UNK_02: Mapped[str] = mapped_column("80945")
    UNK_03: Mapped[str] = mapped_column("80946")
    name: Mapped[str] = mapped_column("80947")
    desc: Mapped[str] = mapped_column("80948")
    UNK_04: Mapped[int] = mapped_column("80949")
    UNK_05: Mapped[str] = mapped_column("80950")
    UNK_06: Mapped[int] = mapped_column("80951")
    UNK_07: Mapped[int] = mapped_column("80952")
    UNK_08: Mapped[int] = mapped_column("80953")
    UNK_09: Mapped[int] = mapped_column("80954")
    UNK_10: Mapped[str] = mapped_column("80955")
    UNK_11: Mapped[int] = mapped_column("80956")
    UNK_12: Mapped[int] = mapped_column("80957")
    UNK_13: Mapped[int] = mapped_column("80958")
    UNK_14: Mapped[int] = mapped_column("80959")
    UNK_15: Mapped[int] = mapped_column("80960")
    UNK_16: Mapped[str] = mapped_column("80961")
    UNK_17: Mapped[int] = mapped_column("80962")
    UNK_18: Mapped[int] = mapped_column("80963")
    UNK_19: Mapped[int] = mapped_column("80964")
    UNK_20: Mapped[int] = mapped_column("80965")
    UNK_21: Mapped[int] = mapped_column("80966")
    UNK_22: Mapped[str] = mapped_column("80967")
    UNK_23: Mapped[int] = mapped_column("80968")
    UNK_24: Mapped[int] = mapped_column("80969")
    UNK_25: Mapped[str] = mapped_column("80970")
    UNK_26: Mapped[int] = mapped_column("80971")
    UNK_27: Mapped[str] = mapped_column("80972")
    UNK_28: Mapped[int] = mapped_column("80973")
    UNK_29: Mapped[int] = mapped_column("80974")


@DatabaseManager.register_model("emoji")
class StickerMapping(Model):
    """
    market sticker table
    emoji.db -> market_emoticon_table
    """
    __tablename__ = "market_emoticon_table"
    ID: Mapped[str] = mapped_column("80920", primary_key=True)
    pack_id: Mapped[str] = mapped_column("80943", primary_key=True)
    alt: Mapped[str] = mapped_column("80921")
    UNK_00: Mapped[str] = mapped_column("80922")  # always empty
    UNK_01: Mapped[int] = mapped_column("80923")  # always 0
    UNK_02: Mapped[int] = mapped_column("80924")  # always 200
    UNK_03: Mapped[int] = mapped_column("80925")  # always 200
    UNK_04: Mapped[int] = mapped_column("80926")  # always 0
    UNK_05: Mapped[str] = mapped_column("80927")  # always empty
    UNK_06: Mapped[int] = mapped_column("80928")  # always 2
    UNK_07: Mapped[str] = mapped_column("80929")  # always empty
    # keyword maybe used to fast type a sticker, always a list of two same elements
    keyword: Mapped[str] = mapped_column("80930")
    UNK_08: Mapped[str] = mapped_column("80931")  # always empty
    UNK_09: Mapped[int] = mapped_column("80932")  # always 0
    UNK_10: Mapped[int] = mapped_column("80933")  # always 0
    # protobuf, always b2c227095b20225b5d22205d0a, '[ "[]" ]'
    UNK_11: Mapped[bytes] = mapped_column("80934", LargeBinary)
    UNK_12: Mapped[int] = mapped_column("80935")  # always 0
    UNK_13: Mapped[str] = mapped_column("80936")  # always empty
    UNK_14: Mapped[str] = mapped_column("80937")  # always empty
    UNK_15: Mapped[int] = mapped_column("80938")  # always 0
    UNK_16: Mapped[int] = mapped_column("80939")  # always 0
    UNK_17: Mapped[int] = mapped_column("80940", nullable=True)  # always NULL
    UNK_18: Mapped[str] = mapped_column("80941")  # always empty
    UNK_19: Mapped[str] = mapped_column("80942")  # always empty
    UNK_20: Mapped[str] = mapped_column("80602", nullable=True)  # always NULL
    UNK_21: Mapped[str] = mapped_column("80603", nullable=True)  # always NULL


@DatabaseManager.register_model("group_info")
class DoubtGroupNotifyList(Model):
    """
    过滤群通知
    group_info.db -> doubt_group_notify_list
    """
    __tablename__ = "doubt_group_notify_list"
    timestamp: Mapped[int] = mapped_column("61001", primary_key=True)
    type: Mapped[int] = mapped_column("61002")
    status: Mapped[int] = mapped_column("61003")
    group: Mapped[bytes] = mapped_column("61004")
    operatee: Mapped[bytes] = mapped_column("61005")
    operator: Mapped[bytes] = mapped_column("61006")
    operator_info: Mapped[bytes] = mapped_column("61007")
    operation_time: Mapped[int] = mapped_column("61008")
    UNK_09: Mapped[bytes] = mapped_column("61009")
    req_info: Mapped[str] = mapped_column("61010")
    additional: Mapped[str] = mapped_column("61011")


@DatabaseManager.register_model("group_info")
class GroupBulletin(Model):
    """
    群公告(仅最新)
    group_info.db -> group_bulletin_table
    """
    __tablename__ = "group_bulletin"
    groupUin: Mapped[int] = mapped_column("60001", primary_key=True)
    bulletin: Mapped[bytes] = mapped_column("64205")


@DatabaseManager.register_model("group_info")
class GroupDetailInfo(Model):
    """
    群聊更多信息
    group_info.db -> group_detail_info_ver1
    """
    __tablename__ = "group_detail_info_ver1"
    uin: Mapped[int] = mapped_column("60001", primary_key=True)
    name: Mapped[str] = mapped_column("60007")
    latest_bulletin: Mapped[bytes] = mapped_column("60216")
    desc: Mapped[bytes] = mapped_column("60217")
    remark: Mapped[str] = mapped_column("60026")
    owner_uid: Mapped[str] = mapped_column("60002")
    ctime: Mapped[int] = mapped_column("60004")
    UNK_008: Mapped[int] = mapped_column("60203")
    UNK_009: Mapped[int] = mapped_column("60204")
    max_member: Mapped[int] = mapped_column("60005")
    member_count: Mapped[int] = mapped_column("60006")
    UNK_012: Mapped[int] = mapped_column("60205")
    UNK_013: Mapped[int] = mapped_column("60206")
    UNK_014: Mapped[int] = mapped_column("60207")
    UNK_015: Mapped[int] = mapped_column("60210")
    UNK_016: Mapped[int] = mapped_column("60211")
    UNK_017: Mapped[int] = mapped_column("60212")
    UNK_018: Mapped[int] = mapped_column("60011")
    UNK_019: Mapped[int] = mapped_column("60214")
    tags: Mapped[str] = mapped_column("60218")
    UNK_021: Mapped[int] = mapped_column("60221")
    question: Mapped[str] = mapped_column("60224")
    UNK_023: Mapped[int] = mapped_column("60236")
    UNK_024: Mapped[int] = mapped_column("60238")
    UNK_025: Mapped[bytes] = mapped_column("60239")
    legacy_desc: Mapped[bytes] = mapped_column("60240")
    UNK_027: Mapped[bytes] = mapped_column("60241")
    UNK_028: Mapped[bytes] = mapped_column("60242")
    UNK_029: Mapped[int] = mapped_column("60243")
    UNK_030: Mapped[bytes] = mapped_column("60244")
    UNK_031: Mapped[int] = mapped_column("60027")
    UNK_032: Mapped[int] = mapped_column("60028")
    UNK_033: Mapped[int] = mapped_column("60255")
    UNK_034: Mapped[int] = mapped_column("60256")
    UNK_035: Mapped[int] = mapped_column("60258")
    UNK_036: Mapped[bytes] = mapped_column("60261")
    UNK_037: Mapped[str] = mapped_column("60267")
    UNK_038: Mapped[int] = mapped_column("60274")
    UNK_039: Mapped[int] = mapped_column("60277")
    UNK_040: Mapped[int] = mapped_column("60279")
    UNK_041: Mapped[int] = mapped_column("60280")
    UNK_042: Mapped[int] = mapped_column("60281")
    UNK_043: Mapped[int] = mapped_column("60282")
    UNK_044: Mapped[int] = mapped_column("60283")
    UNK_045: Mapped[int] = mapped_column("60284")
    UNK_046: Mapped[int] = mapped_column("60285")
    UNK_047: Mapped[int] = mapped_column("60286")
    UNK_048: Mapped[int] = mapped_column("60287")
    UNK_049: Mapped[int] = mapped_column("60288")
    UNK_050: Mapped[int] = mapped_column("60291")
    UNK_051: Mapped[int] = mapped_column("60292")
    UNK_052: Mapped[int] = mapped_column("60294")
    UNK_053: Mapped[int] = mapped_column("60295")
    UNK_054: Mapped[int] = mapped_column("60296")
    UNK_055: Mapped[int] = mapped_column("60299")
    UNK_056: Mapped[int] = mapped_column("60300")
    UNK_057: Mapped[int] = mapped_column("60301")
    UNK_058: Mapped[int] = mapped_column("60219")
    UNK_059: Mapped[int] = mapped_column("60220")
    UNK_060: Mapped[int] = mapped_column("60222")
    UNK_061: Mapped[int] = mapped_column("60223")
    UNK_062: Mapped[str] = mapped_column("60225")
    UNK_063: Mapped[int] = mapped_column("60226")
    UNK_064: Mapped[int] = mapped_column("60227")
    UNK_065: Mapped[int] = mapped_column("60228")
    UNK_066: Mapped[int] = mapped_column("60229")
    UNK_067: Mapped[int] = mapped_column("60230")
    UNK_068: Mapped[int] = mapped_column("60231")
    UNK_069: Mapped[str] = mapped_column("60232")
    UNK_070: Mapped[str] = mapped_column("60233")
    UNK_071: Mapped[int] = mapped_column("60234")
    UNK_072: Mapped[str] = mapped_column("60235")
    UNK_073: Mapped[int] = mapped_column("60237")
    UNK_074: Mapped[int] = mapped_column("60247")
    UNK_075: Mapped[int] = mapped_column("60248")
    UNK_076: Mapped[int] = mapped_column("60249")
    UNK_077: Mapped[int] = mapped_column("60250")
    UNK_078: Mapped[int] = mapped_column("60251")
    UNK_079: Mapped[int] = mapped_column("60252")
    UNK_080: Mapped[int] = mapped_column("60253")
    UNK_081: Mapped[int] = mapped_column("60254")
    UNK_082: Mapped[int] = mapped_column("60259")
    UNK_083: Mapped[int] = mapped_column("60018")
    UNK_084: Mapped[int] = mapped_column("60262")
    UNK_085: Mapped[int] = mapped_column("60263")
    UNK_086: Mapped[int] = mapped_column("60264")
    UNK_087: Mapped[int] = mapped_column("60265")
    UNK_088: Mapped[int] = mapped_column("60266")
    UNK_089: Mapped[int] = mapped_column("60268")
    UNK_090: Mapped[int] = mapped_column("60269")
    UNK_091: Mapped[int] = mapped_column("60270")
    UNK_092: Mapped[int] = mapped_column("60271")
    UNK_093: Mapped[int] = mapped_column("60272")
    UNK_094: Mapped[int] = mapped_column("60275")
    UNK_095: Mapped[int] = mapped_column("60276")
    UNK_096: Mapped[int] = mapped_column("60278")
    UNK_097: Mapped[int] = mapped_column("60302")
    UNK_098: Mapped[int] = mapped_column("60304")
    UNK_099: Mapped[int] = mapped_column("60306")
    UNK_100: Mapped[int] = mapped_column("60308")
    UNK_101: Mapped[bytes] = mapped_column("20017")
    UNK_102: Mapped[int] = mapped_column("60312")
    UNK_103: Mapped[int] = mapped_column("60313")
    UNK_104: Mapped[int] = mapped_column("66530")
    UNK_105: Mapped[int] = mapped_column("60298")
    UNK_106: Mapped[str] = mapped_column("60289")
    UNK_107: Mapped[int] = mapped_column("60307")
    UNK_108: Mapped[bytes] = mapped_column("60305")
    UNK_109: Mapped[bytes] = mapped_column("60257")
    UNK_110: Mapped[bytes] = mapped_column("60303")
    UNK_111: Mapped[int] = mapped_column("60290")
    leave_status: Mapped[int] = mapped_column("60340")
    UNK_113: Mapped[int] = mapped_column("60344")


@DatabaseManager.register_model("group_info")
class GroupEssence(Model):
    """
    群精华消息
    group_info.db -> group_essence
    """
    __tablename__ = "group_essence"
    group_uin: Mapped[int] = mapped_column("60001", primary_key=True)
    seq: Mapped[int] = mapped_column("67501", primary_key=True)
    msg_random: Mapped[int] = mapped_column("67502", primary_key=True)
    sender_uin: Mapped[int] = mapped_column("67503")
    sender_nickname: Mapped[str] = mapped_column("67504")
    status: Mapped[int] = mapped_column("67505")
    setter_uin: Mapped[int] = mapped_column("67506")
    setter_nickname: Mapped[str] = mapped_column("67507")
    timestamp: Mapped[int] = mapped_column("67508")
    UNK_10: Mapped[int] = mapped_column("67509")


@DatabaseManager.register_model("group_info")
class GroupList(Model):
    """
    群列表
    group_info.db -> group_list
    """
    __tablename__ = "group_list"
    uin: Mapped[int] = mapped_column("60001", primary_key=True)
    UNK_02: Mapped[int] = mapped_column("60221")
    ctime: Mapped[int] = mapped_column("60004")
    max_member: Mapped[int] = mapped_column("60005")
    member_count: Mapped[int] = mapped_column("60006")
    name: Mapped[str] = mapped_column("60007")
    UNK_07: Mapped[int] = mapped_column("60008")
    UNK_08: Mapped[int] = mapped_column("60009")
    UNK_09: Mapped[int] = mapped_column("60020")
    UNK_10: Mapped[int] = mapped_column("60011")
    UNK_11: Mapped[int] = mapped_column("60010")
    UNK_12: Mapped[int] = mapped_column("60017")
    UNK_13: Mapped[int] = mapped_column("60018")
    remark: Mapped[str] = mapped_column("60026")
    UNK_15: Mapped[int] = mapped_column("60022")
    UNK_16: Mapped[int] = mapped_column("60023")
    UNK_17: Mapped[int] = mapped_column("60027")
    UNK_18: Mapped[int] = mapped_column("60028")
    UNK_19: Mapped[int] = mapped_column("60029")
    UNK_20: Mapped[int] = mapped_column("60030")
    UNK_21: Mapped[int] = mapped_column("60031")
    UNK_22: Mapped[int] = mapped_column("60269")
    UNK_23: Mapped[int] = mapped_column("60012")
    UNK_24: Mapped[int] = mapped_column("60034")
    UNK_25: Mapped[int] = mapped_column("60035")
    UNK_26: Mapped[int] = mapped_column("60036")
    UNK_27: Mapped[int] = mapped_column("60037")
    UNK_28: Mapped[int] = mapped_column("60038")
    UNK_29: Mapped[int] = mapped_column("60204")
    UNK_30: Mapped[int] = mapped_column("60238")
    UNK_31: Mapped[int] = mapped_column("60258")
    UNK_32: Mapped[int] = mapped_column("60277")
    UNK_33: Mapped[bytes] = mapped_column("60040")
    UNK_34: Mapped[int] = mapped_column("60206")
    UNK_35: Mapped[int] = mapped_column("60255")
    UNK_36: Mapped[int] = mapped_column("60256")
    UNK_37: Mapped[int] = mapped_column("60279")
    UNK_38: Mapped[int] = mapped_column("60280")
    UNK_39: Mapped[int] = mapped_column("60281")
    UNK_40: Mapped[int] = mapped_column("60299")
    latest_bulletin: Mapped[bytes] = mapped_column("60216")
    UNK_42: Mapped[int] = mapped_column("60310")
    UNK_43: Mapped[int] = mapped_column("60259")
    UNK_44: Mapped[int] = mapped_column("60304")
    UNK_45: Mapped[str] = mapped_column("60267")
    UNK_46: Mapped[int] = mapped_column("60294")
    UNK_47: Mapped[int] = mapped_column("60295")
    UNK_48: Mapped[int] = mapped_column("60250")
    UNK_49: Mapped[int] = mapped_column("60262")
    UNK_50: Mapped[int] = mapped_column("60298")
    UNK_51: Mapped[int] = mapped_column("60252")
    UNK_52: Mapped[int] = mapped_column("60344")


@DatabaseManager.register_model("group_info")
class GroupMember(Model):
    """
    群成员
    group_info.db -> group_member
    """
    __tablename__ = "group_member3"
    group_nickname: Mapped[str] = mapped_column("64003")
    private_nickname: Mapped[str] = mapped_column("20002")
    group_uin: Mapped[int] = mapped_column("60001", primary_key=True)
    uid: Mapped[str] = mapped_column("1000", primary_key=True)
    UNK_05: Mapped[str] = mapped_column("1001")
    uin: Mapped[int] = mapped_column("1002")
    UNK_07: Mapped[int] = mapped_column("64002")
    UNK_08: Mapped[bytes] = mapped_column("64004")
    UNK_09: Mapped[int] = mapped_column("64005")
    UNK_10: Mapped[int] = mapped_column("64006")
    join_time: Mapped[int] = mapped_column("64007")
    last_message_time: Mapped[int] = mapped_column("64008")
    last_ban_ends: Mapped[int] = mapped_column("64009")
    admin: Mapped[int] = mapped_column("64010")
    UNK_15: Mapped[int] = mapped_column("64011")
    UNK_16: Mapped[int] = mapped_column("64012")
    UNK_17: Mapped[int] = mapped_column("64013")
    UNK_18: Mapped[int] = mapped_column("64017")
    UNK_19: Mapped[int] = mapped_column("64015")
    status: Mapped[int] = mapped_column("64016")
    UNK_21: Mapped[int] = mapped_column("64018")
    UNK_22: Mapped[int] = mapped_column("64034")
    UNK_23: Mapped[int] = mapped_column("64020")
    UNK_24: Mapped[int] = mapped_column("64021")
    UNK_25: Mapped[int] = mapped_column("64022")
    custom_badge: Mapped[str] = mapped_column("64023")
    UNK_27: Mapped[int] = mapped_column("64024")
    UNK_28: Mapped[int] = mapped_column("64025")
    UNK_29: Mapped[int] = mapped_column("64026")
    UNK_30: Mapped[int] = mapped_column("64027")
    UNK_31: Mapped[int] = mapped_column("64028")
    UNK_32: Mapped[str] = mapped_column("64029")
    UNK_33: Mapped[int] = mapped_column("64030")
    UNK_34: Mapped[int] = mapped_column("64031")
    UNK_35: Mapped[int] = mapped_column("64032")
    level: Mapped[int] = mapped_column("64035")


@DatabaseManager.register_model("group_info")
class GroupLevelBadge(Model):
    """
    群等级头衔信息
    group_info.db -> group_member_level_info
    """
    __tablename__ = "group_member_level_info"
    uin: Mapped[int] = mapped_column("60001", primary_key=True)
    group_level: Mapped[int] = mapped_column("67100")
    UNK_3: Mapped[int] = mapped_column("67101")
    UNK_4: Mapped[int] = mapped_column("67102")
    badges: Mapped[bytes] = mapped_column("67103")
    UNK_6: Mapped[int] = mapped_column("67104")


@DatabaseManager.register_model("group_info")
class GroupNotify(Model):
    """
    群通知
    group_info.db -> group_notify_list
    """
    __tablename__ = "group_notify_list"
    timestamp: Mapped[int] = mapped_column("61001", primary_key=True)
    type: Mapped[int] = mapped_column("61002")
    status: Mapped[int] = mapped_column("61003")
    group: Mapped[bytes] = mapped_column("61004")
    operatee: Mapped[bytes] = mapped_column("61005")
    operator: Mapped[bytes] = mapped_column("61006")
    operator_info: Mapped[bytes] = mapped_column("61007")
    operation_time: Mapped[int] = mapped_column("61008")
    UNK_09: Mapped[bytes] = mapped_column("61009")
    req_info: Mapped[str] = mapped_column("61010")
    additional: Mapped[str] = mapped_column("61011")


@DatabaseManager.register_model("profile_info")
class Buddy(Model):
    """
    好友信息
    profile_info.db -> buddy_list
    """
    __tablename__ = "buddy_list"
    uid: Mapped[str] = mapped_column("1000", primary_key=True)
    qid: Mapped[str] = mapped_column("1001")
    uin: Mapped[int] = mapped_column("1002")
    category: Mapped[int] = mapped_column("25007")


@DatabaseManager.register_model("profile_info")
class BuddyRequest(Model):
    """
    好友通知
    profile_info.db -> buddy_req_list_5
    """
    __tablename__ = "buddy_req_list_5"
    timestamp: Mapped[int] = mapped_column("21204", primary_key=True)
    uid: Mapped[str] = mapped_column("21001", primary_key=True)
    nickname: Mapped[str] = mapped_column("20002")
    UNK_04: Mapped[str] = mapped_column("20004")
    UNK_05: Mapped[int] = mapped_column("21512")
    approved: Mapped[int] = mapped_column("21502")
    message: Mapped[str] = mapped_column("21508")
    source: Mapped[str] = mapped_column("21509")
    status: Mapped[int] = mapped_column("21505")
    group_uin: Mapped[int] = mapped_column("60001")
    UNK_11: Mapped[str] = mapped_column("60007")
    UNK_12: Mapped[int] = mapped_column("21515")
    source_flag: Mapped[int] = mapped_column("21501")
    UNK_14: Mapped[int] = mapped_column("21516")
    UNK_15: Mapped[int] = mapped_column("21523")
    UNK_16: Mapped[int] = mapped_column("21513")
    UNK_17: Mapped[int] = mapped_column("21506")
    UNK_18: Mapped[int] = mapped_column("21517")
    UNK_19: Mapped[int] = mapped_column("21519")
    UNK_20: Mapped[str] = mapped_column("21522")
    UNK_21: Mapped[str] = mapped_column("21525")
    UNK_22: Mapped[int] = mapped_column("21524")
    UNK_23: Mapped[int] = mapped_column("21526")
    UNK_24: Mapped[int] = mapped_column("21510")
    UNK_25: Mapped[int] = mapped_column("21511")


@DatabaseManager.register_model("profile_info")
class BuddyCategory(Model):
    """
    好友分组
    profile_info.db -> category_list_v2
    """
    __tablename__ = "category_list_v2"
    UNK_1: Mapped[str] = mapped_column("1000", primary_key=True)
    UNK_2: Mapped[int] = mapped_column("25006")
    UNK_3: Mapped[int] = mapped_column("25013")
    UNK_4: Mapped[int] = mapped_column("25012")
    UNK_5: Mapped[int] = mapped_column("20075")
    UNK_6: Mapped[bytes] = mapped_column("25001")
    data: Mapped[bytes] = mapped_column("25011")
    UNK_8: Mapped[int] = mapped_column("25015")


@DatabaseManager.register_model("profile_info")
class BotProfile(Model):
    """
    机器人信息
    profile_info.db -> profile_info_adelie
    """
    __tablename__ = "profile_info_adelie"
    qid: Mapped[str] = mapped_column("1000", primary_key=True)
    uin: Mapped[int] = mapped_column("1002")
    nickname: Mapped[str] = mapped_column("320001")
    avatar_url: Mapped[str] = mapped_column("320002")
    desc: Mapped[str] = mapped_column("320003")
    settings: Mapped[str] = mapped_column("320004")
    UNK_07: Mapped[int] = mapped_column("320005")
    UNK_08: Mapped[str] = mapped_column("320006")
    UNK_09: Mapped[str] = mapped_column("320007")
    background_light: Mapped[str] = mapped_column("320008")
    background_dark: Mapped[str] = mapped_column("320009")
    UNK_12: Mapped[bytes] = mapped_column("320010")
    UNK_13: Mapped[bytes] = mapped_column("320011")
    UNK_14: Mapped[int] = mapped_column("320012")
    UNK_15: Mapped[int] = mapped_column("320013")
    UNK_16: Mapped[bytes] = mapped_column("320014")
    UNK_17: Mapped[int] = mapped_column("320015")
    UNK_18: Mapped[int] = mapped_column("320016")
    UNK_19: Mapped[int] = mapped_column("320017")
    UNK_20: Mapped[int] = mapped_column("320060")
    UNK_21: Mapped[bytes] = mapped_column("320018")
    UNK_22: Mapped[int] = mapped_column("320019")
    UNK_23: Mapped[int] = mapped_column("320020")
    UNK_24: Mapped[int] = mapped_column("32002")
    UNK_25: Mapped[int] = mapped_column("320021")
    UNK_26: Mapped[bytes] = mapped_column("320022")
    UNK_27: Mapped[bytes] = mapped_column("320023")
    UNK_28: Mapped[bytes] = mapped_column("320025")
    UNK_29: Mapped[int] = mapped_column("320026")
    UNK_30: Mapped[str] = mapped_column("320027")
    UNK_31: Mapped[int] = mapped_column("320028")
    UNK_32: Mapped[str] = mapped_column("320029")
    UNK_33: Mapped[str] = mapped_column("320030")
    UNK_34: Mapped[int] = mapped_column("320031")
    UNK_35: Mapped[int] = mapped_column("320032")
    UNK_36: Mapped[str] = mapped_column("320033")
    UNK_37: Mapped[int] = mapped_column("320034")
    body: Mapped[str] = mapped_column("320035")
    UNK_39: Mapped[str] = mapped_column("320036")
    UNK_40: Mapped[int] = mapped_column("320037")
    UNK_41: Mapped[int] = mapped_column("320038")
    UNK_42: Mapped[int] = mapped_column("320039")
    UNK_43: Mapped[int] = mapped_column("320040")
    UNK_44: Mapped[int] = mapped_column("320041")
    UNK_45: Mapped[int] = mapped_column("320042")
    UNK_46: Mapped[str] = mapped_column("320043")
    UNK_47: Mapped[str] = mapped_column("320044")
    UNK_48: Mapped[str] = mapped_column("320045")
    UNK_49: Mapped[int] = mapped_column("320046")
    UNK_50: Mapped[int] = mapped_column("320047")
    UNK_51: Mapped[str] = mapped_column("320048")
    UNK_52: Mapped[int] = mapped_column("320051")
    UNK_53: Mapped[int] = mapped_column("320049")
    UNK_54: Mapped[bytes] = mapped_column("320050")
    UNK_55: Mapped[int] = mapped_column("320059")
    UNK_56: Mapped[int] = mapped_column("320052")
    UNK_57: Mapped[int] = mapped_column("320054")
    UNK_58: Mapped[int] = mapped_column("320055")
    UNK_59: Mapped[int] = mapped_column("320056")
    UNK_60: Mapped[int] = mapped_column("320057")
    UNK_61: Mapped[int] = mapped_column("320058")
    UNK_62: Mapped[bytes] = mapped_column("320062")
    UNK_63: Mapped[int] = mapped_column("320063")


@DatabaseManager.register_model("profile_info")
class BuddyProfile(Model):
    """
    好友信息
    profile_info.db -> profile_info_v6
    """
    __tablename__ = "profile_info_v6"
    qid: Mapped[str] = mapped_column("1001")
    uin: Mapped[int] = mapped_column("1002")
    nickname: Mapped[str] = mapped_column("20002")
    UNK_4: Mapped[str] = mapped_column("24106")
    UNK_5: Mapped[str] = mapped_column("24107")
    UNK_6: Mapped[str] = mapped_column("24108")
    UNK_7: Mapped[str] = mapped_column("24109")
    remark: Mapped[str] = mapped_column("20009")
    signature: Mapped[str] = mapped_column("20011")
    uid: Mapped[str] = mapped_column("1000", primary_key=True)
    UNK_11: Mapped[int] = mapped_column("20001")
    UNK_12: Mapped[int] = mapped_column("20003")
    avatar_url: Mapped[str] = mapped_column("20004")
    UNK_14: Mapped[int] = mapped_column("20005")
    UNK_15: Mapped[int] = mapped_column("20006")
    UNK_16: Mapped[int] = mapped_column("20007")
    UNK_17: Mapped[int] = mapped_column("20008")
    UNK_18: Mapped[int] = mapped_column("20010")
    UNK_19: Mapped[int] = mapped_column("20012")
    UNK_20: Mapped[int] = mapped_column("20014")
    UNK_21: Mapped[bytes] = mapped_column("20017")
    UNK_22: Mapped[int] = mapped_column("20016")
    UNK_23: Mapped[int] = mapped_column("24103")
    UNK_24: Mapped[bytes] = mapped_column("20042")
    UNK_25: Mapped[bytes] = mapped_column("20059")
    UNK_26: Mapped[int] = mapped_column("20060")
    UNK_27: Mapped[int] = mapped_column("20061")
    UNK_28: Mapped[int] = mapped_column("20043")
    UNK_29: Mapped[int] = mapped_column("20048")
    UNK_30: Mapped[int] = mapped_column("20037")
    UNK_31: Mapped[int] = mapped_column("20056")
    UNK_32: Mapped[int] = mapped_column("20067")
    UNK_33: Mapped[bytes] = mapped_column("20057")
    UNK_34: Mapped[int] = mapped_column("20070")
    UNK_35: Mapped[int] = mapped_column("20071")
    UNK_36: Mapped[bytes] = mapped_column("21000")
    relation: Mapped[bytes] = mapped_column("20072")
    UNK_38: Mapped[int] = mapped_column("20075")
    UNK_39: Mapped[bytes] = mapped_column("20066")
    UNK_40: Mapped[int] = mapped_column("24104")
    UNK_41: Mapped[bytes] = mapped_column("24105")
    UNK_42: Mapped[int] = mapped_column("24110")
    UNK_43: Mapped[int] = mapped_column("24111")
