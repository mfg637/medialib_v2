import typing
import abc


class AbstractOriginType(abc.ABC):
    @abc.abstractmethod
    def generate_url(self, origin_content_id: str) -> str:
        pass

    @abc.abstractmethod
    def get_prefix(self) -> str:
        pass

    @staticmethod
    def filesystem_safe_content_id(origin_content_id: str):
        return origin_content_id.replace("#", "_")


class SimpleOriginType(AbstractOriginType):
    @abc.abstractmethod
    def _get_template_string(self) -> str:
        pass

    def generate_url(self, origin_content_id):
        return self._get_template_string().format(origin_content_id)


class DerpibooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://derpibooru.org/images/{}"

    def get_prefix(self):
        return "db"


class PonybooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://ponybooru.org/images/{}"

    def get_prefix(self):
        return "pb"


class TwibooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://twibooru.org/{}"

    def get_prefix(self):
        return "tb"


class E621Origin(SimpleOriginType):
    def _get_template_string(self):
        return "https://e621.net/posts/{}"

    def get_prefix(self):
        return "ef"


class FurbooruOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://furbooru.org/images/{}"

    def get_prefix(self):
        return "fb"


class TantabusAIOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://tantabus.ai/images/{}"

    def get_prefix(self):
        return "ta"


class CivitAIOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://civitai.com/images/{}"

    def get_prefix(self):
        return "ca"


class FurAffinityOrigin(SimpleOriginType):
    def _get_template_string(self):
        return "https://www.furaffinity.net/view/{}/"

    def get_prefix(self):
        return "fa"


class TwitterXOrigin(AbstractOriginType):
    def generate_url(self, origin_content_id):
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


ORIGIN_TYPE: dict[str, typing.Type[AbstractOriginType]] = {
    "derpibooru": DerpibooruOrigin,
    "ponybooru": PonybooruOrigin,
    "twibooru": TwibooruOrigin,
    "e621": E621Origin,
    "furbooru": FurbooruOrigin,
    "tantabus": TantabusAIOrigin,
    "furaffinity": FurAffinityOrigin,
    "twitter": TwitterXOrigin,
    "civit ai": CivitAIOrigin,
}


def get_origin_type(
    origin_name: str,
) -> typing.Optional[typing.Type[AbstractOriginType]]:
    """
    Returns concrete OriginType, or None for unknown origin
    """
    return ORIGIN_TYPE.get(origin_name, None)
