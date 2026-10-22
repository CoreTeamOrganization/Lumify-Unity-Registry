# Lumify Unity Registry

A Unity Package Manager scoped registry for the vendor packages [Lumify](https://github.com/CoreTeamOrganization/Lumify-Unity-SDK)
depends on that no public registry serves — today Google's Firebase packages, under their official names.

It holds metadata only. Each version's download points at the vendor's own file (for Firebase,
`https://dl.google.com/games/registry/unity/...`), so no vendor code is stored or redistributed here.

## Use

Lumify's Package Installer adds the registry for you. By hand, in `Packages/manifest.json`:

```json
"scopedRegistries": [
  {
    "name": "Lumify Registry",
    "url": "https://coreteamorganization.github.io/Lumify-Unity-Registry",
    "scopes": [ "com.google.firebase" ]
  }
]
```

Firebase App depends on the External Dependency Manager, which comes from OpenUPM
(`https://package.openupm.com`, scope `com.google.external-dependency-manager`).

## Packages

| Package | Versions |
|---|---|
| `com.google.firebase.app` | 12.9.0, 13.17.0 |
| `com.google.firebase.analytics` | 12.9.0, 13.17.0 |
| `com.google.firebase.crashlytics` | 12.9.0, 13.17.0 |
| `com.google.firebase.remote-config` | 12.9.0, 13.17.0 |

## Adding a version

1. Add the version to `packages.json`.
2. Run `python tools/build.py`: it downloads each new tarball once, checks it, and regenerates `docs/`.
3. Commit and push. GitHub Pages serves `docs/`.
