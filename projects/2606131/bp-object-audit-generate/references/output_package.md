# Output Package

> **Evan 落地配置（2026-06-13）**
> - `PROJECT_ROOT` 定义在 `references/source_manifest.md` § 2，本文件不重复硬编码
> - 当前 Evan 端：`<PROJECT_ROOT>/输出/BP对象审计生成/`（路径在 source_manifest 落地注释中维护）

## 1. Default Output Root

Use `<PROJECT_ROOT>/输出/BP对象审计生成/` as the default output root. `PROJECT_ROOT` itself is defined in `references/source_manifest.md` § 2; do not redefine the absolute path here. If `PROJECT_ROOT` is not set yet, ask the user to confirm it (and the output directory) before writing any file.

If the platform does not support local file writing, output the Markdown content in the chat and ask the user to save it manually.

## 2. Recommended Folder Structure

```text
BP对象审计生成/
├── 00_BP对象生成总目录.md
├── 01_已确认规则与口径清单.md
├── 02_待确认问题清单.md
├── 03_来源读取与证据状态.md
├── 04_承接关系总表.md
├── group/
├── centers/
├── departments/
├── individuals/
└── packages/
```

## 3. BP Object File Naming

| Level | Pattern |
|---|---|
| Group | `group/O<编号>_<短标题>.md` |
| Center / business company | `centers/<中心或公司>_<目标编号>_<短标题>.md` |
| Department | `departments/<中心或公司>_<部门>_<目标编号>_<短标题>.md` |
| Individual | `individuals/<姓名或岗位>_<目标编号>_<短标题>.md` |

Use safe filenames. Keep original Chinese names when useful.

## 4. Status Files

Update these when archiving confirmed or draft BP objects:

| File | Purpose |
|---|---|
| `00_BP对象生成总目录.md` | Object list, level, status, file path. Maintain a **processing progress** section showing which objectives are 已归档 vs 待处理 when the source document contains multiple BP objects (see state `archived` in `interactive_state_machine.md`). |
| `01_已确认规则与口径清单.md` | User-confirmed reusable rules |
| `02_待确认问题清单.md` | Open issues and affected objects |
| `03_来源读取与证据状态.md` | Source status by object |
| `04_承接关系总表.md` | Upstream initiative to downstream object relationship |

Do not update status files if the user only asked for a chat discussion and did not authorize writing.

## 5. Skill Package

When the user asks to package this skill, include:

1. `SKILL.md`;
2. `agents/agent.yaml`;
3. all files under `references/`;
4. no external BP source documents unless the user explicitly asks to bundle source BP materials.

Package name pattern:

`bp-object-audit-generate_<YYYYMMDD>.zip`

