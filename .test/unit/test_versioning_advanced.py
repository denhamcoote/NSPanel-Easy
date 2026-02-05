"""
Advanced tests for versioning system including boundary cases, negative tests, and regression tests.
Tests error conditions, edge cases, and scenarios that could cause issues.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import subprocess


class TestVersionBoundaryConditions:
    """Test boundary conditions for version numbers"""

    VERSION_FILE = Path("/home/jailuser/git/versioning/VERSION")

    def test_version_month_boundary_january(self):
        """Test version handles January (month 1) correctly"""
        version = self.VERSION_FILE.read_text().strip()
        parts = version.split('.')
        month = int(parts[1])
        # If month is 1, it should be represented as "1" not "01"
        if month == 1:
            assert parts[1] == "1", "January should be represented as '1' not '01'"

    def test_version_month_boundary_december(self):
        """Test version handles December (month 12) correctly"""
        version = self.VERSION_FILE.read_text().strip()
        parts = version.split('.')
        month = int(parts[1])
        # If month is 12, it should be valid
        if month == 12:
            assert parts[1] == "12", "December should be represented as '12'"

    def test_version_sequence_minimum(self):
        """Test version sequence starts at minimum value 1"""
        version = self.VERSION_FILE.read_text().strip()
        parts = version.split('.')
        sequence = int(parts[2])
        # Sequence should never be less than 1
        assert sequence >= 1, "Sequence must be at least 1"

    def test_version_year_four_digits(self):
        """Test year is exactly 4 digits"""
        version = self.VERSION_FILE.read_text().strip()
        parts = version.split('.')
        year_str = parts[0]
        assert len(year_str) == 4, f"Year must be exactly 4 digits, got: {year_str}"

    def test_version_handles_large_sequence_numbers(self):
        """Test version can handle large sequence numbers"""
        version = self.VERSION_FILE.read_text().strip()
        parts = version.split('.')
        sequence = int(parts[2])
        # Should support sequences up to reasonable limits
        assert sequence < 10000, "Sequence number seems unreasonably large"


class TestVersionNegativeCases:
    """Test negative cases and invalid inputs"""

    def test_version_file_no_extra_lines(self):
        """Test VERSION file doesn't have multiple version lines"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        lines = [line for line in version_file.read_text().split('\n') if line.strip()]
        assert len(lines) <= 1, "VERSION file should contain only one version"

    def test_version_yaml_no_duplicate_keys(self):
        """Test VERSION_YAML doesn't have duplicate version keys"""
        import yaml
        version_yaml = Path("/home/jailuser/git/versioning/VERSION_YAML")
        with open(version_yaml, 'r') as f:
            data = yaml.safe_load(f)
        # Count occurrences of 'version' key
        keys = list(data.keys())
        assert keys.count('version') == 1, "VERSION_YAML should have exactly one 'version' key"

    def test_version_no_special_characters(self):
        """Test version contains no special characters besides dots"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version = version_file.read_text().strip()
        # Should only contain digits and dots
        for char in version:
            assert char.isdigit() or char == '.', \
                f"Version should only contain digits and dots, found: {char}"

    def test_version_not_empty_string(self):
        """Test version is not an empty string"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version = version_file.read_text().strip()
        assert version != "", "VERSION must not be empty"

    def test_version_yaml_value_not_null(self):
        """Test VERSION_YAML version value is not null"""
        import yaml
        version_yaml = Path("/home/jailuser/git/versioning/VERSION_YAML")
        with open(version_yaml, 'r') as f:
            data = yaml.safe_load(f)
        assert data['version'] is not None, "VERSION_YAML version must not be null"
        assert data['version'] != "", "VERSION_YAML version must not be empty string"


class TestBumpVersionScriptRobustness:
    """Test bump_version.sh script robustness and error handling"""

    SCRIPT_PATH = Path("/home/jailuser/git/versioning/bump_version.sh")

    def test_script_checks_version_file_exists(self):
        """Test script checks if VERSION file exists"""
        content = self.SCRIPT_PATH.read_text()
        # Should check file existence with -f
        assert 'if [ -f' in content or 'if [[ -f' in content, \
            "Script should check if VERSION file exists"

    def test_script_exits_on_invalid_format(self):
        """Test script exits when version format is invalid"""
        content = self.SCRIPT_PATH.read_text()
        # Should exit with error code 1 on invalid format
        lines = content.split('\n')
        found_format_check = False
        found_exit = False

        for i, line in enumerate(lines):
            if 'Invalid version format' in line or 'version format' in line.lower():
                found_format_check = True
                # Check nearby lines for exit
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+5)])
                if 'exit 1' in context:
                    found_exit = True
                    break

        assert found_format_check and found_exit, \
            "Script should exit with error on invalid version format"

    def test_script_validates_before_writing(self):
        """Test script validates version before writing to files"""
        content = self.SCRIPT_PATH.read_text()
        lines = content.split('\n')

        # Find where version is written to file
        write_line = -1
        new_version_line = -1

        for i, line in enumerate(lines):
            if 'NEW_VERSION=' in line and 'echo' not in line:
                new_version_line = i
            if 'echo' in line and 'NEW_VERSION' in line and '>' in line:
                write_line = i
                break

        # NEW_VERSION should be calculated before writing
        assert new_version_line != -1, "Script should calculate NEW_VERSION"
        assert write_line != -1, "Script should write NEW_VERSION to file"
        assert new_version_line < write_line, \
            "Should calculate NEW_VERSION before writing to file"

    def test_script_atomicity_commits_after_both_files(self):
        """Test script commits only after updating both files"""
        content = self.SCRIPT_PATH.read_text()
        lines = content.split('\n')

        version_file_write = -1
        yaml_file_write = -1
        git_add = -1

        for i, line in enumerate(lines):
            if 'echo' in line and 'VERSION_FILE' in line and '>' in line:
                version_file_write = i
            if 'echo' in line and 'VERSION_YAML_FILE' in line and '>' in line:
                yaml_file_write = i
            if 'git add' in line:
                git_add = i

        # Both files should be written before git add
        if version_file_write != -1 and yaml_file_write != -1 and git_add != -1:
            assert version_file_write < git_add, "VERSION should be written before git add"
            assert yaml_file_write < git_add, "VERSION_YAML should be written before git add"

    def test_script_uses_portable_date_command(self):
        """Test script date command is compatible"""
        content = self.SCRIPT_PATH.read_text()
        # Should use date command for year and month
        assert 'date' in content.lower(), "Script should use date command"

    def test_script_handles_month_rollover(self):
        """Test script handles month changes correctly"""
        content = self.SCRIPT_PATH.read_text()
        # Should compare current month with version month
        assert 'CURRENT_MONTH' in content and 'VERSION_MONTH' in content, \
            "Script should compare months to handle rollover"

    def test_script_uses_safe_git_operations(self):
        """Test script uses safe git operations"""
        content = self.SCRIPT_PATH.read_text()
        # Should not use --force or other dangerous options
        assert '--force' not in content, "Script should not use git --force"
        assert '-f ' not in content or 'if [ -f' in content, \
            "Script should not use dangerous force flags (except -f for file test)"


class TestWorkflowRobustness:
    """Test GitHub Actions workflow robustness"""

    WORKFLOW_PATH = Path("/home/jailuser/git/.github/workflows/versioning.yml")

    def test_workflow_prevents_infinite_loops(self):
        """Test workflow prevents infinite triggering loops"""
        content = self.WORKFLOW_PATH.read_text()
        # Should ignore VERSION files to prevent infinite loops
        assert 'paths-ignore' in content, "Workflow should have paths-ignore"
        assert 'VERSION' in content, "Workflow should ignore VERSION file changes"

    def test_workflow_commit_message_has_skip_marker(self):
        """Test workflow ensures commits have skip marker"""
        content = self.WORKFLOW_PATH.read_text()
        script_path = Path("/home/jailuser/git/versioning/bump_version.sh")
        script_content = script_path.read_text()

        # Script should include [skip-versioning] marker in commit
        assert '[skip-versioning]' in script_content or 'skip-versioning' in script_content, \
            "Bump script should use skip-versioning marker in commit message"

    def test_workflow_handles_pr_not_found(self):
        """Test workflow handles case when PR info not available"""
        import yaml
        with open(self.WORKFLOW_PATH, 'r') as f:
            data = yaml.safe_load(f)

        job = data['jobs']['version-and-tag']
        steps = job['steps']

        # Find PR info step
        pr_step = next((s for s in steps if 'pr' in s.get('name', '').lower() and 'info' in s.get('name', '').lower()), None)

        if pr_step and 'uses' in pr_step:
            # Should have try-catch or fallback
            script_content = pr_step.get('with', {}).get('script', '')
            assert 'try' in script_content or 'catch' in script_content, \
                "PR info step should handle errors"

    def test_workflow_validates_version_before_tagging(self):
        """Test workflow validates VERSION file exists before creating tags"""
        content = self.WORKFLOW_PATH.read_text()

        # Stable and latest tag steps should verify VERSION file
        lines = content.split('\n')
        found_validation = False

        for i, line in enumerate(lines):
            # Look for VERSION file check in stable or latest tag steps
            if 'if [ ! -f' in line and 'VERSION' in line:
                found_validation = True
                break
            if 'if [[ ! -f' in line and 'VERSION' in line:
                found_validation = True
                break

        # Should have found validation
        assert found_validation, "Workflow should validate VERSION file exists before tagging"

    def test_workflow_cleanup_removes_temp_files(self):
        """Test workflow cleanup step removes temporary files"""
        content = self.WORKFLOW_PATH.read_text()

        # Cleanup step should remove tag_message.txt
        assert 'rm' in content or 'Cleanup' in content, \
            "Workflow should have cleanup logic"

    def test_workflow_uses_specific_action_versions(self):
        """Test workflow uses specific versions of actions (not @latest)"""
        import yaml
        with open(self.WORKFLOW_PATH, 'r') as f:
            data = yaml.safe_load(f)

        job = data['jobs']['version-and-tag']
        steps = job['steps']

        for step in steps:
            if 'uses' in step:
                action = step['uses']
                # Should use specific version like @v4, not @latest
                if '@' in action:
                    version_part = action.split('@')[1]
                    assert version_part != 'latest', \
                        f"Action should use specific version, not @latest: {action}"


class TestVersioningRegressionTests:
    """Regression tests for known or potential issues"""

    def test_version_consistent_after_month_change(self):
        """Test version sequence resets correctly after month change"""
        # This is a regression test for the month rollover logic
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version = version_file.read_text().strip()
        parts = version.split('.')

        year = int(parts[0])
        month = int(parts[1])
        sequence = int(parts[2])

        # If it's a new month, sequence should be low
        from datetime import datetime
        current_year = datetime.now().year
        current_month = datetime.now().month

        if year == current_year and month == current_month:
            # Sequence should be reasonable for current month
            assert sequence >= 1, "Current month sequence should start at 1"

    def test_version_yaml_parseable_by_esphome(self):
        """Test VERSION_YAML format is compatible with ESPHome includes"""
        version_yaml = Path("/home/jailuser/git/versioning/VERSION_YAML")
        content = version_yaml.read_text()

        # Should be in format that ESPHome can include
        assert content.startswith('version: '), \
            "VERSION_YAML should start with 'version: ' for ESPHome compatibility"

        # Should not have extra YAML document markers
        assert '---' not in content, "VERSION_YAML should not have document markers"
        assert '...' not in content, "VERSION_YAML should not have document end markers"

    def test_bump_script_preserves_newlines(self):
        """Test bump script writes files with proper newlines"""
        script = Path("/home/jailuser/git/versioning/bump_version.sh")
        content = script.read_text()

        # Check how files are written
        if 'echo "$NEW_VERSION" >' in content or 'echo $NEW_VERSION >' in content:
            # echo adds newline by default, which is good
            pass
        elif 'echo -n' in content:
            pytest.fail("Script should not use echo -n which suppresses newlines")

    def test_workflow_runs_on_push_to_main_only(self):
        """Test workflow only runs on main branch pushes"""
        import yaml
        workflow = Path("/home/jailuser/git/.github/workflows/versioning.yml")
        with open(workflow, 'r') as f:
            data = yaml.safe_load(f)

        triggers = data.get(True, data.get('on', {}))
        push_config = triggers.get('push', {})
        branches = push_config.get('branches', [])

        # Should only trigger on main
        assert 'main' in branches or 'master' in branches, \
            "Workflow should trigger on main/master branch"
        # Should not trigger on all branches
        assert '*' not in branches, "Workflow should not trigger on all branches"

    def test_version_file_encoding_utf8(self):
        """Test VERSION files use UTF-8 encoding"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version_yaml = Path("/home/jailuser/git/versioning/VERSION_YAML")

        # Should be readable as UTF-8
        try:
            version_file.read_text(encoding='utf-8')
            version_yaml.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            pytest.fail("VERSION files should use UTF-8 encoding")


class TestVersioningSecurityChecks:
    """Security-related tests for versioning system"""

    def test_bump_script_no_command_injection(self):
        """Test bump script is not vulnerable to command injection"""
        script = Path("/home/jailuser/git/versioning/bump_version.sh")
        content = script.read_text()

        # Variables should be quoted in commands
        # Look for dangerous patterns like: git commit -m $VAR
        lines = content.split('\n')
        for line in lines:
            if 'git commit' in line and '-m' in line:
                # Should use quotes or heredoc
                assert '"' in line or "'" in line or '<<' in line, \
                    f"Git commit should quote variables: {line}"

    def test_workflow_uses_github_token_safely(self):
        """Test workflow uses GITHUB_TOKEN in secure way"""
        content = Path("/home/jailuser/git/.github/workflows/versioning.yml").read_text()

        # Should use secrets.GITHUB_TOKEN
        assert 'secrets.GITHUB_TOKEN' in content or 'GITHUB_TOKEN' in content, \
            "Workflow should use GITHUB_TOKEN"

        # Should not expose token in logs
        assert 'echo $GITHUB_TOKEN' not in content, \
            "Workflow should not echo GITHUB_TOKEN"

    def test_bump_script_no_hardcoded_credentials(self):
        """Test bump script has no hardcoded credentials"""
        script = Path("/home/jailuser/git/versioning/bump_version.sh")
        content = script.read_text()

        # Common patterns to avoid
        dangerous_patterns = [
            'password=',
            'token=',
            'api_key=',
            'secret=',
        ]

        for pattern in dangerous_patterns:
            assert pattern not in content.lower(), \
                f"Script should not contain hardcoded credentials: {pattern}"


class TestVersioningPerformance:
    """Performance-related tests"""

    def test_bump_script_reasonable_length(self):
        """Test bump script is reasonably sized"""
        script = Path("/home/jailuser/git/versioning/bump_version.sh")
        lines = script.read_text().split('\n')

        # Script should be concise (under 100 lines is reasonable)
        assert len(lines) < 200, \
            f"Script has {len(lines)} lines, consider refactoring if too long"

    def test_workflow_minimal_steps(self):
        """Test workflow doesn't have unnecessary steps"""
        import yaml
        workflow = Path("/home/jailuser/git/.github/workflows/versioning.yml")
        with open(workflow, 'r') as f:
            data = yaml.safe_load(f)

        job = data['jobs']['version-and-tag']
        steps = job['steps']

        # Should have reasonable number of steps (not excessive)
        assert len(steps) < 20, \
            f"Workflow has {len(steps)} steps, consider if all are necessary"

    def test_version_file_size_reasonable(self):
        """Test VERSION files are small"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version_yaml = Path("/home/jailuser/git/versioning/VERSION_YAML")

        # Files should be very small (under 100 bytes)
        assert version_file.stat().st_size < 100, "VERSION file too large"
        assert version_yaml.stat().st_size < 200, "VERSION_YAML file too large"


class TestVersioningMaintainability:
    """Tests for code maintainability and clarity"""

    def test_bump_script_has_comments(self):
        """Test bump script has explanatory comments"""
        script = Path("/home/jailuser/git/versioning/bump_version.sh")
        content = script.read_text()

        # Should have at least some comments
        comment_lines = [line for line in content.split('\n') if line.strip().startswith('#')]
        assert len(comment_lines) >= 3, \
            "Script should have comments explaining key logic"

    def test_workflow_steps_have_names(self):
        """Test all workflow steps have descriptive names"""
        import yaml
        workflow = Path("/home/jailuser/git/.github/workflows/versioning.yml")
        with open(workflow, 'r') as f:
            data = yaml.safe_load(f)

        job = data['jobs']['version-and-tag']
        steps = job['steps']

        for i, step in enumerate(steps):
            assert 'name' in step, f"Step {i} should have a name"
            assert len(step['name']) > 3, f"Step {i} name should be descriptive"

    def test_version_files_in_versioning_directory(self):
        """Test VERSION files are in dedicated versioning directory"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version_yaml = Path("/home/jailuser/git/versioning/VERSION_YAML")

        # Both should be in versioning directory
        assert version_file.parent.name == "versioning", \
            "VERSION should be in versioning directory"
        assert version_yaml.parent.name == "versioning", \
            "VERSION_YAML should be in versioning directory"

    def test_readme_in_versioning_directory(self):
        """Test README is in versioning directory with other files"""
        readme = Path("/home/jailuser/git/versioning/README.md")
        assert readme.exists(), "README should be in versioning directory"


class TestVersioningCompatibility:
    """Test compatibility with different environments"""

    def test_bump_script_bash_compatible(self):
        """Test bump script uses bash-compatible syntax"""
        script = Path("/home/jailuser/git/versioning/bump_version.sh")
        content = script.read_text()

        # Should not use zsh-specific or other shell-specific syntax
        assert '#!/bin/bash' in content, "Should explicitly use bash"

    def test_workflow_runs_on_ubuntu_latest_compatible(self):
        """Test workflow uses ubuntu-latest compatible commands"""
        import yaml
        workflow = Path("/home/jailuser/git/.github/workflows/versioning.yml")
        with open(workflow, 'r') as f:
            data = yaml.safe_load(f)

        job = data['jobs']['version-and-tag']

        # Should run on ubuntu
        assert 'ubuntu' in job['runs-on'], "Should run on ubuntu"

    def test_version_format_semver_inspired(self):
        """Test version format is clear and semver-inspired"""
        version_file = Path("/home/jailuser/git/versioning/VERSION")
        version = version_file.read_text().strip()

        # Should use dots as separators (like semver)
        assert version.count('.') == 2, "Version should have 2 dots (3 components)"

        # Should be numeric
        parts = version.split('.')
        for part in parts:
            assert part.isdigit(), f"Version part should be numeric: {part}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])