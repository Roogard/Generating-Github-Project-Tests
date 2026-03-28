def pytest_configure(config):
    pytest.use_correct = config.getoption("--correct")
    pytest.run_slow = config.getoption("--runslow")