from thefuzz import process

from ..models import Domain


def search_domains(keywords: list[str], limit: int = 200) -> list[str]:
    domains = (domain.url for domain in Domain.select(Domain.url))
    extract_result = process.extract(" ".join(keywords), domains, limit=limit)
    return [domain for domain, _score in sorted(extract_result, key=lambda x: x[1], reverse=True)]
