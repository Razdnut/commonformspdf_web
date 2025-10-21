from commonforms.inference import prepare_form


def main():
    from commonforms.__main__ import main as cli_main

    cli_main()


__all__ = ["prepare_form", "main"]
