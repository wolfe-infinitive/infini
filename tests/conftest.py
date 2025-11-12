def pytest_addoption(parser):
    parser.addoption(
        "--fix",
        action="store_true",
        default=False,
        help="Automatically fix requirements.txt (add missing, comment unused).",
    )