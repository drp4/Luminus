"""查询孩子档案"""
import asyncio, sys

sys.stdout.reconfigure(encoding="utf-8")
from services.database import get_session_ctx
from sqlalchemy import text


async def main(nickname: str | None = None):
    async with get_session_ctx() as s:
        # 所有孩子
        if nickname:
            children = (await s.execute(
                text("SELECT * FROM children WHERE nickname=:n"), {"n": nickname}
            )).fetchall()
        else:
            children = (await s.execute(text("SELECT * FROM children"))).fetchall()

        for c in children:
            m = c._mapping
            child_uuid = m["id"]  # CHAR(32) 无连字符

            # 拼出带连字符的版本给 long_memories
            uuid_with_dash = f"{child_uuid[:8]}-{child_uuid[8:12]}-{child_uuid[12:16]}-{child_uuid[16:20]}-{child_uuid[20:]}"

            print(f"  {m['nickname']} | {m['age']}岁 | {m['grade']} | id={child_uuid[:12]}...")

            # Profile Snapshot
            snap = (await s.execute(
                text("SELECT * FROM profile_snapshots WHERE child_id=:cid"), {"cid": child_uuid}
            )).first()
            if snap:
                sm = snap._mapping
                print(f"    画像: 好奇={sm['curiosity_score']} 表达={sm['expression_score']} "
                      f"思考={sm['thinking_score']} 风格={sm['learning_style']}")

            # Interests
            interests = (await s.execute(
                text("SELECT topic, weight, trend FROM interest_models WHERE child_id=:cid"),
                {"cid": child_uuid},
            )).fetchall()
            if interests:
                topics = ", ".join(f"{r._mapping['topic']}({r._mapping['weight']:.1f}/{r._mapping['trend']})" for r in interests)
                print(f"    兴趣: {topics}")

            # Long Memories
            mems = (await s.execute(
                text("SELECT memory_type, importance, content FROM long_memories WHERE child_id=:cid"),
                {"cid": uuid_with_dash},
            )).fetchall()
            if mems:
                print(f"    记忆: {len(mems)} 条")
                for mem in mems:
                    mm = mem._mapping
                    print(f"      [{mm['memory_type']}] imp={mm['importance']:.1f} {mm['content'][:80]}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(name))
