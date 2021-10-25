"""An experiment that enables ``Message.__eq__``.

It compares the IDs of each ``Message``.

Example:

```py
>>> m1 == m1
True # Same IDs
>>> m1 == m2
False # Different IDs
```
"""

import nextcord


nextcord.Message.__eq__ = lambda s, o: isinstance(o, nextcord.Message) and s.id == o.id
