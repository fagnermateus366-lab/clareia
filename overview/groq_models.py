"""Text models documented for Groq's Free plan, intersected with its live API.

The Models API has no price/account-plan field. Never treat every returned model
as free, and never auto-select a replacement. This list was checked 2026-10-19:
https://console.groq.com/docs/rate-limits (Free Plan Limits).
The same IDs can be billed on a paid organization; the key must belong to Free.
"""
FREE_TEXT_MODELS={
    'openai/gpt-oss-20b':'GPT OSS 20B',
    'openai/gpt-oss-120b':'GPT OSS 120B',
    'qwen/qwen3.8-27b':'Qwen 3.8 27B',
}
BASE_URL='https://api.groq.com/openai/v1'


def available(model):
    return model.get('id') in FREE_TEXT_MODELS and model.get('active',True) is True
