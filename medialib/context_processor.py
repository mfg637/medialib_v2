from .models import COMPATIBILITY_LEVEL_DICT
import json

DEFAULT_LEVEL = 2


def cl_processor(request):
    filtered_choices = {
        k: v for k, v in COMPATIBILITY_LEVEL_DICT.items() if k > 0
    }
    return {
        "CL_CHOICES_JSON": json.dumps(filtered_choices),
        "CURRENT_CL": int(request.session.get("clevel", DEFAULT_LEVEL)),
        "DEFAULT_LEVEL": DEFAULT_LEVEL,
    }
