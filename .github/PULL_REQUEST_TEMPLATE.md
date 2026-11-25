## Summary of Changes

Describe the changes proposed in this Pull Request and reference any related issues.

Fixes #(issue)

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds real-time / HIL functionality)
- [ ] Refactoring / Performance / Latency optimization
- [ ] Documentation update
- [ ] Governance / Infrastructure update

## Verification & Testing

Please describe the tests and checks executed:

- [ ] `python -m py_compile <modified_py_files>` passes with 0 syntax errors.
- [ ] `bash -n <modified_sh_files>` passes with 0 syntax errors.
- [ ] C++ sources compile cleanly without warnings (`-Wall -Wextra`).
- [ ] Zero allocations (`malloc`/`new`) or blocking calls in periodic real-time loops.
- [ ] No private keys, credentials, or active tunnels introduced (`.env.example` used).

## Checklist

- [ ] My code adheres to the project's coding standards and RTOS guidelines.
- [ ] I have read and agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
- [ ] Commits follow Conventional Commits guidelines.
- [ ] SPDX headers are present and unmodified on altered `.py`, `.sh`, and C++ files.
