# SPDX-License-Identifier: MIT

from struct import unpack_from

try:
    from nacl.secret import SecretBox

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

except ImportError:

    def no_nacl(*args, **kwargs):
        raise RuntimeError("PyNaCl library needed in order to use voice")

    strip_header_ext = no_nacl
    decrypt_xsalsa20_poly1305 = no_nacl
    decrypt_xsalsa20_poly1305_suffix = no_nacl
    decrypt_xsalsa20_poly1305_lite = no_nacl
