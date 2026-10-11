# Contributing

Thanks for helping! This project only exists because one person had a Switch save they wanted
on PC. Every report makes it more reliable for the next person.

## Reporting results

Open an issue with the **Conversion report** template, whether it worked or not. Include:

- the output of `python -m sot_save_converter info <switch file> <converted file>`;
- the language of each game version, and where you got the PC game (Steam, Ubisoft, …);
- what you checked in game, and what (if anything) was wrong.

**Save files:** don't attach saves to public issues unless you are fine with them being public.
If a save is needed to reproduce a bug, say so in the issue and we'll find a way.

## Development

Python 3.8+, standard library only.

```bash
python -m unittest discover -s tests -v
```

The tests use **synthetic** saves built by `tests/synthetic.py`. Real saves must never be
committed (`.gitignore` blocks the usual names). Read `docs/FORMAT.md` before changing the
converter, and update it when you learn something new about the format.

## Help wanted

- **PC → Switch** conversion.
- Testing with other languages, other game versions, the Ubisoft Connect / GOG versions,
  Switch 2 and Steam Deck.

## Pull requests

Keep changes focused, add or update tests, and describe how you tested with real saves (without
attaching them).

This project only works with save files. Please don't submit anything that decompiles, patches
or redistributes the game, its executable or its assets.
