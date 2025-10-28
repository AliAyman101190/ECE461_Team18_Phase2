import os
import sys
import pytest
import json
import tempfile
import subprocess
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
app_dir = os.path.join(project_root, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from app.cli_controller import CLIController
from app.url_data import RepositoryData, URLData
# Import URLCategory the same way the CLI controller does
import sys
sys.path.insert(0, app_dir)
from url_category import URLCategory # type: ignore


class TestCLIControllerInit:
    """Test CLIController initialization and basic setup."""
    
    def test_init_creates_dependencies(self):
        """Test that __init__ properly initializes all required dependencies."""
        controller = CLIController()
        
        assert hasattr(controller, 'url_handler')
        assert hasattr(controller, 'metric_calculator')
        assert hasattr(controller, 'data_retriever')
        assert hasattr(controller, 'valid_url_categories')
        assert len(controller.valid_url_categories) == 3
        # Check that all expected categories are present by converting to strings
        category_strings = {str(cat) for cat in controller.valid_url_categories}
        assert "URLCategory.GITHUB" in category_strings or "github" in category_strings
        assert "URLCategory.NPM" in category_strings or "npm" in category_strings
        assert "URLCategory.HUGGINGFACE" in category_strings or "huggingface" in category_strings


class TestParseArguments:
    """Test command line argument parsing."""
    
    def test_parse_arguments_install_command(self, monkeypatch):
        """Test parsing install command."""
        controller = CLIController()
        monkeypatch.setattr(sys, 'argv', ['run', 'install'])
        
        args = controller.parse_arguments()
        assert args.command == 'install'

    def test_parse_arguments_test_command(self, monkeypatch):
        """Test parsing test command."""
        controller = CLIController()
        monkeypatch.setattr(sys, 'argv', ['run', 'test'])
        
        args = controller.parse_arguments()
        assert args.command == 'test'
    
    def test_parse_arguments_file_command(self, monkeypatch):
        """Test parsing file path command."""
        controller = CLIController()
        monkeypatch.setattr(sys, 'argv', ['run', 'sample_input.txt'])
        
        args = controller.parse_arguments()
        assert args.command == 'sample_input.txt'
    
    def test_parse_arguments_no_command(self, monkeypatch):
        """Test parsing with no command (should raise SystemExit)."""
        controller = CLIController()
        monkeypatch.setattr(sys, 'argv', ['run'])
        
        with pytest.raises(SystemExit):
            controller.parse_arguments()


class TestInstallDependencies:
    """Test dependency installation functionality."""
    
    def test_install_dependencies_success(self):
        """Test successful dependency installation."""
        controller = CLIController()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stderr = ''

        with patch('app.cli_controller.subprocess.run', return_value=mock_proc) as mock_run:
            result = controller.install_dependencies()
            
            assert result == 0
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert sys.executable in call_args
            assert '-m' in call_args
            assert 'pip' in call_args
            assert 'install' in call_args
            assert '-r' in call_args
            assert 'requirements.txt' in call_args
            assert '--user' in call_args
    
    def test_install_dependencies_failure(self):
        """Test dependency installation failure."""
        controller = CLIController()
        
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stderr = 'Package not found'
        
        with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
            result = controller.install_dependencies()
            assert result == 1
    
    def test_install_dependencies_exception(self):
        """Test dependency installation with exception."""
        controller = CLIController()
        
        with patch('app.cli_controller.subprocess.run', side_effect=Exception('Network error')):
            result = controller.install_dependencies()
            assert result == 1
    
    def test_install_dependencies_timeout(self):
        """Test dependency installation timeout."""
        controller = CLIController()
        
        with patch('app.cli_controller.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='pip', timeout=300)):
            result = controller.install_dependencies()
            assert result == 1


class TestNormalizeRepo:
    """Test repository data normalization."""
    
    def test_normalize_repo_none_input(self):
        """Test normalization with None input."""
        controller = CLIController()
        result = controller._normalize_repo(None)
        assert result == {}
    
    def test_normalize_repo_dict_input(self):
        """Test normalization with dictionary input."""
        controller = CLIController()
        input_dict = {'name': 'test-repo', 'stars': 100, 'updated_at': '2023-01-01'}
        
        result = controller._normalize_repo(input_dict)
        assert result == input_dict
    
    def test_normalize_repo_object_input(self):
        """Test normalization with object input."""
        controller = CLIController()
        
        class MockRepo:
            def __init__(self):
                self.name = 'test-repo'
                self.stars = 100
                self.private = False
        
        repo_obj = MockRepo()
        result = controller._normalize_repo(repo_obj)
        
        assert result['name'] == 'test-repo'
        assert result['stars'] == 100
        assert result['private'] is False
    
    def test_normalize_repo_datetime_conversion(self):
        """Test datetime object conversion to ISO string."""
        controller = CLIController()
        
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        input_dict = {'name': 'test', 'updated_at': dt}
        
        result = controller._normalize_repo(input_dict)
        assert isinstance(result['updated_at'], str)
        assert '2023-01-01T12:00:00' in result['updated_at']
    
    def test_normalize_repo_skips_private_attributes(self):
        """Test that private attributes are skipped."""
        controller = CLIController()
        
        class MockRepo:
            def __init__(self):
                self.name = 'test'
                self._private_attr = 'should be skipped'
                self.__very_private = 'also skipped'
        
        repo_obj = MockRepo()
        result = controller._normalize_repo(repo_obj)
        
        assert 'name' in result
        assert '_private_attr' not in result
        assert '__very_private' not in result
    
    def test_normalize_repo_skips_callable_attributes(self):
        """Test that callable attributes are skipped."""
        controller = CLIController()
        
        class MockRepo:
            def __init__(self):
                self.name = 'test'
                self.method = lambda x: x
        
        repo_obj = MockRepo()
        result = controller._normalize_repo(repo_obj)
        
        assert 'name' in result
        assert 'method' not in result


class TestProcessSingleModel:
    """Test single model processing functionality."""
    
    def test_process_single_model_success(self):
        """Test successful model processing."""
        controller = CLIController()
        
        # Mock repository data
        code_repo = RepositoryData(platform='github', identifier='user/code', name='code-repo', success=True)
        dataset_repo = RepositoryData(platform='huggingface', identifier='user/dataset', name='dataset-repo', success=True)
        model_repo = RepositoryData(platform='github', identifier='user/model', name='model-repo', success=True)
        
        # Mock data retriever
        controller.data_retriever.retrieve_data = MagicMock(side_effect=[code_repo, dataset_repo, model_repo])
        
        # Mock metric calculator
        mock_metrics = {'ramp_up': 0.8, 'correctness': 0.9, 'bus_factor': 0.7, 'responsive_maintainer': 0.6, 'license_score': 1.0}
        controller.metric_calculator.calculate_all_metrics = MagicMock(return_value=mock_metrics)
        
        input_data = {
            'code': URLData(original_url='https://github.com/user/code', category=URLCategory.GITHUB, hostname='github.com', is_valid=True),
            'dataset': URLData(original_url='https://huggingface.co/user/dataset', category=URLCategory.HUGGINGFACE, hostname='huggingface.co', is_valid=True),
            'model': URLData(original_url='https://github.com/user/model', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        }
        
        result = controller.process_single_model(input_data)
        
        assert result is not None
        assert result['name'] == 'model-repo'
        assert result['ramp_up'] == 0.8
        assert result['correctness'] == 0.9
        controller.metric_calculator.calculate_all_metrics.assert_called_once()
    
    def test_process_single_model_partial_data(self):
        """Test model processing with partial data (missing code/dataset)."""
        controller = CLIController()
        
        # Mock repository data - only model exists
        model_repo = RepositoryData(platform='github', identifier='user/model', name='model-repo', success=True)
        
        controller.data_retriever.retrieve_data = MagicMock(return_value=model_repo)
        
        mock_metrics = {'ramp_up': 0.8, 'correctness': 0.9}
        controller.metric_calculator.calculate_all_metrics = MagicMock(return_value=mock_metrics)
        
        input_data = {
            'code': None,
            'dataset': None,
            'model': URLData(original_url='https://github.com/user/model', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        }
        
        result = controller.process_single_model(input_data)
        
        assert result is not None
        assert result['name'] == 'model-repo'
        controller.metric_calculator.calculate_all_metrics.assert_called_once()
    
    def test_process_single_model_retrieval_failure(self):
        """Test model processing when data retrieval fails."""
        controller = CLIController()
        
        # Mock data retriever to raise exception
        controller.data_retriever.retrieve_data = MagicMock(side_effect=Exception('API error'))
        
        input_data = {
            'code': URLData(original_url='https://github.com/user/code', category=URLCategory.GITHUB, hostname='github.com', is_valid=True),
            'dataset': None,
            'model': URLData(original_url='https://github.com/user/model', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        }
        
        result = controller.process_single_model(input_data)
        assert result is None
    
    def test_process_single_model_metric_calculation_failure(self):
        """Test model processing when metric calculation fails."""
        controller = CLIController()
        
        # Mock successful data retrieval
        model_repo = RepositoryData(platform='github', identifier='user/model', name='model-repo', success=True)
        controller.data_retriever.retrieve_data = MagicMock(return_value=model_repo)
        
        # Mock metric calculator to raise exception
        controller.metric_calculator.calculate_all_metrics = MagicMock(side_effect=Exception('Calculation error'))
        
        input_data = {
            'code': None,
            'dataset': None,
            'model': URLData(original_url='https://github.com/user/model', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        }
        
        result = controller.process_single_model(input_data)
        assert result is None


class TestProcessUrls:
    """Test URL processing functionality."""
    
    def test_process_urls_success(self, capsys):
        """Test successful URL processing."""
        controller = CLIController()
        
        # Mock URL data
        fake_urls = [
            {
                'code': 'https://github.com/user/code',
                'dataset': 'https://huggingface.co/user/dataset',
                'model': 'https://github.com/user/model'
            }
        ]
        
        # Mock URL handler
        controller.url_handler.read_urls_from_file = MagicMock(return_value=fake_urls)
        
        # Mock URL handling
        code_data = URLData(original_url='https://github.com/user/code', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        dataset_data = URLData(original_url='https://huggingface.co/user/dataset', category=URLCategory.HUGGINGFACE, hostname='huggingface.co', is_valid=True)
        model_data = URLData(original_url='https://github.com/user/model', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        
        controller.url_handler.handle_url = MagicMock(side_effect=[code_data, dataset_data, model_data])
        
        # Mock process_single_model
        mock_result = {'name': 'test-model', 'ramp_up': 0.8}
        controller.process_single_model = MagicMock(return_value=mock_result)
        
        result = controller.process_urls('test.txt')
        
        assert result == 0
        captured = capsys.readouterr()
        assert 'test-model' in captured.out
        assert 'ramp_up' in captured.out
    
    def test_process_urls_invalid_model_url(self):
        """Test URL processing with invalid model URL."""
        controller = CLIController()
        
        fake_urls = [
            {
                'code': 'https://github.com/user/code',
                'dataset': 'https://huggingface.co/user/dataset',
                'model': 'invalid-url'
            }
        ]
        
        controller.url_handler.read_urls_from_file = MagicMock(return_value=fake_urls)
        
        # Mock URL handling - model URL is invalid
        code_data = URLData(original_url='https://github.com/user/code', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        dataset_data = URLData(original_url='https://huggingface.co/user/dataset', category=URLCategory.HUGGINGFACE, hostname='huggingface.co', is_valid=True)
        model_data = URLData(original_url='invalid-url', category=URLCategory.GITHUB, hostname='invalid', is_valid=False)
        
        controller.url_handler.handle_url = MagicMock(side_effect=[code_data, dataset_data, model_data])
        
        result = controller.process_urls('test.txt')
        
        assert result == 0  # Should still return 0 even if no valid models found
    
    def test_process_urls_file_read_error(self):
        """Test URL processing when file reading fails."""
        controller = CLIController()
        
        controller.url_handler.read_urls_from_file = MagicMock(side_effect=Exception('File not found'))
        
        result = controller.process_urls('nonexistent.txt')
        assert result == 1
    
    def test_process_urls_empty_file(self):
        """Test URL processing with empty file."""
        controller = CLIController()
        
        controller.url_handler.read_urls_from_file = MagicMock(return_value=[])
        
        result = controller.process_urls('empty.txt')
        assert result == 0
    
    def test_process_urls_processing_exception(self):
        """Test URL processing when individual URL processing fails."""
        controller = CLIController()
        
        fake_urls = [
            {
                'code': 'https://github.com/user/code',
                'dataset': 'https://huggingface.co/user/dataset',
                'model': 'https://github.com/user/model'
            }
        ]
        
        controller.url_handler.read_urls_from_file = MagicMock(return_value=fake_urls)
        controller.url_handler.handle_url = MagicMock(side_effect=Exception('URL processing error'))
        
        result = controller.process_urls('test.txt')
        assert result == 0  # Should continue processing other URLs


class TestRunTests:
    """Test test execution functionality."""
    
    def test_run_tests_success(self, capsys):
        """Test successful test execution."""
        controller = CLIController()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "20 passed, 0 failed in 1.23s\nTOTAL 100 85%"
        
        with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
            result = controller.run_tests()
            
            assert result == 0
            captured = capsys.readouterr()
            assert "20/20 test cases passed" in captured.out
            assert "85% line coverage achieved" in captured.out
    
    def test_run_tests_with_failures(self, capsys):
        """Test test execution with some failures."""
        controller = CLIController()
        
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = "15 passed, 5 failed in 1.23s\nTOTAL 100 75%"
        
        with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
            result = controller.run_tests()
            
            assert result == 1
            captured = capsys.readouterr()
            assert "15/20 test cases passed" in captured.out
            assert "75% line coverage achieved" in captured.out

    def test_run_tests_timeout(self):
        """Test test execution timeout."""
        controller = CLIController()

        with patch('app.cli_controller.subprocess.run', side_effect=subprocess.TimeoutExpired(cmd='pytest', timeout=300)):
            result = controller.run_tests()
            assert result == 1
    
    def test_run_tests_exception(self):
        """Test test execution with exception."""
        controller = CLIController()

        with patch('app.cli_controller.subprocess.run', side_effect=Exception('Test error')):
            result = controller.run_tests()
            assert result == 1
    
    def test_run_tests_malformed_output(self, capsys):
        """Test test execution with malformed pytest output."""
        controller = CLIController()
        
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Some random output without test results"
        
        with patch('app.cli_controller.subprocess.run', return_value=mock_proc):
            result = controller.run_tests()
            
            assert result == 0
            captured = capsys.readouterr()
            assert "0/0 test cases passed" in captured.out
            assert "0% line coverage achieved" in captured.out


class TestRun:
    """Test main run method and command dispatch."""
    
    def test_run_install_command(self):
        """Test run method with install command."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(return_value=SimpleNamespace(command='install'))
        controller.install_dependencies = MagicMock(return_value=0)
        
        result = controller.run()
        assert result == 0
        controller.install_dependencies.assert_called_once()
    
    def test_run_test_command(self):
        """Test run method with test command."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(return_value=SimpleNamespace(command='test'))
        controller.run_tests = MagicMock(return_value=0)
        
        result = controller.run()
        assert result == 0
        controller.run_tests.assert_called_once()
    
    def test_run_file_command(self):
        """Test run method with file command."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(return_value=SimpleNamespace(command='sample.txt'))
        controller.process_urls = MagicMock(return_value=0)
        
        result = controller.run()
        assert result == 0
        controller.process_urls.assert_called_once_with('sample.txt')
    
    def test_run_keyboard_interrupt(self):
        """Test run method with keyboard interrupt."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(side_effect=KeyboardInterrupt())
        
        result = controller.run()
        assert result == 1
    
    def test_run_general_exception(self):
        """Test run method with general exception."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(side_effect=Exception('General error'))
        
        result = controller.run()
        assert result == 1
    
    def test_run_install_failure(self):
        """Test run method when install command fails."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(return_value=SimpleNamespace(command='install'))
        controller.install_dependencies = MagicMock(return_value=1)
        
        result = controller.run()
        assert result == 1
    
    def test_run_test_failure(self):
        """Test run method when test command fails."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(return_value=SimpleNamespace(command='test'))
        controller.run_tests = MagicMock(return_value=1)
        
        result = controller.run()
        assert result == 1
    
    def test_run_file_failure(self):
        """Test run method when file processing fails."""
        controller = CLIController()
        
        controller.parse_arguments = MagicMock(return_value=SimpleNamespace(command='sample.txt'))
        controller.process_urls = MagicMock(return_value=1)
        
        result = controller.run()
        assert result == 1


# class TestEdgeCases:
#     """Test various edge cases and error conditions."""
    
#     def test_process_single_model_empty_data(self):
#         """Test processing model with empty data."""
#         controller = CLIController()
        
#         controller.metric_calculator.calculate_all_metrics = MagicMock(return_value={'ramp_up': 0.5})
        
#         result = controller.process_single_model({})
#         assert result is not None
#         assert result['name'] is None  # No model data provided
    
#     def test_process_single_model_all_none_data(self):
#         """Test processing model with all None data."""
#         controller = CLIController()
        
#         controller.metric_calculator.calculate_all_metrics = MagicMock(return_value={'ramp_up': 0.5})
        
#         input_data = {'code': None, 'dataset': None, 'model': None}
#         result = controller.process_single_model(input_data)
#         assert result is not None
    
#     def test_normalize_repo_with_exception_during_attribute_access(self):
#         """Test normalize_repo when attribute access raises exception."""
#         controller = CLIController()
        
#         class ProblematicRepo:
#             def __init__(self):
#                 self.name = 'test'
            
#             @property
#             def problematic_attr(self):
#                 raise Exception('Access denied')
        
#         repo_obj = ProblematicRepo()
#         result = controller._normalize_repo(repo_obj)
        
#         assert result['name'] == 'test'
#         assert 'problematic_attr' not in result
    
#     def test_process_urls_with_mixed_validity_urls(self):
#         """Test URL processing with mix of valid and invalid URLs."""
#         controller = CLIController()
        
#         fake_urls = [
#             {
#                 'code': 'https://github.com/user/code1',
#                 'dataset': 'https://huggingface.co/user/dataset1',
#                 'model': 'https://github.com/user/model1'
#             },
#             {
#                 'code': 'invalid-code',
#                 'dataset': 'invalid-dataset',
#                 'model': 'invalid-model'
#             },
#             {
#                 'code': 'https://github.com/user/code2',
#                 'dataset': 'https://huggingface.co/user/dataset2',
#                 'model': 'https://github.com/user/model2'
#             }
#         ]
        
#         controller.url_handler.read_urls_from_file = MagicMock(return_value=fake_urls)
        
#         # First URL set - all valid
#         code1 = URLData(original_url='https://github.com/user/code1', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
#         dataset1 = URLData(original_url='https://huggingface.co/user/dataset1', category=URLCategory.HUGGINGFACE, hostname='huggingface.co', is_valid=True)
#         model1 = URLData(original_url='https://github.com/user/model1', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        
#         # Second URL set - all invalid
#         code2 = URLData(original_url='invalid-code', category=URLCategory.GITHUB, hostname='invalid', is_valid=False)
#         dataset2 = URLData(original_url='invalid-dataset', category=URLCategory.HUGGINGFACE, hostname='invalid', is_valid=False)
#         model2 = URLData(original_url='invalid-model', category=URLCategory.GITHUB, hostname='invalid', is_valid=False)
        
#         # Third URL set - all valid
#         code3 = URLData(original_url='https://github.com/user/code2', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
#         dataset3 = URLData(original_url='https://huggingface.co/user/dataset2', category=URLCategory.HUGGINGFACE, hostname='huggingface.co', is_valid=True)
#         model3 = URLData(original_url='https://github.com/user/model2', category=URLCategory.GITHUB, hostname='github.com', is_valid=True)
        
#         controller.url_handler.handle_url = MagicMock(side_effect=[
#             code1, dataset1, model1,  # First set
#             code2, dataset2, model2,  # Second set (invalid)
#             code3, dataset3, model3   # Third set
#         ])
        
#         mock_result = {'name': 'test-model', 'ramp_up': 0.8}
#         controller.process_single_model = MagicMock(return_value=mock_result)
        
#         result = controller.process_urls('test.txt')
        
#         assert result == 0
#         # Should process 2 valid models (first and third sets)
#         assert controller.process_single_model.call_count == 2
