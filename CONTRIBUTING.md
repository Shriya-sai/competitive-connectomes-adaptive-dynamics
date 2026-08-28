# Contributing

Bug reports, reproducibility checks and focused pull requests are welcome.
Please open an issue before proposing a substantial methodological change.

Set up Python 3.12 and the development environment as described in the README,
then run the test suite before submitting a change:

```bash
python -m pytest -q
```

Do not commit participant data, generated derivatives, model outputs, software
licences, credentials or local machine paths. Scientific changes should state
whether they are exploratory or confirmatory and preserve the frozen
configuration history.
