import pprint
import sys

filename = "c:/Users/Ayaz Khan/Desktop/Database Migration Agent/backend/config/migration_matrix.py"
sys.path.append("c:/Users/Ayaz Khan/Desktop/Database Migration Agent")
from backend.config.migration_matrix import MIGRATION_MATRIX

MIGRATION_MATRIX["mysql_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] = True
MIGRATION_MATRIX["postgres_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] = True
MIGRATION_MATRIX["mssql_to_oracle"]["datatypes"]["BOOLEAN"]["lossy"] = True

with open(filename) as f:
    content = f.read()

import re

match = re.search(r"\"oracle_to_mysql\":\s*\{", content)
if match:
    new_str = ""
    for k in [
        "oracle_to_mysql",
        "oracle_to_postgres",
        "oracle_to_mssql",
        "mysql_to_oracle",
        "postgres_to_oracle",
        "mssql_to_oracle",
    ]:
        new_str += (
            f'    "{k}": '
            + pprint.pformat(MIGRATION_MATRIX[k], indent=4).replace("\n", "\n    ")
            + ",\n"
        )
    new_str = new_str.rstrip(",\n")

    new_content = content[: match.start()] + new_str + "\n}\n"
    with open(filename, "w") as f:
        f.write(new_content)
    print("Fixed safely")
