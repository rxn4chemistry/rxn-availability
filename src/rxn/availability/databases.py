import functools
import json
import logging
from typing import Any, Dict, List, Optional

import pymongo
from pydantic import BaseModel, ValidationError
from pymongo import MongoClient
from rxn.utilities.databases.pymongo import PyMongoSettings

from .config import Settings, get_settings

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class DBConfig(BaseModel):
    uri: str
    database: str
    collection: str
    tls_ca_certificate_path: Optional[str] = None


class DB:
    def __init__(self, url: str):
        self.url = url

    def availability(self, smi: str, pricing_threshold: int = 0) -> bool:
        raise NotImplementedError("Please use MongoDB instead of the DB Base class.")


class MongoDB(DB):
    def __init__(
        self, url: str, db: str, collection: str, tls_ca_certificate_path: Optional[str]
    ):  # For mongo we give directly the connection url
        super().__init__(url=url)
        self.db = db
        self.collection = collection
        self.tls_ca_certificate_path = tls_ca_certificate_path
        self.mongo_client: MongoClient = PyMongoSettings.instantiate_client(
            mongo_uri=self.url, tls_ca_certificate_path=self.tls_ca_certificate_path
        )

    @functools.lru_cache(maxsize=2**9)
    def query_by_smi(self, smi: str) -> List[Dict[str, Any]]:
        """Fetch info by SMILES in the database.

        Args:
            smi: the molecule to check.

        Returns:
            a list of matching SMILES with the corresponding metadata.
        """

        logger.debug(f"Fetch information for {smi} in database.")

        collection = self.mongo_client[self.db][self.collection]

        # Create index for smiles -- By default, indexes are created only if missing
        logger.debug('Creating index for "smiles" key if it does not exist')
        collection.create_index([("smiles", pymongo.HASHED)])

        return list(collection.find({"smile": smi}))

    def availability(self, smi: str, pricing_threshold: int = 0) -> bool:
        """Determines whether or not the given molecule `smi` is commercially available,
        according to our customized version of the eMolecules database.

        If a pricing threshold is given, any molecule more expensive than the threshold
        is considered unavailable.

        Args:
            smi: the molecule to check.
            pricing_threshold: the threshold in USD per g/L.

        Returns:
            True if considered available, False otherwise.
        """

        logger.debug(f"Check availability for {smi} in database.")

        results = [item["price_per_amount"] for item in self.query_by_smi(smi=smi)]

        is_available = self._availability_from_db_results(results, pricing_threshold)
        logger.debug(
            f"Done checking for {smi} in database (is_available: {str(is_available)})."
        )
        return is_available

    def _availability_from_db_results(
        self, prices: List[Any], pricing_threshold: int
    ) -> bool:
        # False if nothing found in the DB
        if len(prices) == 0:
            return False

        # True if pricing threshold not set or set to max
        if pricing_threshold == 0 or pricing_threshold == 1000:
            return True

        # keep only the numbers (DB contains also "NA")
        valid_prices = [p for p in prices if isinstance(p, (int, float))]

        # False if no price left
        if len(valid_prices) == 0:
            return False

        # True if the lowest price is under the threshold
        return min(valid_prices) < pricing_threshold


def initialize_databases_from_environment_variables() -> Dict[str, DB]:
    """Initialize databases from availbaility from the environment.

    This function uses the Settings class to read from the environment a path to a configuration file in JSON format
    that stores the URI and connection information to instantiate databases used for availability.

    Returns:
        a dictionary of database names and DB object.
    """
    # Settings
    settings: Settings = get_settings()
    # Databases
    databases: Dict[str, DB] = {}
    if settings.database_config_path is None:
        logger.warning(
            "No database configuration provided! Not using database sources."
        )
    else:
        with open(settings.database_config_path) as json_file:
            database_config = json.load(json_file)
            for database in database_config:
                try:
                    db_config = DBConfig.parse_obj(database_config[database])
                except ValidationError:
                    logger.error(
                        f"Database configuration problem. Check if the file at {settings.database_config_path} has the right configuration format for all databases."
                    )
                    raise
                new_db = MongoDB(
                    url=db_config.uri,
                    db=db_config.database,
                    collection=db_config.collection,
                    tls_ca_certificate_path=db_config.tls_ca_certificate_path,
                )
                databases[database] = new_db
    return databases
