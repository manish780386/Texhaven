"""URL extraction and static URL risk signals."""
import ipaddress
import re
from urllib.parse import urlparse

URL_RE = re.compile(
    r"(?i)\b((?:https?://|www\.)[^\s<>\"']+|(?:[a-z0-9-]+\.)+(?:com|net|org|in|co|io|xyz|top|click|link|ly|me|info|biz|ru|tk|ml|ga|cf|gq|site|online|shop|live|support|app|dev|icu|buzz|zip|cyou|sbs)(?:/[^\s<>\"']*)?)"
)
SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "rb.gy", "shorturl.at",
    "ow.ly", "tiny.cc", "rebrand.ly", "bit.do", "s.id", "t.ly", "buff.ly", "lnkd.in",
}
BAD_TLDS = {"xyz", "top", "click", "tk", "ml", "ga", "cf", "gq", "zip", "icu", "buzz", "cyou", "sbs", "work", "rest"}
BRANDS = {
    "paypal": ["paypal.com"], "amazon": ["amazon.com", "amazon.in", "amazon.co.uk", "amzn.to"],
    "google": ["google.com", "goo.gl"], "apple": ["apple.com", "icloud.com"],
    "microsoft": ["microsoft.com", "live.com", "office.com"], "netflix": ["netflix.com"],
    "facebook": ["facebook.com", "fb.com"], "instagram": ["instagram.com"],
    "whatsapp": ["whatsapp.com", "wa.me"], "paytm": ["paytm.com"], "phonepe": ["phonepe.com"],
    "fedex": ["fedex.com"], "dhl": ["dhl.com"], "usps": ["usps.com"], "irs": ["irs.gov"],
    "binance": ["binance.com"], "coinbase": ["coinbase.com"], "dropbox": ["dropbox.com"],
    "hdfc": ["hdfcbank.com"], "icici": ["icicibank.com"], "sbi": ["sbi.co.in", "onlinesbi.sbi"],
    "chase": ["chase.com"], "wellsfargo": ["wellsfargo.com"], "hsbc": ["hsbc.com"],
}
_LEET = str.maketrans("01345$", "oleass")


def extract_urls(text: str) -> list[str]:
    seen, out = set(), []
    for m in URL_RE.finditer(text):
        u = m.group(1).rstrip(".,;:!?)]}'\"")
        if m.start() > 0 and text[m.start() - 1] == "@":
            continue  # domain part of an email address, not a link
        if u.lower() not in seen:
            seen.add(u.lower())
            out.append(u)
    return out[:10]


def _lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _brand_lookalike(host: str):
    for token in re.split(r"[^a-z0-9]+", host):
        if not token:
            continue
        norm = token.translate(_LEET)
        for brand, legit in BRANDS.items():
            matches = norm == brand or (len(brand) >= 5 and (brand in norm or _lev(norm, brand) <= 1))
            if matches and not any(host == d or host.endswith("." + d) for d in legit):
                return brand
    return None


def analyze(url: str) -> dict:
    """Returns {'url', 'host', 'signals': [(code, weight, label)]}."""
    raw = url if "://" in url else "http://" + url
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    signals: list[tuple[str, int, str]] = []
    if not host:
        return {"url": url, "host": "", "signals": signals}

    try:
        ipaddress.ip_address(host)
        signals.append(("url_ip_host", 35, "Link points to a raw IP address"))
    except ValueError:
        pass
    if host in SHORTENERS:
        signals.append(("url_shortener", 20, "Link is shortened, so the real destination is hidden"))
    if "xn--" in host:
        signals.append(("url_punycode", 30, "Link uses look-alike international characters"))
    if "@" in (parsed.netloc or ""):
        signals.append(("url_userinfo", 35, "Link hides its real destination behind an @ sign"))
    if host.rsplit(".", 1)[-1] in BAD_TLDS:
        signals.append(("url_bad_tld", 20, "Link uses a domain ending often abused by scammers"))
    if host.count(".") >= 4:
        signals.append(("url_subdomains", 15, "Link has an unusually long chain of subdomains"))
    if parsed.scheme == "http":
        signals.append(("url_no_https", 8, "Link is not encrypted (http)"))
    brand = _brand_lookalike(host)
    if brand:
        signals.append(("url_brand_lookalike", 45, f"Link imitates {brand.title()} but is not its official site"))
    return {"url": url, "host": host, "signals": signals}
