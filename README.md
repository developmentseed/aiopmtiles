# aiopmtiles

<p align="center">
  <em>Async Version of Python PMTiles Reader.</em>
</p>
<p align="center">
  <a href="https://github.com/developmentseed/aiopmtiles/actions?query=workflow%3ACI" target="_blank">
      <img src="https://github.com/developmentseed/aiopmtiles/workflows/CI/badge.svg" alt="Test">
  </a>
  <a href="https://codecov.io/gh/developmentseed/aiopmtiles" target="_blank">
      <img src="https://codecov.io/gh/developmentseed/aiopmtiles/branch/main/graph/badge.svg" alt="Coverage">
  </a>
  <a href="https://pypi.org/project/aiopmtiles" target="_blank">
      <img src="https://img.shields.io/pypi/v/aiopmtiles?color=%2334D058&label=pypi%20package" alt="Package version">
  </a>
  <a href="https://pypistats.org/packages/aiopmtiles" target="_blank">
      <img src="https://img.shields.io/pypi/dm/aiopmtiles.svg" alt="Downloads">
  </a>
  <a href="https://github.com/developmentseed/aiopmtiles/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/github/license/developmentseed/aiopmtiles.svg" alt="Downloads">
  </a>
</p>

---

**Documentation**:

**Source Code**: <a href="https://github.com/developmentseed/aiopmtiles" target="_blank">https://github.com/developmentseed/aiopmtiles</a>

---

## Installation

```bash
$ pip install pip -U

# From Pypi
$ pip install aiopmtiles

# Or from source
$ pip install git+http://github.com/developmentseed/aiopmtiles
```

## Example

```python

from aiopmtiles import Reader

async with Reader("https://r2-public.protomaps.com/protomaps-sample-datasets/cb_2018_us_zcta510_500k.pmtiles") as src:
    data = await src.get_tile(0, 0, 0)
```

## Contribution & Development

See [CONTRIBUTING.md](https://github.com/developmentseed/aiopmtiles/blob/main/CONTRIBUTING.md)

## Authors

See [contributors](https://github.com/developmentseed/aiopmtiles/graphs/contributors)

## Changes

See [CHANGES.md](https://github.com/developmentseed/aiopmtiles/blob/main/CHANGES.md).

## License

See [LICENSE](https://github.com/developmentseed/aiopmtiles/blob/main/LICENSE)
