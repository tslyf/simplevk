from dataclasses import dataclass, field
from typing import Any

from dacite import Config, from_dict

DACITE_CONFIG = Config(strict=False, cast=[bool, int, str, float])


@dataclass(slots=True, kw_only=True)
class BaseAttachment:
    attachment_type: str = field(init=False)


@dataclass(slots=True, kw_only=True)
class PhotoSize:
    url: str | None = None
    width: int = 0
    height: int = 0
    type: str | None = None


@dataclass(slots=True, kw_only=True)
class PhotoSizes:
    sizes: list[PhotoSize]


@dataclass(slots=True, kw_only=True)
class Likes:
    count: int
    user_likes: bool = False
    can_like: bool = False
    can_publish: bool = False


@dataclass(slots=True, kw_only=True)
class Reposts:
    count: int
    wall_count: int = 0
    mail_count: int = 0
    user_reposted: bool = False


@dataclass(slots=True, kw_only=True)
class Photo(BaseAttachment):
    attachment_type: str = field(init=False, default="photo")

    id: int
    album_id: int = 0
    owner_id: int
    user_id: int = 0
    text: str | None = None
    date: int = 0
    thumb_hash: str | None = None
    has_tags: bool = False
    sizes: list[PhotoSize] = field(default_factory=list)
    width: int | None = None
    height: int | None = None
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class Video(BaseAttachment):
    attachment_type: str = field(init=False, default="video")

    id: int
    owner_id: int
    title: str
    description: str = ""
    duration: int = 0
    image: list[PhotoSize] = field(default_factory=list)
    first_frame: list[PhotoSize] = field(default_factory=list)
    date: int | None = None
    adding_date: int = 0
    views: int = 0
    local_views: int = 0
    comments: int = 0
    player: str | None = None
    platform: str | None = None
    can_add: bool = False
    is_private: bool = False
    access_key: str | None = None
    processing: bool = False
    is_favorite: bool = False
    can_comment: bool = False
    can_edit: bool = False
    can_like: bool = False
    can_repost: bool = False
    can_subscribe: bool = False
    can_add_to_faves: bool = False
    can_attach_link: bool = False
    width: int = 0
    height: int = 0
    user_id: int | None = None
    converting: bool = False
    added: bool = False
    is_subscribed: bool = False
    repeat: bool = False
    type: str | None = None
    balance: int = 0
    live: bool = False
    live_start_time: int | None = None
    live_status: str | None = None
    upcoming: bool = False
    spectators: int = 0
    likes: Likes | None = None
    reposts: Reposts | None = None


@dataclass(slots=True, kw_only=True)
class Audio(BaseAttachment):
    attachment_type: str = field(init=False, default="audio")

    id: int
    owner_id: int
    artist: str
    title: str
    duration: int = 0
    url: str | None = None
    lyrics_id: int | None = None
    album_id: int | None = None
    genre_id: int | None = None
    date: int = 0
    no_search: bool = False
    is_hq: bool = False
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class Graffiti(BaseAttachment):
    attachment_type: str = field(init=False, default="doc")

    id: int
    owner_id: int
    url: str
    width: int = 0
    height: int = 0
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class AudioMessage(BaseAttachment):
    attachment_type: str = field(init=False, default="doc")

    id: int
    owner_id: int
    duration: int = 0
    waveform: list[int] = field(default_factory=list)
    link_mp3: str | None = None
    link_ogg: str | None = None
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class DocGraffitiPreview:
    src: str
    width: int = 0
    height: int = 0


@dataclass(slots=True, kw_only=True)
class DocAudioMessagePreview:
    duration: int
    waveform: list[int] = field(default_factory=list)
    link_mp3: str | None = None
    link_ogg: str | None = None


@dataclass(slots=True, kw_only=True)
class DocPreview:
    photo: PhotoSizes | None = None
    graffiti: DocGraffitiPreview | None = None
    audio_message: DocAudioMessagePreview | None = None


@dataclass(slots=True, kw_only=True)
class Doc(BaseAttachment):
    attachment_type: str = field(init=False, default="doc")

    id: int
    owner_id: int
    title: str
    size: int = 0
    ext: str | None = None
    url: str | None = None
    date: int | None = None
    type: int = 0
    preview: DocPreview | None = None
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class Product:
    price: int


@dataclass(slots=True, kw_only=True)
class LinkButtonAction:
    type: str
    url: str


@dataclass(slots=True, kw_only=True)
class LinkButton:
    title: str
    action: LinkButtonAction | None = None


@dataclass(slots=True, kw_only=True)
class Link(BaseAttachment):
    attachment_type: str = field(init=False, default="link")

    url: str
    title: str
    caption: str | None = None
    description: str | None = None
    photo: Photo | None = None
    product: Product | None = None
    button: LinkButton | None = None
    preview_page: str = ""
    preview_url: str = ""


@dataclass(slots=True, kw_only=True)
class Sticker(BaseAttachment):
    attachment_type: str = field(init=False, default="sticker")

    product_id: int
    sticker_id: int
    images: list[PhotoSize] = field(default_factory=list)
    images_with_background: list[PhotoSize] = field(default_factory=list)
    animation_url: str | None = None
    is_allowed: bool = False


@dataclass(slots=True, kw_only=True)
class Gift:
    id: int
    thumb_256: str | None = None
    thumb_96: str | None = None
    thumb_48: str | None = None


@dataclass(slots=True, kw_only=True)
class GiftItem(BaseAttachment):
    attachment_type: str = field(init=False, default="gift-item")

    id: int
    from_id: int
    message: str | None = None
    date: int | None = None
    gift: Gift
    privacy: int | None = None
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class MarketAlbum(BaseAttachment):
    attachment_type: str = field(init=False, default="market_album")

    id: int
    owner_id: int
    title: str = ""
    is_main: bool = False
    is_hidden: bool = False
    photo: Photo | None = None
    count: int = 0
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class WallReplyDonut:
    is_don: bool = False
    placeholder: str = ""


@dataclass(slots=True, kw_only=True)
class WallReplyThread:
    count: int
    items: list["WallReply"] = field(default_factory=list)
    can_post: bool = False
    show_reply_button: bool = False
    groups_can_post: bool = False


@dataclass(slots=True, kw_only=True)
class WallReply(BaseAttachment):
    attachment_type: str = field(init=False, default="wall_reply")

    id: int
    from_id: int
    date: int
    text: str
    donut: WallReplyDonut | None = None
    reply_to_user: int | None = None
    reply_to_comment: int | None = None
    attachments: list[Any] = field(default_factory=list)
    parents_stack: list[int] = field(default_factory=list)
    thread: WallReplyThread | None = None


@dataclass(slots=True, kw_only=True)
class Copyright:
    id: int
    link: str | None = None
    name: str | None = None
    type: str | None = None


@dataclass(slots=True, kw_only=True)
class Views:
    count: int = 0


@dataclass(slots=True, kw_only=True)
class Comments:
    count: int = 0
    can_post: bool = False
    groups_can_post: bool = False
    can_close: bool = False
    can_open: bool = False


@dataclass(slots=True, kw_only=True)
class PostSource:
    type: str
    platform: str
    data: str
    url: str


@dataclass(slots=True, kw_only=True)
class Place:
    id: int
    title: str
    latitude: int
    longitude: int
    created: int | None = None
    icon: str | None = None
    checkins: int | None = None
    updated: int | None = None
    type: int | None = None
    city: int | None = None
    address: str | None = None


@dataclass(slots=True, kw_only=True)
class Geo:
    type: str
    coordinates: str
    place: Place | None = None


@dataclass(slots=True, kw_only=True)
class WallDonut:
    is_donut: bool = False
    paid_duration: int | None = None
    placeholder: str | None = None
    can_publish_free_copy: bool = False
    edit_mode: str


@dataclass(slots=True, kw_only=True)
class Post(BaseAttachment):
    attachment_type: str = field(init=False, default="wall")

    id: int
    owner_id: int
    from_id: int
    created_by: int | None = None
    date: int
    text: str
    reply_owner_id: int | None = None
    reply_post_id: int | None = None
    friends_only: bool = False
    comments: Comments | None = None
    copyright: Copyright | None = None
    likes: Likes | None = None
    reposts: Reposts | None = None
    views: Views | None = None
    post_type: str
    post_source: PostSource | None = None
    attachments: list[dict] = field(default_factory=list)
    geo: Geo | None = None
    signer_id: int | None = None
    copy_history: list["Post"] = field(default_factory=list)
    can_pin: bool = False
    can_delete: bool = False
    can_edit: bool = False
    is_pinned: bool = False
    marked_as_ads: bool = False
    is_favorite: bool = False
    donut: WallDonut | None = None
    postponed_id: int | None = None
    access_key: str | None = None


@dataclass(slots=True, kw_only=True)
class Unknown(BaseAttachment):
    attachment_type: str = field(default="unknown")

    data: dict = field(default_factory=dict)


_ATTACHMENT_MAP: dict[str, type[BaseAttachment]] = {
    "photo": Photo,
    "video": Video,
    "audio": Audio,
    "doc": Doc,
    "link": Link,
    "sticker": Sticker,
    "wall": Post,
    "wall_reply": WallReply,
    # "market": Market,
    "market_album": MarketAlbum,
    "gift": GiftItem,
    "graffiti": Graffiti,
    "audio_message": AudioMessage,
}

_DOC_ATTACHMENTS: list[str] = ["doc", "graffiti", "audio_message"]


def parse_attachment(data: dict) -> BaseAttachment | None:
    att_type = data.get("type")
    if not att_type:
        return None

    target_class = _ATTACHMENT_MAP.get(att_type)
    if not target_class:
        return Unknown(attachment_type=att_type, data=data)

    inner_data = data.get(att_type, data)

    return from_dict(data_class=target_class, data=inner_data, config=DACITE_CONFIG)
