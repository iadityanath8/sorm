# SORM

**SORM** — Simple ORM for Python  

A lightweight **ORM engine** currently in development. SORM aims to provide a clean and intuitive way to interact with SQLite databases in Python. Eventually, it will include a **CLI tool** to generate models, manage migrations, and simplify database operations.

---

## Features (Planned)

- Define models declaratively with Python classes  
- Auto-generate SQLite tables from models  
- Save and fetch records easily  
- Support for constraints like `PRIMARY KEY`, `NOT NULL`, `DEFAULT`, `CHECK`  
- CLI tool to scaffold models and manage the database  

---

## Current Status

> ⚠️ Development has just begun. The ORM engine is being implemented. CLI functionality will be added once the core engine is stable.  

---

## Usage (Example)

```python
from sorm import BaseModel, NOTNULL, DEFAULT, CHECK

class User(BaseModel):
    a: int
    b: str
    c: int

    PK = "a"
    CONSTRAINTS = {
        "b": NOTNULL(),
        "c": [DEFAULT(0), CHECK("c > 9")]
    }

User.create_table()
```

- The above example demonstrates **creating a table with constraints**.  
- Later, the CLI will automate generating such models.  

---

## Installation

> Not yet published. Clone the repo to use the development version:

```bash
git clone https://github.com/iadityanath8/sorm.git
cd sorm
```

---

## Roadmap

- [x] Complete ORM engine  
- [x] Implement save and fetch methods  
- [ ] Add support for migrations  
- [ ] Build the CLI tool for model generation and DB management  
- [ ] Add advanced constraints and relations  


---

## Contribution

Contributions are welcome! Open an issue or pull request to help improve SORM.