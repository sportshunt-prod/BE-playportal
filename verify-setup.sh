#!/bin/bash
# Docker Setup Verification Script
# This script verifies that the Docker setup is ready to run

set -e

echo "🔍 Verifying Docker Compose setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
CHECKS_PASSED=0
CHECKS_FAILED=0

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_file_executable() {
    if [ -x "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 is executable"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $1 is not executable (will try to fix)"
        chmod +x "$1"
        if [ -x "$1" ]; then
            echo -e "${GREEN}✓${NC} $1 is now executable"
            ((CHECKS_PASSED++))
            return 0
        else
            echo -e "${RED}✗${NC} Failed to make $1 executable"
            ((CHECKS_FAILED++))
            return 1
        fi
    fi
}

check_env_var() {
    if grep -q "^$1=" .env 2>/dev/null; then
        value=$(grep "^$1=" .env | cut -d'=' -f2)
        if [ -n "$value" ] && [ "$value" != "your-secret-key-here-change-this-in-production" ] && [ "$value" != "your-secure-password-here" ] && [[ ! "$value" =~ ^your- ]]; then
            echo -e "${GREEN}✓${NC} $1 is configured"
            ((CHECKS_PASSED++))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $1 needs to be updated in .env"
            ((CHECKS_FAILED++))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $1 is missing in .env"
        ((CHECKS_FAILED++))
        return 1
    fi
}

echo "1️⃣  Checking required commands..."
check_command "docker"
check_command "docker-compose"
echo ""

echo "2️⃣  Checking Docker files..."
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file ".dockerignore"
check_file "docker-entrypoint.sh"
check_file_executable "docker-entrypoint.sh"
echo ""

echo "3️⃣  Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    ((CHECKS_PASSED++))
    echo ""
    echo "   Checking environment variables..."
    check_env_var "DJANGO_SECRET_KEY"
    check_env_var "POSTGRES_PASSWORD"
    check_env_var "GOOGLE_CLIENT_ID"
    check_env_var "GOOGLE_CLIENT_SECRET"
    check_env_var "JWT_SECRET"
else
    echo -e "${RED}✗${NC} .env file is missing"
    echo -e "${YELLOW}ℹ${NC}  Run: cp .env.example .env"
    ((CHECKS_FAILED++))
fi
echo ""

echo "4️⃣  Validating docker-compose.yml syntax..."
if docker-compose config --quiet 2>/dev/null; then
    echo -e "${GREEN}✓${NC} docker-compose.yml is valid"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} docker-compose.yml has syntax errors"
    ((CHECKS_FAILED++))
fi
echo ""

echo "5️⃣  Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC} Docker daemon is not running"
    echo -e "${YELLOW}ℹ${NC}  Please start Docker Desktop or Docker daemon"
    ((CHECKS_FAILED++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: ${GREEN}$CHECKS_PASSED passed${NC}, ${RED}$CHECKS_FAILED failed${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All checks passed! You're ready to run:${NC}"
    echo ""
    echo "    docker-compose up"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed. Please fix the issues above.${NC}"
    echo ""
    if [ ! -f ".env" ]; then
        echo "Quick fix: cp .env.example .env && nano .env"
        echo ""
    fi
    exit 1
fi

