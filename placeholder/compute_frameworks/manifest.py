"""Entry-point manifest: concrete ComputeFramework classes this package exports to mloda discovery."""

from mloda.provider import ComputeFramework

from placeholder.compute_frameworks.my_plugin.my_compute_framework import MyComputeFramework

# Referenced by the "mloda.compute_frameworks" entry point in pyproject.toml.
COMPUTE_FRAMEWORKS: list[type[ComputeFramework]] = [MyComputeFramework]
