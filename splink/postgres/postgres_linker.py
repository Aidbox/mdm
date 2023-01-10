import edn_format as edn
import logging
from typing import Union, List
from tempfile import TemporaryDirectory

from aidbox import Aidbox
import pandas as pd

from .postgres_helpers import (
    validate_postgres_connection,
    create_temporary_postgres_connection,
    postgres_load_from_file,
    generate_zen_model
)
from ..linker import Linker
from ..splink_dataframe import SplinkDataFrame
from ..logging_messages import execute_sql_logging_message_info, log_sql
from ..misc import (
    ensure_is_list,
    all_letter_combos,
)
from ..input_column import InputColumn

logger = logging.getLogger(__name__)


class PostgresLinkerDataFrame(SplinkDataFrame):
    def __init__(self, templated_name, physical_name, postgres_linker):
        super().__init__(templated_name, physical_name)
        self.postgres_linker = postgres_linker

    @property
    def columns(self) -> List[InputColumn]:
        sql = f"""
        SELECT * FROM {self.physical_name} LIMIT 1;
        """

        result = self.postgres_linker.box.sql(sql)
        columns = result[0].keys()
        return [InputColumn(column, sql_dialect="postgres") for column in columns]

    def validate(self):
        pass

    def drop_table_from_database(self, force_non_splink_table=False):

        self._check_drop_table_created_by_splink(force_non_splink_table)

        drop_sql = f"""
        DROP TABLE IF EXISTS {self.physical_name}"""
        self.postgres_linker.box.sql(drop_sql)

    def as_record_dict(self, limit=None):

        sql = f"select * from {self.physical_name}"
        if limit:
            sql += f" limit {limit}"

        return self.postgres_linker.box.sql(sql)


class PostgresLinker(Linker):
    """Manages the data linkage process and holds the data linkage model."""

    def __init__(
        self,
        model,
        box: Aidbox,
        settings_dict: dict = None,
        set_up_basic_logging: bool = True,
        input_table_aliases: Union[str, list] = None,
    ):
        """The Linker object manages the data linkage process and holds the data linkage
        model.

        Most of Splink's functionality can  be accessed by calling functions (methods)
        on the linker, such as `linker.predict()`, `linker.profile_columns()` etc.

        Args:
            input_table_or_tables (Union[str, list]): Input data into the linkage model.
                Either a single string (the name of a table in a database) for
                deduplication jobs, or a list of strings  (the name of tables in a
                database) for link_only or link_and_dedupe
            settings_dict (dict, optional): A Splink settings dictionary. If not
                provided when the object is created, can later be added using
                `linker.initialise_settings()` Defaults to None.
            connection (PostgresPyConnection or str, optional):  Connection to postgres.
                If a a string, will instantiate a new connection.  Defaults to :memory:.
                If the special :temporary: string is provided, an on-disk postgres
                database will be created in a temporary directory.  This can be used
                if you are running out of memory using :memory:.
            set_up_basic_logging (bool, optional): If true, sets ups up basic logging
                so that Splink sends messages at INFO level to stdout. Defaults to True.
            output_schema (str, optional): Set the schema along which all tables
                will be created.
            input_table_aliases (Union[str, list], optional): Labels assigned to
                input tables in Splink outputs.  If the names of the tables in the
                input database are long or unspecific, this argument can be used
                to attach more easily readable/interpretable names. Defaults to None.
        """

        self._sql_dialect_ = "postgres"

        self.box = box

        self.box.sql("""
        CREATE OR REPLACE FUNCTION
        log2(x double precision)
        RETURNS double precision
        AS $$
        select log(2, x::numeric)::double precision;
        $$ LANGUAGE SQL IMMUTABLE PARALLEL SAFE STRICT
        """)

        input_table_or_tables = model.table_name()

        super().__init__(
            input_table_or_tables,
            settings_dict,
            set_up_basic_logging,
            input_table_aliases=input_table_aliases,
        )

    def _table_to_splink_dataframe(self, templated_name, physical_name) -> PostgresLinkerDataFrame:
        return PostgresLinkerDataFrame(templated_name, physical_name, self)

    def _execute_sql_against_backend(self, sql, templated_name, physical_name):

        # In the case of a table already existing in the database,
        # execute sql is only reached if the user has explicitly turned off the cache
        self._delete_table_from_database(physical_name)

        logger.debug(
            execute_sql_logging_message_info(
                templated_name, physical_name
            )
        )
        logger.log(5, log_sql(sql))

        sql = f"""
        CREATE TABLE {physical_name}
        AS
        ({sql})
        """
        self.box.sql(sql)
    
        output_obj = self._table_to_splink_dataframe(templated_name, physical_name)
        return output_obj

    def register_table(self, input, table_name, overwrite=False):

        # Check if table name is already in use
        exists = self._table_exists_in_database(table_name)
        if exists:
            if not overwrite:
                raise ValueError(
                    f"Table '{table_name}' already exists in database. "
                    "Please use the 'overwrite' argument if you wish to overwrite"
                )
            else:
                self._delete_table_from_database(table_name)

        if isinstance(input, dict):
            input = pd.DataFrame(input)
        elif isinstance(input, list):
            input = pd.DataFrame.from_records(input)

        # Will error if an invalid data type is passed
        input.to_sql(table_name, self.con, index=False)
        return self._table_to_splink_dataframe(table_name, table_name)

    def initialise_settings(self, settings_dict: dict):
        if "sql_dialect" not in settings_dict:
            settings_dict["sql_dialect"] = "postgres"
        super().initialise_settings(settings_dict)

    def _random_sample_sql(self, proportion, sample_size):
        if proportion == 1.0:
            return ""
        percent = proportion * 100
        return f"TABLESAMPLE BERNOULLI({percent})"

    @property
    def _infinity_expression(self):
        return "'infinity'"

    def _table_exists_in_database(self, table_name):
        sql = f"""SELECT EXISTS (
            SELECT FROM
                pg_tables
            WHERE
                tablename='{table_name}'
            );"""

        result = self.box.sql(sql)[0]['exists']
        if result:
            return True
        else:
            return False

    def _delete_table_from_database(self, name):
        drop_sql = f"""
        DROP TABLE IF EXISTS {name}"""
        self.box.sql(drop_sql)
    
    def save_zen_model_edn(self, filename):
        with open(filename, w) as f:
            model = self._settings_obj.as_dict()
            zen_model = generate_zen_model(model)
            edn_string = edn.dumps(f)
            f.write(edn_string)

    def drop_splink_tables(self):
        splink_tables_sql = f"""
            SELECT tablename FROM
                pg_tables
            WHERE
                tablename like '\\_\\_splink\\_\\_%'
            """

        response = self.box.sql(splink_tables_sql)
        splink_tables = [row['tablename'] for row in response]

        table_sql_list = ', '.join([f'"{table}"' for table in splink_tables])
        drop_sql = f"DROP TABLE IF EXISTS {table_sql_list}"
        self.box.sql(drop_sql)
