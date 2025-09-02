from configs.settings import settings

def score_to_status(score: float) -> str:
    if score >= settings.THREAT_SCORE_THRESHOLD_MALICIOUS:
        return "malicious"
    if score >= settings.THREAT_SCORE_THRESHOLD_SUSPICIOUS:
        return "suspicious"
    return "benign"
