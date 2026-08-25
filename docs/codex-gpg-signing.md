# Codex GPG commit signing

This note records the narrow configuration required for the local Codex `unsafe`
profile to create OpenPGP-signed Git commits without granting it write access to
the GnuPG home directory.

## Problem

The profile permits workspace and `.git` writes, but Git invokes GnuPG to create
the signature. On this Fedora setup, GnuPG 2.4 uses `keyboxd`. Its default
startup path attempts to create a dynamic lock file in the GnuPG home directory.
The resulting failure is similar to:

```text
gpg: failed to create temporary file '/home/USER/.gnupg/.#lk...': Read-only file system
gpg: signing failed: Input/output error
```

Commit signing does not normally change trust data. The lock coordinates access
to shared GnuPG state and service startup; the lock filename is dynamic, so it
cannot be safely pre-allowlisted as one static file.

## Narrow approach

Run a host-controlled wrapper that tells GnuPG not to start services or create
GnuPG locks:

```sh
#!/bin/sh
exec /usr/bin/gpg --no-autostart --lock-never "$@"
```

Keep the wrapper outside the workspace and make it readable, but not writable,
by the Codex profile. Git's `gpg.openpgp.program` setting accepts a program
pathname, not fixed command arguments, so the wrapper is required.

Use it for the intended commit rather than setting it as the global default:

```sh
git -c gpg.openpgp.program="$HOME/.local/libexec/codex-gpg-sign" commit -S
```

## Required profile access

GnuPG needs read access to its configuration and access to the already-running
`keyboxd` and `gpg-agent` Unix sockets. Discover the paths on the host instead
of assuming a UID or runtime-directory layout:

```sh
gpgconf --list-dirs homedir keyboxd-socket agent-socket
```

For this host, the relevant values are:

```text
homedir:/home/ben/.gnupg
keyboxd-socket:/run/user/1000/gnupg/S.keyboxd
agent-socket:/run/user/1000/gnupg/S.gpg-agent
```

Add equivalent rules to `~/.codex/unsafe.config.toml`, substituting the paths
reported by `gpgconf`:

```toml
[permissions.unsafe.filesystem]
"~/.gnupg" = "read"
"~/.local/libexec/codex-gpg-sign" = "read"

[permissions.unsafe.filesystem."~/.gnupg"]
"openpgp-revocs.d" = "deny"
"private-keys-v1.d" = "deny"

[permissions.unsafe.network.unix_sockets]
"/run/user/1000/gnupg/S.gpg-agent" = "allow"
"/run/user/1000/gnupg/S.keyboxd" = "allow"
```

Codex permission profiles can grant direct filesystem access and explicit Unix
socket permissions; use the narrowest paths that permit the signing workflow.
See the [Codex permission-profile documentation](https://learn.chatgpt.com/docs/permissions).

## Operational constraints

`--no-autostart` requires `keyboxd` and `gpg-agent` to be reachable already.
If either service is unavailable, signing fails instead of writing state under
`~/.gnupg`.

`--lock-never` is not a cryptographic weakening: it does not expose the signing
key or change a valid signature. It is an operational constraint. Use it only
for this controlled signing path, where concurrent key import, trust-database
maintenance, or GnuPG service lifecycle work is not expected. Do not set the
wrapper as the global Git signing program.

The profile grants the GnuPG secret-key files no direct access. The agent socket
can still authorize a signature using an unlocked key, which is the capability
needed for signed commits.
