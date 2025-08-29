import asyncio
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.db import AsyncSessionLocal
from app.domain.models import Track

SAMPLES = [
    {"id":"mock:track:1","title":"Levitating","artist":"Dua Lipa","duration_ms":203000},
    {"id":"mock:track:2","title":"Blinding Lights","artist":"The Weeknd","duration_ms":200000},
    {"id":"mock:track:3","title":"Pepas","artist":"Farruko","duration_ms":269000},
    {"id":"mock:track:4","title":"Titi Me Preguntó","artist":"Bad Bunny","duration_ms":240000},
    {"id":"mock:track:5","title":"Anti-Hero","artist":"Taylor Swift","duration_ms":201000},
    {"id":"mock:track:6","title":"As It Was","artist":"Harry Styles","duration_ms":168000},
    {"id":"mock:track:7","title":"Dance Monkey","artist":"Tones and I","duration_ms":209000},
    {"id":"mock:track:8","title":"Happier Than Ever","artist":"Billie Eilish","duration_ms":298000},
    {"id":"mock:track:9","title":"bad guy","artist":"Billie Eilish","duration_ms":194000},
    {"id":"mock:track:10","title":"One Kiss","artist":"Calvin Harris & Dua Lipa","duration_ms":213000},
]

#add tracks to the database
async def main():
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        existing = (await session.execute(select(Track))).scalars().first()
        if existing:
            print("Tracks already seeded"); return
        for t in SAMPLES:
            session.add(Track(**t))
        await session.commit()
        print(f"Seeded {len(SAMPLES)} tracks ✅")

#avoid running this script if imported
if __name__ == "__main__":
    asyncio.run(main())
