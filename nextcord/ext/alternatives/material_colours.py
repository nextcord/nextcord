from nextcord.colour import Colour


MDIO_COLOURS = {
    "400": {
        "red": 0xEF534E,
        "pink": 0xEC407E,
        "purple": 0xAB47BC,
        "deep_purple": 0x7E56C1,
        "indigo": 0x5C6BC0,
        "blue": 0x42A5F5,
        "light_blue": 0x29B6F6,
        "cyan": 0x26C6DA,
        "teal": 0x26A69A,
        "green": 0x66BB6A,
        "light_green": 0x9CCC65,
        "lime": 0xD4E157,
        "yellow": 0xFFEE58,
        "amber": 0xFFCA28,
        "orange": 0xFFA726,
        "deep_orange": 0xFF7043,
    }
}

for shade, colours in MDIO_COLOURS.items():
    for name, value in colours.items():
        delegate = lambda cls, value=value: cls(value)
        setattr(Colour, "material_{0}_{1}".format(shade, name), classmethod(delegate))
