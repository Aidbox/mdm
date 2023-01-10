from ..comparison_library import (
    ExactMatchBase,
    DistanceFunctionAtThresholdsComparisonBase,
    LevenshteinAtThresholdsComparisonBase,
    JaroWinklerAtThresholdsComparisonBase,
    JaccardAtThresholdsComparisonBase,
    ArrayIntersectAtSizesComparisonBase,
)
from .postgres_base import (
    PostgresBase,
)
from .postgres_comparison_level_library import (
    exact_match_level,
    null_level,
    else_level,
    distance_function_level,
    levenshtein_level,
    jaro_winkler_level,
    jaccard_level,
    array_intersect_level,
)


class PostgresComparison(PostgresBase):
    @property
    def _exact_match_level(self):
        return exact_match_level

    @property
    def _null_level(self):
        return null_level

    @property
    def _else_level(self):
        return else_level


class exact_match(PostgresComparison, ExactMatchBase):
    pass


class distance_function_at_thresholds(
    PostgresComparison, DistanceFunctionAtThresholdsComparisonBase
):
    @property
    def _distance_level(self):
        return distance_function_level


class levenshtein_at_thresholds(
    PostgresComparison, LevenshteinAtThresholdsComparisonBase
):
    @property
    def _distance_level(self):
        return levenshtein_level


class jaro_winkler_at_thresholds(
    PostgresComparison, JaroWinklerAtThresholdsComparisonBase
):
    @property
    def _distance_level(self):
        return jaro_winkler_level


class jaccard_at_thresholds(PostgresComparison, JaccardAtThresholdsComparisonBase):
    @property
    def _distance_level(self):
        return jaccard_level


class array_intersect_at_sizes(PostgresComparison, ArrayIntersectAtSizesComparisonBase):
    @property
    def _array_intersect_level(self):
        return array_intersect_level
