"""Entry-point manifest: concrete FeatureGroup classes this package exports to mloda discovery."""

from mloda.provider import FeatureGroup

from placeholder.feature_groups.my_plugin.my_feature_group import MyFeatureGroup

# Referenced by the "mloda.feature_groups" entry point in pyproject.toml.
FEATURE_GROUPS: list[type[FeatureGroup]] = [MyFeatureGroup]
