"""Shared timing/continuity rules for documentary collage visuals and narration."""
import json

VERSION='collage-comfort-v2-layers'


def passage_duration(effect,seconds):
    if effect=='nenhuma':return 0.
    minimum=1.2 if effect in ('padrao','dissolver') else 1.5 if effect=='papel_amassado' else 1.4
    return max(minimum,seconds)


def context_identity(beat):
    # Phrase numbers/timings are not visual changes. Stable slots also tolerate
    # a model returning the same figures in a different list order.
    elements=sorted(json.dumps(e,ensure_ascii=False,sort_keys=True) for e in beat['elementos'])
    return (beat['titulo'],beat['composicao'],tuple(elements))
