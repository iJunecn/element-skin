from ..core import BaseDB
import time

class FallbackModule:
    def __init__(self, db: BaseDB):
        self.db = db

    async def list_endpoints(self) -> list[dict]:
        async with self.db.get_conn() as conn:
            async with conn.execute(
                """
                SELECT id, priority, session_url, account_url, services_url, cache_ttl, skin_domains,
                       enable_profile, enable_hasjoined, enable_whitelist, note
                FROM fallback_endpoints
                ORDER BY priority ASC, id ASC
                """
            ) as cur:
                rows = await cur.fetchall()
                return [
                    {
                        "id": r[0],
                        "priority": r[1],
                        "session_url": r[2],
                        "account_url": r[3],
                        "services_url": r[4],
                        "cache_ttl": r[5],
                        "skin_domains": r[6],
                        "enable_profile": bool(r[7]),
                        "enable_hasjoined": bool(r[8]),
                        "enable_whitelist": bool(r[9]),
                        "note": r[10],
                    }
                    for r in rows
                ]

    async def get_primary_endpoint(self) -> dict | None:
        endpoints = await self.list_endpoints()
        return endpoints[0] if endpoints else None

    async def save_endpoints(self, fallbacks: list[dict]):
        async with self.db.get_conn() as conn:
            async with conn.execute("SELECT id FROM fallback_endpoints") as cur:
                existing_ids = {row[0] for row in await cur.fetchall()}

            incoming_ids = {
                entry["id"] for entry in fallbacks if entry.get("id") is not None
            }
            for endpoint_id in existing_ids - incoming_ids:
                await conn.execute(
                    "DELETE FROM fallback_endpoints WHERE id=?", (endpoint_id,)
                )

            for idx, entry in enumerate(fallbacks, start=1):
                priority = idx
                session_url = entry["session_url"]
                account_url = entry["account_url"]
                services_url = entry["services_url"]
                cache_ttl = entry["cache_ttl"]
                skin_domains = entry.get("skin_domains", "")
                enable_profile = 1 if entry.get("enable_profile") else 0
                enable_hasjoined = 1 if entry.get("enable_hasjoined") else 0
                enable_whitelist = 1 if entry.get("enable_whitelist") else 0
                note = entry.get("note", "")

                if entry.get("id") is not None:
                    await conn.execute(
                        """
                        UPDATE fallback_endpoints
                        SET priority=?, session_url=?, account_url=?, services_url=?, cache_ttl=?, skin_domains=?,
                            enable_profile=?, enable_hasjoined=?, enable_whitelist=?, note=?
                        WHERE id=?
                        """,
                        (
                            priority,
                            session_url,
                            account_url,
                            services_url,
                            cache_ttl,
                            skin_domains,
                            enable_profile,
                            enable_hasjoined,
                            enable_whitelist,
                            note,
                            entry["id"],
                        ),
                    )
                else:
                    await conn.execute(
                        """
                        INSERT INTO fallback_endpoints (
                            priority, session_url, account_url, services_url, cache_ttl, skin_domains,
                            enable_profile, enable_hasjoined, enable_whitelist, note
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            priority,
                            session_url,
                            account_url,
                            services_url,
                            cache_ttl,
                            skin_domains,
                            enable_profile,
                            enable_hasjoined,
                            enable_whitelist,
                            note,
                        ),
                    )
            await conn.commit()
            
    async def collect_skin_domains(self) -> list[str]:
        async with self.db.get_conn() as conn:
            async with conn.execute(
                "SELECT skin_domains FROM fallback_endpoints WHERE skin_domains IS NOT NULL AND skin_domains != ''"
            ) as cur:
                rows = await cur.fetchall()
                # 对于每一个非空的 skin_domains 字段，按逗号分割并收集所有域名
                domains = []
                for row in rows:
                    raw = row[0]
                    if raw:
                        parts = [part.strip() for part in raw.split(",") if part.strip()]
                        domains.extend(parts)
                return domains
            
    # ========== Fallback Whitelist ==========

    async def add_whitelist_user(self, username: str, endpoint_id: int):
        created_at = int(time.time() * 1000)
        async with self.db.get_conn() as conn:
            await conn.execute(
                """
                INSERT OR IGNORE INTO whitelisted_users (username, endpoint_id, created_at)
                VALUES (?, ?, ?)
                """,
                (username, endpoint_id, created_at),
            )
            await conn.commit()

    async def remove_whitelist_user(
        self, username: str, endpoint_id: int
    ):
        async with self.db.get_conn() as conn:
            await conn.execute(
                "DELETE FROM whitelisted_users WHERE username=? AND endpoint_id=?",
                (username, endpoint_id),
            )
            await conn.commit()

    async def is_user_in_whitelist(
        self, username: str, endpoint_id: int
    ) -> bool:
        async with self.db.get_conn() as conn:
            query = (
                "SELECT 1 FROM whitelisted_users WHERE username=? COLLATE NOCASE AND endpoint_id=?"
            )
            params = (username, endpoint_id)
            async with conn.execute(query, params) as cur:
                row = await cur.fetchone()
                return row is not None

    async def list_whitelist_users(
        self, endpoint_id: int
    ) -> list[dict]:
        async with self.db.get_conn() as conn:
            query = (
                "SELECT username, created_at FROM whitelisted_users WHERE endpoint_id=? ORDER BY created_at DESC"
            )
            params = (endpoint_id,)
            async with conn.execute(query, params) as cur:
                rows = await cur.fetchall()
                return [{"username": r[0], "created_at": r[1]} for r in rows]
