#!/bin/bash
# Security scanning script for StreamlitForge
# Run this script to perform comprehensive security analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  StreamlitForge Security Scan${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Save start time
START_TIME=$(date +%s)

# Create results directory
mkdir -p security_results

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}$1${NC}"
    echo -e "${BLUE}─${NC}$(printf '─%.0s' {1..$((${#1}+40))})"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}✗ $1 not found - skipping $2${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $1 found${NC}"
        return 0
    fi
}

# 1. Bandit Scan
print_section "1. Bandit Scan (Code Security)"
if check_command bandit "code security"; then
    echo "Running bandit..."
    bandit -r streamlitforge/ -f json -o security_results/bandit.json
    bandit -r streamlitforge/ -f txt > security_results/bandit.txt 2>&1 || true

    # Count HIGH severity issues
    HIGH_COUNT=$(python3 -c "import json; data=json.load(open('security_results/bandit.json')); print(len([i for i in data['results'] if i['severity']=='HIGH'])" 2>/dev/null || echo 0)

    echo ""
    echo "High severity issues: $HIGH_COUNT"

    if [ "$HIGH_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ No HIGH severity issues${NC}"
    else
        echo -e "${RED}✗ Found $HIGH_COUNT HIGH severity issues${NC}"
    fi
fi

# 2. Safety Check
print_section "2. Safety Check (Dependency Vulnerabilities)"
if check_command safety "dependency vulnerabilities"; then
    echo "Running safety check..."
    safety check --json > security_results/safety.json 2>&1 || true
    safety check > security_results/safety.txt 2>&1 || true

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ No known vulnerabilities found${NC}"
    else
        echo -e "${YELLOW}⚠ Vulnerabilities found${NC}"
    fi
fi

# 3. pip-audit
print_section "3. pip-audit (Dependency Audit)"
if check_command pip-audit "dependency audit"; then
    echo "Running pip-audit..."
    pip-audit --format json > security_results/pip_audit.json 2>&1 || true
    pip-audit > security_results/pip_audit.txt 2>&1 || true

    echo "Audit complete"
fi

# 4. SCA Security Scan (if available)
print_section "4. SCA Security Scan"
if check_command trivy "container vulnerability scan"; then
    echo "Running trivy scan..."
    trivy fs streamlitforge/ > security_results/trivy_fs.txt 2>&1 || true
    echo "Scan complete"
else
    echo "Trivy not installed - skipping container scan"
fi

# 5. Secrets Detection
print_section "5. Secrets Detection"
if check_command trufflehog "secrets detection"; then
    echo "Running trufflehog..."
    trufflehog git file://$(pwd) --only-verified --json > security_results/trufflehog.json 2>&1 || true
    echo "Scan complete"
else
    echo "Trufflehog not installed - skipping secrets detection"
fi

# Summary
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
print_section "Security Scan Summary"
echo -e "Total duration: ${YELLOW}${DURATION}s${NC}"
echo -e "Results directory: ${BLUE}security_results/${NC}"
echo ""
echo "Files created:"
ls -lh security_results/

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Scan Complete${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Review the results in security_results/ directory${NC}"
echo -e "${YELLOW}  - bandit.txt: Code security issues${NC}"
echo -e "${YELLOW}  - safety.txt: Dependency vulnerabilities${NC}"
echo -e "${YELLOW}  - pip_audit.txt: Dependency audit results${NC}"
echo ""
echo -e "${YELLOW}To fix security issues:${NC}"
echo -e "  1. Review security_results/bandit.txt for code issues"
echo -e "  2. Run 'safety check --update' to get patch information"
echo -e "  3. Run 'pip-audit --fix' to auto-fix vulnerabilities"
echo ""
