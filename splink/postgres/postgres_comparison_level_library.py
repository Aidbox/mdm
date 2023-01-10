from ..comparison_level_library import (
    ExactMatchLevelBase,
    LevenshteinLevelBase,
    JaccardLevelBase,
    JaroWinklerLevelBase,
    ElseLevelBase,
    NullLevelBase,
    DistanceFunctionLevelBase,
    ColumnsReversedLevelBase,
    DistanceInKMLevelBase,
    PercentageDifferenceLevelBase,
    ArrayIntersectLevelBase,
)
from .postgres_base import (
    PostgresBase,
)


class null_level(PostgresBase, NullLevelBase):
    pass


class exact_match_level(PostgresBase, ExactMatchLevelBase):
    pass


class else_level(PostgresBase, ElseLevelBase):
    pass


class columns_reversed_level(PostgresBase, ColumnsReversedLevelBase):
    pass


class distance_function_level(PostgresBase, DistanceFunctionLevelBase):
    pass


class levenshtein_level(PostgresBase, LevenshteinLevelBase):
    pass


class jaro_winkler_level(PostgresBase, JaroWinklerLevelBase):
    pass


class jaccard_level(PostgresBase, JaccardLevelBase):
    pass


class array_intersect_level(PostgresBase, ArrayIntersectLevelBase):
    pass


class percentage_difference_level(PostgresBase, PercentageDifferenceLevelBase):
    pass


class distance_in_km_level(PostgresBase, DistanceInKMLevelBase):
    pass
