# tests/test_khitrack.py
import pytest
import aiohttp


@pytest.mark.asyncio
async def test_khi_track_get_source(khi_track, mock_khinsider):
    async with aiohttp.ClientSession() as session:
        source_url = await khi_track.get_source(session)

    assert str(source_url) == "http://example.com/audio.mp3"


@pytest.mark.asyncio
async def test_khi_track_get_audio_stream(mock_khinsider, khi_track):
    async with aiohttp.ClientSession() as session:
        chunks = [chunk async for chunk in khi_track.get_audio_stream(session)]

    assert chunks == [b"1234567890"]


@pytest.mark.asyncio
async def test_khi_track_save_to_file(khi_track, tmp_path, mock_khinsider):
    filename = tmp_path / "track1.mp3"

    async with aiohttp.ClientSession() as session:
        await khi_track.save_to_file(session, filename)

    assert filename.exists()
    assert filename.read_bytes() == b"1234567890"


def test_khi_track_generate_filename(khi_track):
    assert khi_track.generate_filename() == "1-01 Track 1.mp3"
