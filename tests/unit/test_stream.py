import pytest

from stream.inputstream import InputStream
from stream.outputstream import AddressableOutputStream, OutputStream


def test_stream_round_trip_aligned_values():
    output = OutputStream()
    output.put_u16(0x1234)
    output.put_u16(0x5678)
    output.put_u32(0x89ABCDEF)

    stream = InputStream(output.get_buffer())
    assert stream.get_u16() == 0x1234
    assert stream.get_u16() == 0x5678
    assert stream.get_u32() == 0x89ABCDEF
    assert stream.is_eos()


def test_stream_round_trip_unchecked_bytes():
    output = OutputStream()
    output.put_u8(0x12)
    output.put_u16(0x3456)
    output.put_u32(0x789ABCDE)

    stream = InputStream(output.get_buffer(), check_alignment=False)
    assert stream.get_u8() == 0x12
    assert stream.get_u16() == 0x3456
    assert stream.get_u32() == 0x789ABCDE


def test_stream_peek_and_unget():
    stream = InputStream(bytearray(b"\x01\x02\x03\x04"), check_alignment=False)

    assert stream.peek_u8() == 0x01
    assert stream.get_u8() == 0x01
    stream.unget_u8()
    assert stream.get_u8() == 0x01
    assert stream.get_u16() == 0x0302


def test_stream_rejects_misaligned_reads():
    stream = InputStream(bytearray(b"\x00\x01\x02\x03"))
    assert stream.get_u8() == 0x00

    with pytest.raises(RuntimeError, match="half-word aligned"):
        stream.get_u16()

    with pytest.raises(RuntimeError, match="word aligned"):
        stream.get_u32()


def test_stream_rejects_partial_reads():
    with pytest.raises(RuntimeError, match="Unexpected end of stream"):
        InputStream(bytearray(b"\x01"), check_alignment=False).get_u16()

    with pytest.raises(RuntimeError, match="Unexpected end of stream"):
        InputStream(bytearray(b"\x01\x02\x03"), check_alignment=False).get_u32()

    with pytest.raises(RuntimeError, match="Unexpected end of stream"):
        InputStream(bytearray(b"\x01"), check_alignment=False).peek_u16()


def test_stream_from_string():
    stream = InputStream.from_string("ABC")
    assert stream.get_char() == "A"
    assert stream.get_char() == "B"
    assert stream.get_char() == "C"
    assert stream.is_eos()


def test_addressable_output_stream():
    stream = AddressableOutputStream(base_addr=0x8000000)
    stream.put_u32(0x12345678)
    assert stream.current_addr() == 0x8000004
    assert stream.size() == 4
