import nox


@nox.session(python=["3.8", "3.9", "3.10", "3.11"], reuse_venv=True)
@nox.parametrize("cairo", ["pycairo", "cairocffi"])
def tests(session, cairo):
    session.install(f".[{cairo}]")
    session.install("pytest")
    session.run("pytest")
