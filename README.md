# bitovi_packs

Bitovi Custom Pack management functionality.

## Actions

### install
Use `bitovi_packs.install` instead of `packs.install` to enable pack dependencies.

`dependencies` are specified as an `array` in `pack.yml` like:
```yml
dependencies:
  - file:////opt/stackstorm/packs.dev/dependencies_test_parent # useful for local development
  - https://github.com/mickmcgrath13/dependencies_test_parent # dependencies from github
  - dependencies_test_parent # dependencies from the exchange index
```

### get_pack_dependencies
Returns the `dependencies` list from `pack.yml`