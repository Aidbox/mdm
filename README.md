# Python API for Aidbox MDM module
MDM module helps you deduplicate data in your Aidbox.
This repository has 2 Python modules:
- `aidbox` — module for communication with Aidbox
- `splink` — fork of [splink](https://github.com/moj-analytical-services/splink) with support for Aidbox

## Installation
You need to have Python 3, poetry, and Jupyter.

Then run
```sh
poetry install
poetry shell
python -m ipykernel install --user --name aidbox --display-name Aidbox
```

## Usage
### Connection to Aidbox
Create Aidbox connection:
```python
import aidbox
box = aidbox.Aidbox('https://base-url', 'client-id', 'client-secret')
```

Check connection:
```python
box.check()
```

### Creating MDM model
Create empty MDM model:
```python
import aidbox.mdm as mdm

model = mdm.Model('ResourceType')
```

Set up fields to extract in MDM table:
```python
model['first_name'] = ['name', 0, 'given', 0]
model['last_name'] = ['name', 0, 'family']
```

Set up term frequencies for needed fields:
```python
model.enable_frequencies('first_name')
```

Apply model to create MDM table in Aidbox:
```python
model.apply(box)
```

### Learning model weights
See [splink](https://github.com/moj-analytical-services/splink) documentation to learn how to use splink.
This guide shows only differences needed for data linkage with Aidbox.

Change id column from `unique_id` to `id`:
```python
settings = {
    # ...
    'unique_id_column_name': 'id',
    # ...
}
```

Create linker
```python
linker = PostgresLinker(model, box, settings)
```

Splink caches intermediate results. If you want to start from scratch (e.g. your data has changed), use
```python
linker.drop_splink_tables()
```

Train model as usual

Export model as zen-lang edn file for Aidbox configuration project
```
linker.save_zen_model_edn('filename.edn')
```
