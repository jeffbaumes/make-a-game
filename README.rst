========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |coveralls| |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/make-a-game/badge/?style=flat
    :target: https://readthedocs.org/projects/make-a-game
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/jeffbaumes/make-a-game.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/jeffbaumes/make-a-game

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/jeffbaumes/make-a-game?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/jeffbaumes/make-a-game

.. |requires| image:: https://requires.io/github/jeffbaumes/make-a-game/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/jeffbaumes/make-a-game/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/jeffbaumes/make-a-game/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/jeffbaumes/make-a-game

.. |codecov| image:: https://codecov.io/github/jeffbaumes/make-a-game/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/jeffbaumes/make-a-game

.. |version| image:: https://img.shields.io/pypi/v/make-a-game.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/make-a-game

.. |commits-since| image:: https://img.shields.io/github/commits-since/jeffbaumes/make-a-game/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/jeffbaumes/make-a-game/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/make-a-game.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/make-a-game

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/make-a-game.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/make-a-game

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/make-a-game.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/make-a-game


.. end-badges

Make a game!

* Free software: MIT license

Installation
============

::

    pip install make-a-game

Documentation
=============

https://make-a-game.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
