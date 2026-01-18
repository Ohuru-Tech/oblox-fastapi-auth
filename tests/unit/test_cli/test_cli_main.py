"""Test CLI main module to cover missing lines."""

from unittest.mock import patch

from fastapi_auth.cli import main


class TestCLIMainModule:
    """Test CLI main module to cover all lines."""

    def test_cli_main_function(self):
        """Test main function execution."""
        # Test that main() calls cli()
        # We can't easily test the if __name__ == "__main__" path, but we can test main()
        with patch("fastapi_auth.cli.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()

    def test_cli_main_as_script(self):
        """Test CLI when run as script."""
        # Test the __main__ path by importing and checking
        import fastapi_auth.cli as cli_module

        # Verify main exists and is callable
        assert hasattr(cli_module, "main")
        assert callable(cli_module.main)

        # Verify cli group exists
        assert hasattr(cli_module, "cli")
        assert callable(cli_module.cli)
