from urllib.parse import urlparse


def detect_sql_dialect(conn_url: str) -> str:
    url = urlparse(conn_url)
    if '+' in url.scheme:
        return url.scheme.split('+')[0]
    else:
        return url.scheme
