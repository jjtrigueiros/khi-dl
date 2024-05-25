import pytest
from yarl import URL
import aiohttp
from khi_dl.main import KhiAlbum


@pytest.mark.asyncio
async def test_khi_album_from_khi_url(mock_khinsider):
    async with aiohttp.ClientSession() as session:
        album = await KhiAlbum.from_khi_url(URL("http://example.com/album1"), session)

    assert album.name == "Sample Album"
    assert len(album.tracks) == 2

    assert album.tracks[0].disc == 1
    assert album.tracks[0].number == 2
    assert album.tracks[0].name == "Track 1"

    assert album.tracks[1].disc == 3
    assert album.tracks[1].number == 4
    assert album.tracks[1].name == "Track 2"
