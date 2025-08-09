from abc import ABC, abstractmethod
from collections import defaultdict
from typing import List, Type, TypeVar

import blackboxprotobuf
from pydantic import BaseModel


E = TypeVar("E", bound="Element")


class ElementRegistry:
    """
    A registry for managing and decoding elements based on their IDs.

    Attributes:
        _decoders (defaultdict): A dictionary mapping element IDs to their corresponding decoder classes.

    Methods:
        register(elem_id: int) -> callable:
            A class method that registers a decoder class for a given element ID.

        decode(data) -> E:
            A class method that decodes the given data using the registered decoder class for the element ID.
    """

    _decoders = defaultdict(lambda: UnsupportedElement)

    @classmethod
    def register(cls, elem_id: int) -> callable:
        """
        Registers a class as a decoder for a specific element ID.

        This method is intended to be used as a decorator to register a class
        that can decode messages of a specific type identified by `elem_id`.

        Args:
            elem_id (int): The element ID to register the class for.

        Example:
            @ElementRegistry.register(elem_id=10)
            class SomeElement(Element):
                @classmethod
                def decode(cls, data):
                    return SomeElement()
        """

        def decorator(element_class: Type[E]) -> Type[E]:
            cls._decoders[elem_id] = element_class
            return element_class

        return decorator

    @classmethod
    def decode(cls, data) -> E:
        """
        Decodes the given data using the appropriate decoder.

        Args:
            data (dict): The data to decode.

        Returns:
            E: The decoded element if successful.
            UnsupportedElement: If decoding fails due to a ValueError.
        """
        try:
            return cls._decoders[data.get("45002")].decode(data)
        except ValueError:
            return UnsupportedElement(data=None)


class Element(ABC, BaseModel):
    """
    Abstract base class for elements, inheriting from ABC and BaseModel.

    Methods:
        decode(cls, data) -> E:
            Decodes the given data into an instance of the element.
            Must be implemented by subclasses.

        __str__(self):
            Returns a string representation of the element.
            Must be implemented by subclasses.
    """

    ...

    @classmethod
    @abstractmethod
    def decode(cls, data) -> E:
        """
        Abstract method to decode the given data into an instance of the element.

        Args:
            data: The data to be decoded.

        Returns:
            An instance of type E.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError

    @abstractmethod
    def __str__(self):
        """
        Return a string representation of the object.
        This method should be overridden by subclasses to provide a meaningful
        string representation of the object. If not implemented, it raises a
        NotImplementedError.

        Returns:
            str: A string representation of the object.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """

        raise NotImplementedError


class UnsupportedElement(Element):
    """
    UnsupportedElement is a class that represents an element which is not supported.

    Attributes:
        data (dict | None): Contains the data unsupported to parse, None if fails to parse.

    Methods:
        decode(cls, data):
            Class method that decodes the given data into an UnsupportedElement instance.

        __str__():
            Returns a string representation indicating that the message is not supported.
    """

    data: dict | None

    @classmethod
    def decode(cls, data):
        return UnsupportedElement(data=data)

    def __str__(self):
        return "[不支持的消息]"


@ElementRegistry.register(elem_id=1)
class Text(Element):
    """
    Basic text element class.

    Attributes:
        content (str | None): The content of the text element.
    """

    content: str | None

    @classmethod
    def decode(cls, data):
        if not isinstance(data.get("45101"), bytes):
            return Text(content=None)
        return Text(content=data["45101"].decode())

    def __str__(self):
        return self.content


@ElementRegistry.register(elem_id=2)
class Image(Element):
    """
    Image element class.

    Attributes:
        filename (str | None): The filename of the image.
        width (int): The width of the image.
        height (int): The height of the image.
        path (str | None): The path of the image.
        alt (str | None): The alt text of the image.
    """

    filename: str | None
    width: int
    height: int
    path: str | None
    alt: str | None

    @classmethod
    def decode(cls, data):
        alt = data.get("45815")
        if isinstance(alt, list):
            if isinstance(alt[0], bytes):
                alt = alt[0].decode()
            else:
                alt = None
        else:
            alt = None

        return Image(
            filename=filename if isinstance(filename := (data["45402"]), str) else None,
            width=data["45411"],
            height=data["45412"],
            path=data.get("45812"),
            alt=alt,
        )

    def __str__(self):
        return self.alt if self.alt else ""


@ElementRegistry.register(elem_id=3)
class FileElement(Element):
    """
    File element class.

    Attributes:
        hash (str | None): The hash of the file.
        path (str | None): The path of the file.
    """

    hash: str | None
    path: str | None

    @classmethod
    def decode(cls, data):
        return FileElement(
            hash=hash_digest.hex() if isinstance(hash_digest := data.get("45406"), bytes) else None,
            path=(
                path.decode() if isinstance(path := data.get("45954"), bytes) else None
            ),
        )

    def __str__(self):
        return "[文件]"


@ElementRegistry.register(elem_id=4)
class AudioElement(Element):
    """
    Audio element class.

    Attributes:
        filename (str | None): The filename of the audio.
        hash (str | None): The hash of the audio.
    """

    filename: str
    hash: str | None

    @classmethod
    def decode(cls, data):
        return AudioElement(
            filename=data.get("45402"),
            hash=hash.hex() if isinstance(hash := data.get("45406"), bytes) else None,
        )

    def __str__(self):
        return "[语音消息]"


@ElementRegistry.register(elem_id=5)
class VideoElement(Element):
    """
    Video element class.

    Attributes:
        filename (str | None): The filename of the video.
        hash (str | None): The hash of the video.
    """

    filename: str | None
    hash: str | None

    @classmethod
    def decode(cls, data):
        return VideoElement(
            filename=data.get("40402"),
            hash=hash.hex() if isinstance(hash := data.get("45406"), bytes) else None,
        )

    def __str__(self):
        return "[视频消息]"


@ElementRegistry.register(elem_id=6)
class EmojiElement(Element):
    """
    System Emoji element class.

    Attributes:
        ID (int): The ID of the emoji.
    """

    ID: int

    @classmethod
    def decode(cls, data):
        return EmojiElement(
            ID=data.get("47601")  # -> emoji.db / base_sys_emoji_table / 81211
        )

    def __str__(self):
        return "[Emoji表情]"


@ElementRegistry.register(elem_id=7)
class Reply(Element):
    """
    Reply to a message.

    Attributes:
        source_seq (int | None): The sequence number of the source message.
        source_sender_uin (str | None): The sender UIN of the source message.
        source_sender_qq (int | None): The sender QQ of the source message.
        source_time (int | None): The time of the source message.
        source_content (Message): The source message parsed using from_reply.
    """

    source_seq: int | None
    source_sender_uin: str | None
    source_sender_qq: int | None
    source_time: int | None
    source_content: "Message"

    @classmethod
    def decode(cls, data):
        return Reply(
            source_seq=data.get("47402"),
            source_sender_uin=(
                sender_uin if isinstance(sender_uin := data.get("40020"), str) else None
            ),
            source_sender_qq=data.get("47403"),
            source_time=data.get("47404"),
            source_content=Message.from_reply(data.get("47423")),
        )

    def __str__(self):
        return ""


@ElementRegistry.register(elem_id=8)
class SystemNotificationElement(Element):
    """
    System notification abstract element.

    Methods:
        system_decode(cls, data) -> E:
            Decodes the given data into an instance of a SystemNotificationElement.
            Must be implemented by subclasses
    """

    @classmethod
    def decode(cls, data):
        # 47705 -> sender
        # 47716 -> withdrawer
        # 47713 -> suffix
        # 49154 or 45003 -> type I guess (1 -> withdraw)
        return WithdrawNotifyElement.system_decode(data)

    @classmethod
    def system_decode(cls, data):
        raise NotImplementedError

    def __str__(self):
        return "[系统消息]"


class WithdrawNotifyElement(SystemNotificationElement):
    """
    Withdraw notification SystemNotificationElement class.

    Attributes:
        sender (str | None): The sender of the message.
        withdrawer (str | None): The withdrawer of the message.
        suffix (str | None): The suffix of the withdraw notification.
    """

    sender: str | None
    withdrawer: str | None
    suffix: str | None

    @classmethod
    def system_decode(cls, data):
        return WithdrawNotifyElement(
            sender=sender if isinstance(sender := data.get("47705"), str) else None,
            withdrawer=(
                withdrawer if isinstance(withdrawer := data.get("47716"), str) else None
            ),
            suffix=suffix if (suffix := data.get("47713")) else None,
        )

    def __str__(self):
        return "撤回了一条消息"


@ElementRegistry.register(elem_id=9)
class RedPackElement(Element):
    """
    Red packet element.

    Attributes:
        greet (str): The greeting message for the red packet.
        alt (str): The alt text for the red packet.
        skin_type (str | None): The skin type of the red packet.
    """

    greet: str
    alt: str
    skin_type: str | None

    @classmethod
    def decode(cls, data):
        desc = data.get("48403")
        # 48403 -> 48443 greet
        #          48444 赶紧点击拆开吧
        #          48445 QQ红包
        #          48448 alt
        # 48421 -> 5     skin_type
        return RedPackElement(
            greet=desc.get("48443"),
            alt=desc.get("48448"),
            skin_type=(
                skin_type
                if isinstance(skin_type := data.get("48421").get("5"), str)
                else None
            ),
        )

    def __str__(self):
        return self.alt


@ElementRegistry.register(elem_id=10)
class AppElement(Element):
    """
    App message element.

    Attributes:
        data (str): The json data of the app message.
    """

    data: str

    @classmethod
    def decode(cls, data):
        return AppElement(data=data.get("47901").decode())

    def __str__(self):
        return "[应用消息]"


@ElementRegistry.register(elem_id=11)
class StickerElement(Element):
    """
    Sticker element.

    Attributes:
        alt (str | None): The alt text for the sticker.
        ID (str | None): The ID of the sticker.
    """

    alt: str | None
    ID: str | None

    @classmethod
    def decode(cls, data):
        return StickerElement(
            alt=data["80900"].decode() if isinstance(data["80900"], bytes) else None,
            ID=data["80903"].hex() if isinstance(data["80903"], bytes) else None,
        )

    def __str__(self):
        return self.alt if self.alt else ""


@ElementRegistry.register(elem_id=14)
class BotCardElement(Element):
    # TODO: i guess
    @classmethod
    def decode(cls, data):
        return BotCardElement()

    def __str__(self):
        return "[Bot卡片]"


@ElementRegistry.register(elem_id=16)
class XMLElement(Element):
    """
    XML message element.
    """
    @classmethod
    def decode(cls, data):
        # TODO: Example Missing
        return ForwardedMessagesXMLElement.xml_decode(data=data["48602"])

    @classmethod
    def xml_decode(cls, data):
        raise NotImplementedError

    def __str__(self):
        return ""


class ForwardedMessagesXMLElement(XMLElement):
    """
    Multiple forwarded messages XML element.
    """
    @classmethod
    def xml_decode(cls, data):
        # TODO
        return ForwardedMessagesXMLElement()

    def __str__(self):
        return "[聊天记录]"


@ElementRegistry.register(elem_id=17)
class BotCardMobileElement(Element):
    # TODO: i guess
    @classmethod
    def decode(cls, data):
        return BotCardMobileElement()

    def __str__(self):
        return "[Bot卡片]"


@ElementRegistry.register(elem_id=21)
class CallNotifyElement(Element):
    """
    Call notification element.

    Attributes:
        alt_1 (str): The first alt text.
        alt_2 (str): The second alt text
    """
    alt_1: str
    alt_2: str

    @classmethod
    def decode(cls, data):
        return CallNotifyElement(
            alt_1=data.get("48153"),
            alt_2=data.get("48157"),
        )

    def __str__(self):
        return self.alt_1


class Message(BaseModel):
    """
    Message class represents a message with an ID, sequence number, and a list of elements.

    Attributes:
        ID (int | None): The unique identifier of the message.
        seq (int | None): The sequence number of the message.
        elements (List[Element]): A list of elements contained in the message.

    Methods:
        from_db(cls, dbo: GroupMessage) -> "Message":
            Creates a Message instance from a database object.
            
            Args:
                dbo (GroupMessage): The database object containing message data.
            
            Returns:
                Message: A new instance of the Message class.
        
        from_reply(cls, embed) -> "Message":
            Creates a Message instance from a reply embed.
            
            Args:
                embed (dict or list): The embed data from a reply.
            
            Returns:
                Message: A new instance of the Message class.
    """
    ID: int | None
    seq: int | None
    elements: List["Element"]

    @classmethod
    def from_db(cls, dbo) -> "Message":
        """
        Create a Message instance from a GroupMessage database object.

        Args:
            cls: The class that this method is called on.
            dbo (GroupMessage): The database object containing the message data.

        Returns:
            Message: An instance of the Message class populated with data from the database object.
        """
        if dbo.msgBody is None:
            elements = []
        else:
            raw_elements, _ = blackboxprotobuf.decode_message(dbo.msgBody)
            raw_elements = raw_elements["40800"]
            if isinstance(raw_elements, dict):
                raw_elements = [raw_elements]
            elements = [ElementRegistry.decode(_) for _ in raw_elements]

        return Message(
            ID=dbo.msgId,
            seq=dbo.msgSeq,
            elements=elements,
        )

    @classmethod
    def from_reply(cls, embed) -> "Message":
        if embed is None:
            embed = []
        if isinstance(embed, dict):
            embed = [embed]

        elements = [ElementRegistry.decode(_) for _ in embed]
        return Message(ID=None, seq=None, elements=elements)