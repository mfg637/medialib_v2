import typing
from typing import Optional
import abc
import re


class AbstractOriginType(abc.ABC):
    def __init__(
        self, origin_id: Optional[str] = None, alternate: bool = False
    ) -> None:
        self.origin_id = origin_id
        self.alternate = alternate

    @abc.abstractmethod
    def generate_url(self, origin_content_id: Optional[str] = None) -> str:
        pass

    @abc.abstractmethod
    def get_prefix(self) -> str:
        pass

    @abc.abstractmethod
    def parse_url(self, url: str) -> typing.Optional[str]:
        """
        returns origin content id or None
        """
        pass

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @staticmethod
    def filesystem_safe_content_id_s(origin_content_id: str):
        return origin_content_id.replace("#", "_")

    def _validate_origin_id(
        self, origin_content_id: Optional[str] = None
    ) -> str:
        if origin_content_id is None:
            if self.origin_id is not None:
                origin_content_id = self.origin_id
            else:
                raise ValueError("origin_id is unset")
        return origin_content_id

    def filesystem_safe_content_id(
        self, origin_content_id: Optional[str] = None
    ):
        origin_content_id = self._validate_origin_id(origin_content_id)
        return self.filesystem_safe_content_id_s(origin_content_id)


class SimpleOriginType(AbstractOriginType):
    @abc.abstractmethod
    def _get_template_string(self) -> str:
        pass

    def generate_url(self, origin_content_id: Optional[str] = None):
        origin_content_id = self._validate_origin_id(origin_content_id)
        return self._get_template_string().format(origin_content_id)


class DerpibooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://derpibooru.org/images/{}"

    def get_prefix(self):
        return "db"

    def get_name(self) -> str:
        return "derpibooru"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://derpibooru.org/images/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class PonybooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://ponybooru.org/images/{}"

    def get_prefix(self):
        return "pb"

    def get_name(self) -> str:
        return "ponybooru"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://ponybooru.org/images/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class TwibooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://twibooru.org/{}"

    def get_prefix(self):
        return "tb"

    def get_name(self) -> str:
        return "twibooru"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://twibooru.org/"):
            raw_str = url.split("?", maxsplit=1)[0].split("/", maxsplit=3)[-1]
            test = re.match(r"^\d+$", raw_str)
            if test is not None:
                return raw_str


class E621Origin(SimpleOriginType):
    def _get_template_string(self):
        return "https://e621.net/posts/{}"

    def get_prefix(self):
        return "ef"

    def get_name(self) -> str:
        return "e621"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://e621.net/posts/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class E6AIOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://e6ai.net/posts/{}"

    def get_prefix(self):
        return "ea"

    def get_name(self) -> str:
        return "e6ai"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://e6ai.net/posts/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class FurbooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://furbooru.org/images/{}"

    def get_prefix(self):
        return "fb"

    def get_name(self) -> str:
        return "furbooru"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://furbooru.org/images/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class TantabusAIOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://tantabus.ai/images/{}"

    def get_prefix(self):
        return "ta"

    def get_name(self) -> str:
        return "tantabus"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://tantabus.ai/images/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class CivitAIOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://civitai.com/images/{}"

    def get_prefix(self):
        return "ca"

    def get_name(self) -> str:
        return "civit-ai"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://civitai.com/images/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class FurAffinityOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://www.furaffinity.net/view/{}/"

    def get_prefix(self):
        return "fa"

    def get_name(self) -> str:
        return "furaffinity"

    def parse_url(self, url: str) -> typing.Optional[str]:
        if url.startswith("https://www.furaffinity.net/view/"):
            return url.split("?", maxsplit=1)[0].split("/")[-1]


class TwitterXOrigin(AbstractOriginType):
    _URL_PATTERN = re.compile(
        r"https?://(?:x|twitter)\.com/(?P<user>[^/]+)/status/(?P<status_id>\d+)(?:/photo/(?P<photo_id>\d+))?"
    )

    def generate_url(self, origin_content_id: Optional[str] = None):
        origin_content_id = self._validate_origin_id(origin_content_id)
        id_parts: list[str] = origin_content_id.split("#")
        if len(id_parts) == 3:
            return (
                f"https://x.com/{id_parts[0]}/status/"
                f"{id_parts[1]}/photo/{id_parts[2]}"
            )
        elif len(id_parts) == 2:
            return f"https://x.com/{id_parts[0]}/status/{id_parts[1]}"
        else:
            raise ValueError("Incorrect X (Twitter) ID!")

    def get_prefix(self):
        return "tx-"

    def get_name(self) -> str:
        return "twitter"

    def parse_url(self, url: str) -> typing.Optional[str]:
        match = self._URL_PATTERN.search(url)
        if not match:
            return None

        groups = match.groupdict()
        user = groups["user"]
        status_id = groups["status_id"]
        photo_id = groups["photo_id"]

        if photo_id:
            return f"{user}#{status_id}#{photo_id}"
        return f"{user}#{status_id}"


class DeviantArtOrigin(AbstractOriginType):
    _URL_PATTERN = re.compile(
        r"https?://(?:www\.)?deviantart\.com/(?P<user>[^/]+)/art/.*-(?P<content_id>\d+)/?$"
    )

    def generate_url(self, origin_content_id: Optional[str] = None):
        origin_content_id = self._validate_origin_id(origin_content_id)
        id_parts: list[str] = origin_content_id.split("#")
        if len(id_parts) == 2:
            return (
                f"https://www.deviantart.com/{id_parts[0]}/art/{id_parts[1]}"
            )
        else:
            raise ValueError("Incorrect DeviantArt content ID!")

    def parse_url(self, url: str) -> typing.Optional[str]:
        clean_url = url.split("?")[0]
        match = self._URL_PATTERN.search(clean_url)

        if not match:
            return None

        groups = match.groupdict()
        return f"{groups['user']}#{groups['content_id']}"

    def get_prefix(self):
        return "da-"

    def get_name(self) -> str:
        return "deviantart"


class TelegramMessenger(AbstractOriginType):
    _URL_PATTERN = re.compile(
        r"https://t\.me/(?P<user>[^/]+)/(?P<content_id>\d+)$"
    )

    def generate_url(self, origin_content_id: Optional[str] = None):
        origin_content_id = self._validate_origin_id(origin_content_id)
        id_parts: list[str] = origin_content_id.split("#")
        if len(id_parts) == 2:
            return f"https://t.me/{id_parts[0]}/{id_parts[1]}"
        else:
            raise ValueError("Incorrect Telegram post ID!")

    def parse_url(self, url: str) -> typing.Optional[str]:
        clean_url = url.split("?")[0]
        match = self._URL_PATTERN.search(clean_url)

        if not match:
            return None

        groups = match.groupdict()
        return f"{groups['user']}#{groups['content_id']}"

    def get_prefix(self):
        return "te-"

    def get_name(self) -> str:
        return "telegram"


ORIGIN_TYPE: dict[str, typing.Type[AbstractOriginType]] = {
    "derpibooru": DerpibooruOrigin,
    "ponybooru": PonybooruOrigin,
    "twibooru": TwibooruOrigin,
    "e621": E621Origin,
    "e6ai": E6AIOrigin,
    "furbooru": FurbooruOrigin,
    "tantabus": TantabusAIOrigin,
    "furaffinity": FurAffinityOrigin,
    "twitter": TwitterXOrigin,
    "civit-ai": CivitAIOrigin,
    "deviantart": DeviantArtOrigin,
    "deviant-art": DeviantArtOrigin,
    "telegram": TelegramMessenger,
}


def get_origin_type(
    origin_name: str,
) -> typing.Optional[typing.Type[AbstractOriginType]]:
    """
    Returns concrete OriginType, or None for unknown origin
    """
    return ORIGIN_TYPE.get(origin_name, None)
