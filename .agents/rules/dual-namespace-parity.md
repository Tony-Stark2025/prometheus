---
name: dual-namespace-parity
trigger: always_on
---

# Dual Namespace Parity Invariant

When working in codebases that maintain dual root packages (e.g. `prometheus/` and `app/`):

1. **Symmetric Edits**: Every modification made to a file in `prometheus/` must be mirrored to the corresponding file in `app/` before running tests or committing.
2. **Automated Synchronization**: Use a python sync script or shutil copy step to ensure zero drift:
   ```python
   shutil.copyfile('prometheus/path/file.py', 'app/path/file.py')
   ```
3. **Parity Validation**: Run the namespace parity test suite before git push:
   ```powershell
   pytest tests/integration/test_m1_reviewer2_adversarial.py -k test_app_and_prometheus_namespace_parity
   ```
