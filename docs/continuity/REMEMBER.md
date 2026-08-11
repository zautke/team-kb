# REMEMBER — team-kb (append-only)

## 2026-08-11

- **Canonical repo**: /Volumes/MACDEV/team-kb (largo). Build copy: adagio `C:\Users\me\dev\team-kb`
  (Windows, `ssh adagio`, dotnet 10.0.302, PowerShell default shell). largo NEVER builds (no SDK,
  ENOSPC-prone boot volume).
- **The one rule of this project**: a rule not enforced by code does not belong in `_meta/`. Closed
  vocabularies live in MCP tool schemas; paths + inverse edges computed server-side; every write is
  staged propose→commit. (master-kb died of prose gates — post-mortem R5/R6.)
- **kb (basic-memory) is still the singular kb until team-kb replaces it** — rebuild research is
  mirrored there under `_governance/research/rebuild-2026-08/`.
- **macOS→Windows transfer gotchas**: AppleDouble `._*` files break csc (use `COPYFILE_DISABLE=1
  tar` or purge on extract); PowerShell double-quoted here-strings treat `\"` literally — transfer
  JSON as files.
- **.NET 10 notes**: C# 14 default (omit LangVersion); NU1015 = every PackageReference needs
  explicit Version; dotnet CLI chatter goes to stderr; MCP stdio servers must route ALL logging to
  stderr (`LogToStandardErrorThreshold = Trace`).
- **xunit.v3** (3.2.2) not xunit 2.x; test csproj needs `<OutputType>Exe</OutputType>`.
- Old project's continuity archived at obsidian-vault-config `docs/proto-implementation/continuity/`;
  its compliance ontology is dead, its layered-fence/gate-server patterns remain referenceable.
