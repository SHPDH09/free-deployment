import httpx

from app.config import settings


class CloudflareService:
    BASE_URL = "https://api.cloudflare.com/client/v4"

    @staticmethod
    def is_configured() -> bool:
        return bool(settings.CLOUDFLARE_API_TOKEN and settings.CLOUDFLARE_ZONE_ID)

    @staticmethod
    async def create_dns_record(domain: str, record_type: str, content: str, proxied: bool = True) -> dict | None:
        if not CloudflareService.is_configured():
            return None

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CloudflareService.BASE_URL}/zones/{settings.CLOUDFLARE_ZONE_ID}/dns_records",
                headers={
                    "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "type": record_type,
                    "name": domain,
                    "content": content,
                    "proxied": proxied,
                },
            )
            if response.status_code in (200, 201):
                return response.json().get("result")
            return None

    @staticmethod
    async def _query_txt(name: str) -> list[str]:
        records: list[str] = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://dns.google/resolve",
                    params={"name": name, "type": "TXT"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    for answer in data.get("Answer", []):
                        records.append(answer.get("data", "").strip('"'))
        except Exception:
            pass
        return records

    @staticmethod
    async def verify_domain(domain: str, expected_value: str, record_type: str = "TXT") -> bool:
        txt_names = [f"_deploystack.{domain}", domain]
        for name in txt_names:
            records = await CloudflareService._query_txt(name)
            for record in records:
                if expected_value in record:
                    return True
        return False

    @staticmethod
    def get_dns_instructions(domain: str, verification_token: str, platform_domain: str) -> list[dict]:
        return [
            {
                "type": "CNAME",
                "name": domain,
                "value": f"cname.{platform_domain}",
                "purpose": "Point domain to platform",
            },
            {
                "type": "TXT",
                "name": f"_deploystack.{domain}",
                "value": verification_token,
                "purpose": "Verify domain ownership",
            },
        ]
