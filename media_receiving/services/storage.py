from datetime import datetime
from pathlib import Path
from django.conf import settings
from medialib.models import Content, ContentOrigin
from base.shared_knowledge.origin import get_origin_type, AbstractOriginType
from image_processing.services.representations import Representation
from typing import Optional, Type
import base64


def generate_representation_path(
    content: Content,
    origin_name: str,
    origin_id: str,
    date_now: datetime,
    compatibility_level: int,
    width: int | None,
    height: int | None,
    suffix: str,
) -> Path:
    origin_class: Optional[Type[AbstractOriginType]] = get_origin_type(
        origin_name
    )

    src_hash_b64 = base64.urlsafe_b64encode(content.source_hash).decode(
        "utf-8"
    )[:12]

    base_name = f"mlid{content.id} {src_hash_b64}"
    if origin_class and origin_id:
        safe_id = origin_class.filesystem_safe_content_id(origin_id)
        base_name += f" {origin_class().get_prefix()}{safe_id}"

    size_str = f"_{width}x{height}" if width and height else ""
    filename = f"{base_name}_cl{compatibility_level}{size_str}{suffix}"

    relative_path = Path(date_now.strftime("%Y/%m/%d")) / filename
    return relative_path


def finalize_representation_storage(
    current_file_path: Path,
    rel_path: Path,
) -> Path:
    final_abs_path = Path(settings.MEDIALIB_COLLECTION_ROOT) / rel_path

    final_abs_path.parent.mkdir(parents=True, exist_ok=True)

    current_file_path.move(final_abs_path)

    return Path(settings.MEDIALIB_COLLECTION_DIRECTORY) / rel_path


def move_representations(
    content: Content, representations: list[Representation]
) -> list[Representation]:
    """
    Moves representations to collection firectory with generated name
    and returns representations with new name
    """
    origin = ContentOrigin.objects.filter(content=content).first()
    origin_name = origin.name if origin else ""
    origin_id = origin.origin_id if origin else ""
    date_now: datetime = datetime.now()
    processed_representations: list[Representation] = []

    for ml_repr in representations:
        new_relative_path = generate_representation_path(
            content,
            origin_name,
            origin_id,
            date_now,
            ml_repr.compatibility_level,
            ml_repr.width,
            ml_repr.height,
            ml_repr.file_path.suffix,
        )
        new_path = finalize_representation_storage(
            ml_repr.file_path, new_relative_path
        )
        processed_representations.append(
            Representation(
                ml_repr.compatibility_level,
                new_path,
                ml_repr.width,
                ml_repr.height,
                ml_repr.repr_type,
                ml_repr._format,
                ml_repr.repr_hash,
                ml_repr.codec_string,
            )
        )
    return processed_representations
