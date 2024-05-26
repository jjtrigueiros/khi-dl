import asyncio
import typing as t
from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from yarl import URL


@dataclass
class KhiTrack:
    khi_page: URL
    name: str
    number: int
    disc: int | None = None

    async def get_source(self, session: aiohttp.ClientSession) -> URL:
        async with session.get(self.khi_page) as response:
            khi_track_page = await response.text()
        return URL(
            BeautifulSoup(khi_track_page, features="html.parser")
            .find(id="audio")
            .get("src")
        )

    async def get_audio_stream(
        self, session: aiohttp.ClientSession
    ) -> t.AsyncIterator[bytes]:
        audio_src = await self.get_source(session=session)
        async with session.get(audio_src) as response:
            async for chunk in response.content.iter_chunked(1024):
                yield chunk

    async def save_to_file(
        self, session: aiohttp.ClientSession, filename: Path
    ) -> None:
        async with aiofiles.open(filename, "wb") as file:
            async for chunk in self.get_audio_stream(session=session):
                await file.write(chunk)
        logger.info(f"saved: {filename}")

    def generate_filename(self) -> str:
        # assuming disc is not numbered as "0"...
        identifier = (
            f"{self.disc}-{self.number:02d}" if self.disc else f"{self.number:02d}"
        )
        return f"{identifier} {self.name}.mp3"


@dataclass
class KhiAlbum:
    name: str
    tracks: list[KhiTrack]

    @classmethod
    async def from_khi_url(cls, khi_url: URL, session: aiohttp.ClientSession):
        async with session.get(khi_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, features="html.parser")
            album_name = soup.find("h2").text
            khi_domain = URL(f"{khi_url.scheme}://{khi_url.host}")
            tracks = list(cls._parse_soup_for_tracks(soup, khi_domain))
        return cls(album_name, tracks)

    @staticmethod
    def _parse_soup_for_tracks(soup: BeautifulSoup, host: URL) -> t.Iterator[KhiTrack]:
        # tt: track table
        tt_rows = soup.find(id="songlist").findChildren(name=["tr"])
        tt_header = tt_rows[0]
        tt_track_rows = tt_rows[1:-1]
        # tt_footer = tt_rows[-1]

        tt_column_names = [col.text for col in tt_header.findChildren("th")]
        tt_column_map = {col: pos for pos, col in enumerate(tt_column_names)}
        tt_cd_col = tt_column_map.get("CD", None)
        tt_number_col = tt_column_map["#"]
        tt_name_col = tt_column_map["Song Name"]

        for track_row in tt_track_rows:
            cells = track_row.find_all("td")
            yield KhiTrack(
                khi_page=URL(f"{host}{cells[tt_name_col].find('a').get('href')}"),
                name=cells[tt_name_col].text,
                number=int(cells[tt_number_col].text.rstrip(".")),
                disc=int(cells[tt_cd_col].text.rstrip("."))
                if tt_cd_col is not None
                else None,
            )


async def main(album_urls: list[URL], dl_dir: Path):
    connector = aiohttp.TCPConnector(force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(KhiAlbum.from_khi_url(khi_url=url, session=session))
                for url in album_urls
            ]

        albums: list[KhiAlbum] = [task.result() for task in tasks]

        for album in albums:
            logger.info(f"{album.name}: {len(album.tracks)} tracks")

        dl_dir.mkdir(parents=False, exist_ok=True)

        async with asyncio.TaskGroup() as tg:
            for album in albums:
                album_path = dl_dir / album.name
                album_path.mkdir(exist_ok=True)
                for track in album.tracks:
                    track_file = album_path / track.generate_filename()
                    if track_file.exists():
                        logger.warning(f"file already exists, skipping: {track_file}")
                        continue
                    tg.create_task(
                        track.save_to_file(session=session, filename=track_file)
                    )


if __name__ == "__main__":
    sources_file = Path("./example_sources.txt")
    with sources_file.open() as f:
        album_urls = [URL(line) for line in f.read().splitlines()]
    dl_dir = Path("./downloads")

    asyncio.run(
        main(
            album_urls=album_urls,
            dl_dir=dl_dir,
        )
    )
