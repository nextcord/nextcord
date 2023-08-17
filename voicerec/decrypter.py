"""
The MIT License (MIT)

:copyright: (c) 2021-present Tag-Epic
:copyright: (c) 2021-present Nextcord Developers

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from nacl.secret import SecretBox
from struct import unpack_from

def strip_header_ext(data):
    if data[0] == 0xBE and data[1] == 0xDE and len(data) > 4:
        _, length = unpack_from(">HH", data)
        offset = 4 + length * 4
        data = data[offset:]
    return data

def decrypt_xsalsa20_poly1305(secret_key, header, data):
    box = SecretBox(bytes(secret_key))

    nonce = bytearray(24)
    nonce[:12] = header

    return strip_header_ext(box.decrypt(bytes(data), bytes(nonce)))

def decrypt_xsalsa20_poly1305_suffix(secret_key, _, data):
    box = SecretBox(bytes(secret_key))

    nonce_size = SecretBox.NONCE_SIZE
    nonce = data[-nonce_size:]

    return strip_header_ext(box.decrypt(bytes(data[:-nonce_size]), nonce))

def decrypt_xsalsa20_poly1305_lite(secret_key, _, data):
    box = SecretBox(bytes(secret_key))

    nonce = bytearray(24)
    nonce[:4] = data[-4:]
    data = data[:-4]

    return strip_header_ext(box.decrypt(bytes(data), bytes(nonce)))