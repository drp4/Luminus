"""一键测试 Children Growth OS 完整链路"""
import httpx, asyncio, sys, uuid
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000/api/v1"


async def main():
    async with httpx.AsyncClient(timeout=90) as c:
        # 1. 创建孩子
        r = await c.post(f"{BASE}/children", json={"nickname": "小明", "age": 9, "grade": "3年级"})
        assert r.status_code == 200, f"创建失败: {r.text}"
        child_id = r.json()["id"]
        print(f"1. 创建孩子: {child_id}\n")

        # 2. 日常聊天
        r = await c.post(f"{BASE}/chat", json={"child_id": child_id, "message": "你好！我叫小明，我最喜欢恐龙和太空了！"})
        assert r.status_code == 200, f"聊天失败: {r.text}"
        d1 = r.json()
        print(f"2. 聊天 ({r.elapsed.total_seconds():.1f}s)")
        print(f"   {d1['message'][:120]}...\n")

        # 3. 教育提问
        r = await c.post(f"{BASE}/chat", json={
            "child_id": child_id,
            "message": "为什么恐龙会灭绝？",
            "history": [
                {"role": "user", "content": "你好！我最喜欢恐龙和太空了！"},
                {"role": "assistant", "content": d1["message"]},
            ],
        })
        assert r.status_code == 200, f"教学失败: {r.text}"
        d2 = r.json()
        print(f"3. 教学 ({r.elapsed.total_seconds():.1f}s)")
        print(f"   {d2['message'][:120]}...\n")

        # 4. 等后台记忆写入
        print("4. 等待记忆提取...")
        await asyncio.sleep(5)

        # 5. 查看数据库
        from services.database import get_session_ctx
        from sqlalchemy import text

        async with get_session_ctx() as s:
            cid_hex = uuid.UUID(child_id).hex

            snaps = (await s.execute(
                text("SELECT * FROM profile_snapshots WHERE child_id=:cid"), {"cid": cid_hex}
            )).fetchall()
            print(f"5. Profile Snapshot: {'已创建' if snaps else '无'}")

            interests = (await s.execute(
                text("SELECT topic, weight, trend FROM interest_models WHERE child_id=:cid"), {"cid": cid_hex}
            )).fetchall()
            print(f"6. 兴趣发现: {len(interests)} 个")
            for row in interests:
                m = row._mapping
                print(f"     {m['topic']} (weight={m['weight']:.1f}, {m['trend']})")

            mems = (await s.execute(
                text("SELECT memory_type, importance, content FROM long_memories WHERE child_id=:cid"), {"cid": child_id}
            )).fetchall()
            print(f"7. 长期记忆: {len(mems)} 条")
            for row in mems:
                m = row._mapping
                print(f"     [{m['memory_type']}] imp={m['importance']:.1f} {m['content'][:80]}")

        print("\n=== 全部通过 ===")


if __name__ == "__main__":
    asyncio.run(main())
