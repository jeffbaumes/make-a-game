"""
Entrypoint module, in case you use `python -mmake_a_game`.


Why does this file exist, and why __main__? For more info, read:

- https://www.python.org/dev/peps/pep-0338/
- https://docs.python.org/2/using/cmdline.html#cmdoption-m
- https://docs.python.org/3/using/cmdline.html#cmdoption-m
"""
from make_a_game.cli import main

if __name__ == "__main__":
    main()
