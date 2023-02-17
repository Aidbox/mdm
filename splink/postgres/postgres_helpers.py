import uuid
import os
import tempfile
from pathlib import Path
import edn_format as edn


def validate_postgres_connection(connection, logger):

    return # FIXME!!!
    """Check if the postgres connection requested by the user is valid.

    Raises:
        Exception: If the connection is invalid or a warning if
        the naming convention is ambiguous (not adhering to the
        postgres convention).
    """

    if isinstance(connection, postgres.postgresPyConnection):
        return

    if not isinstance(connection, str):
        raise Exception(
            "Connection must be a string in the form: :memory:, :temporary: "
            "or the name of a new or existing postgres database."
        )

    connection = connection.lower()

    if connection in [":memory:", ":temporary:"]:
        return

    suffixes = (".postgres", ".db")
    if connection.endswith(suffixes):
        return

    logger.info(
        f"The registered connection -- {connection} -- has an uncommon file type. "
        "We recommend that you add a clear suffix of '.db' or '.postgres' "
        "to the connection string, when generating an on-disk database."
    )


def create_temporary_postgres_connection(self):
    """
    Create a temporary postgres connection.
    """
    self._temp_dir = tempfile.TemporaryDirectory(dir=".")
    fname = uuid.uuid4().hex[:7]
    path = os.path.join(self._temp_dir.name, f"{fname}.postgres")
    con = postgres.connect(database=path, read_only=False)
    return con


def postgres_load_from_file(path):
    file_functions = {
        ".csv": f"read_csv_auto('{path}')",
        ".parquet": f"read_parquet('{path}')",
    }
    file_ext = Path(path).suffix
    if file_ext in file_functions.keys():
        return file_functions[file_ext]
    else:
        return path


def comparison_level_type(level):
    if 'is_null_level' in level:
        return 'null'
    elif 'sql_condition' in level and level['sql_condition'].lower() == 'else':
        return 'else'
    else:
        return 'level'


def format_comparison_level(level):
    cond = level['sql_condition']
    m_prob = level['m_probability']
    u_prob = level['u_probability']
    use_frequencies = False
    if 'tf_adjustment_column' in level:
        use_frequencies = True
    level_dict = {
        edn.Keyword('cond'): cond,
        edn.Keyword('m-prob'): m_prob,
        edn.Keyword('u-prob'): u_prob
    }
    if use_frequencies:
        level_dict[edn.Keyword('use-frequencies')] = True
    return {
        'use_frequencies': use_frequencies,
        'levels': level_dict
    }


def format_comparison_null(level):
    return {
        'use_frequencies': False,
        'levels': {edn.Keyword('cond'): level['sql_condition']}
    }


def format_comparison_else(level):
    return {
        'use_frequencies': False,
        'levels': {
            edn.Keyword('cond'): edn.Keyword('else'),
            edn.Keyword('m-prob'): level['m_probability'],
            edn.Keyword('u-prob'): level['u_probability']
        }
    }


def format_comparison_levels(levels):
    null_level = None
    else_level = None
    other_levels = []
    use_frequencies = False
    for level in levels:
        level_type = comparison_level_type(level)

        if level_type == 'null':
            level_info = format_comparison_null(level)
            level_dict = level_info['levels']
            use_frequencies = use_frequencies or level_info['use_frequencies']
            null_level = level_dict
        elif level_type == 'else':
            level_info = format_comparison_else(level)
            level_dict = level_info['levels']
            use_frequencies = use_frequencies or level_info['use_frequencies']
            else_level = level_dict
        else:
            level_info = format_comparison_level(level)
            level_dict = level_info['levels']
            use_frequencies = use_frequencies or level_info['use_frequencies']
            other_levels.append(level_dict)
        
    assert null_level and else_level and other_levels
        
    return {
        'use_frequencies': use_frequencies,
        'levels': [null_level, else_level, *other_levels]
    }


def format_comparisons(comparisons):
    comparisons_dict = {}
    use_frequencies_for = []
    for comparison in comparisons:
        column_name = comparison['output_column_name']
        levels_info = format_comparison_levels(comparison['comparison_levels'])
        levels = levels_info['levels']
        if levels_info['use_frequencies']:
            use_frequencies_for.append(column_name)
        comparisons_dict[edn.Keyword(column_name)] = levels
    return {
        'use_frequencies_for': use_frequencies_for,
        'comparisons': comparisons_dict
    }

def keywordize(data):
    if isinstance(data, list):
        return [keywordize(datum) for datum in data]
    if isinstance(data, dict):
        return {edn.Keyword(key) if isinstance(key, str) else key: keywordize(value) for key, value in data.items()}
    return data

def keywordize_field(data):
    if not isinstance(data, list):
        return data
    result = []
    for datum in data:
        if isinstance(datum, str):
            result.append(edn.Keyword(datum))
        elif isinstance(datum, dict):
            result.append(keywordize(datum))
        else:
            result.append(datum)
    return result

def keywordize_fields(data):
    if not isinstance(data, dict):
        return data
    result = {}
    for key, value in data.items():
        result[edn.Keyword(key)] = keywordize_field(value)
    return result

def format_mdm_model(model):
    return {
        edn.Keyword('resource-type'): model['resource-type'],
        edn.Keyword('use-frequencies-for'): set(model['use-frequencies-for']),
        edn.Keyword('field'): keywordize_fields(model['fields'])
    }

def generate_zen_model(mdm_model, splink_model):
    comparison_data = format_comparisons(splink_model['comparisons'])
    comparisons = comparison_data['comparisons']
    use_frequencies_for = {edn.Keyword(x) for x in comparison_data['use_frequencies_for']}
    random_match_probability = splink_model['probability_two_random_records_match']
    blocking_conds = splink_model['blocking_rules_to_generate_predictions']
    
    zen_model_dict = {
        edn.Keyword('zen/tags'): {edn.Keyword('aidbox.mdm/model')}
        edn.Keyword('comparisons'): comparisons,
        edn.Keyword('random-match-prob'): random_match_probability,
        edn.Keyword('blocking-conds'): blocking_conds
    }
    if use_frequencies_for:
        zen_model_dict[edn.Keyword('use-frequencies-for')] = use_frequencies_for

    mdm_model_edn = format_mdm_model(mdm_model.as_dict())
    return mdm_model_edn | zen_model_dict
