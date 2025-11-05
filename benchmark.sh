#!/bin/bash

###############################################################################
# Alp Package Manager - Performance Benchmark Script
# Tests various performance metrics and compares optimizations
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${CYAN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║     Alp Package Manager - Performance Benchmark          ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Configuration
RESULTS_FILE="benchmark-results-$(date +%Y%m%d-%H%M%S).txt"
DOCKER_IMAGE="alp-manager:latest"

# Helper functions
log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_result() {
    echo -e "${GREEN}[RESULT]${NC} $1"
}

log_metric() {
    echo -e "${CYAN}  →${NC} $1: ${BOLD}$2${NC}"
}

# Initialize results file
echo "Alp Package Manager - Performance Benchmark Results" > "$RESULTS_FILE"
echo "Date: $(date)" >> "$RESULTS_FILE"
echo "System: $(uname -a)" >> "$RESULTS_FILE"
echo "========================================" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

###############################################################################
# Test 1: Docker Image Size
###############################################################################
log_test "1. Docker Image Size"
if docker images "$DOCKER_IMAGE" --format "{{.Size}}" &>/dev/null; then
    IMAGE_SIZE=$(docker images "$DOCKER_IMAGE" --format "{{.Size}}")
    log_metric "Image Size" "$IMAGE_SIZE"
    echo "Image Size: $IMAGE_SIZE" >> "$RESULTS_FILE"
else
    echo "Image not built yet. Run: docker build -t $DOCKER_IMAGE ."
    echo "Image Size: NOT BUILT" >> "$RESULTS_FILE"
fi
echo ""

###############################################################################
# Test 2: Build Time (Fresh Build)
###############################################################################
log_test "2. Docker Build Time (No Cache)"
START_TIME=$(date +%s)
if docker build --no-cache -t "${DOCKER_IMAGE}-test" . &>/dev/null; then
    END_TIME=$(date +%s)
    BUILD_TIME=$((END_TIME - START_TIME))
    log_metric "Fresh Build Time" "${BUILD_TIME}s"
    echo "Fresh Build Time: ${BUILD_TIME}s" >> "$RESULTS_FILE"
    docker rmi "${DOCKER_IMAGE}-test" &>/dev/null || true
else
    echo "Build failed"
    echo "Fresh Build Time: FAILED" >> "$RESULTS_FILE"
fi
echo ""

###############################################################################
# Test 3: Build Time (Cached Build)
###############################################################################
log_test "3. Docker Build Time (Cached)"
START_TIME=$(date +%s)
if docker build -t "${DOCKER_IMAGE}-test" . &>/dev/null; then
    END_TIME=$(date +%s)
    CACHED_BUILD_TIME=$((END_TIME - START_TIME))
    log_metric "Cached Build Time" "${CACHED_BUILD_TIME}s"
    echo "Cached Build Time: ${CACHED_BUILD_TIME}s" >> "$RESULTS_FILE"
    docker rmi "${DOCKER_IMAGE}-test" &>/dev/null || true
else
    echo "Build failed"
    echo "Cached Build Time: FAILED" >> "$RESULTS_FILE"
fi
echo ""

###############################################################################
# Test 4: Container Startup Time
###############################################################################
log_test "4. Container Startup Time"
START_TIME=$(date +%s.%N)
docker run --rm "$DOCKER_IMAGE" alp help &>/dev/null || true
END_TIME=$(date +%s.%N)
STARTUP_TIME=$(echo "$END_TIME - $START_TIME" | bc)
log_metric "Startup Time" "${STARTUP_TIME}s"
echo "Startup Time: ${STARTUP_TIME}s" >> "$RESULTS_FILE"
echo ""

###############################################################################
# Test 5: Memory Usage
###############################################################################
log_test "5. Memory Usage"
# Start container in background
CONTAINER_ID=$(docker run -d "$DOCKER_IMAGE" sleep 60)
sleep 2
MEM_USAGE=$(docker stats "$CONTAINER_ID" --no-stream --format "{{.MemUsage}}" | awk '{print $1}')
log_metric "Memory Usage" "$MEM_USAGE"
echo "Memory Usage: $MEM_USAGE" >> "$RESULTS_FILE"
docker stop "$CONTAINER_ID" &>/dev/null
docker rm "$CONTAINER_ID" &>/dev/null
echo ""

###############################################################################
# Test 6: Package Update Performance
###############################################################################
log_test "6. Package Update Performance"
START_TIME=$(date +%s.%N)
docker run --rm -v alp-bench-data:/root/.alp "$DOCKER_IMAGE" alp update &>/dev/null || true
END_TIME=$(date +%s.%N)
UPDATE_TIME=$(echo "$END_TIME - $START_TIME" | bc)
log_metric "Update Time" "${UPDATE_TIME}s"
echo "Update Time: ${UPDATE_TIME}s" >> "$RESULTS_FILE"

# Cleanup
docker volume rm alp-bench-data &>/dev/null || true
echo ""

###############################################################################
# Test 7: Python Script Load Time
###############################################################################
log_test "7. Python Script Load Time"
START_TIME=$(date +%s.%N)
docker run --rm "$DOCKER_IMAGE" python3 -c "import sys; sys.path.insert(0, '/app'); import alp_manager" &>/dev/null || true
END_TIME=$(date +%s.%N)
LOAD_TIME=$(echo "$END_TIME - $START_TIME" | bc)
log_metric "Script Load Time" "${LOAD_TIME}s"
echo "Script Load Time: ${LOAD_TIME}s" >> "$RESULTS_FILE"
echo ""

###############################################################################
# Test 8: Docker Layer Count
###############################################################################
log_test "8. Docker Layer Analysis"
LAYER_COUNT=$(docker history "$DOCKER_IMAGE" --no-trunc | grep -v "<missing>" | wc -l)
log_metric "Layer Count" "$LAYER_COUNT"
echo "Layer Count: $LAYER_COUNT" >> "$RESULTS_FILE"
echo ""

###############################################################################
# Summary
###############################################################################
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  Benchmark Complete!${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Results saved to:${NC} ${BOLD}$RESULTS_FILE${NC}"
echo ""

# Performance score calculation (simple heuristic)
echo "Performance Summary:" >> "$RESULTS_FILE"
echo "===================" >> "$RESULTS_FILE"

if [ -n "$IMAGE_SIZE" ]; then
    SIZE_MB=$(echo "$IMAGE_SIZE" | sed 's/MB//')
    if (( $(echo "$SIZE_MB < 100" | bc -l) )); then
        echo "✓ Image Size: EXCELLENT (< 100MB)" >> "$RESULTS_FILE"
        echo -e "${GREEN}✓${NC} Image Size: EXCELLENT"
    elif (( $(echo "$SIZE_MB < 200" | bc -l) )); then
        echo "✓ Image Size: GOOD (< 200MB)" >> "$RESULTS_FILE"
        echo -e "${YELLOW}✓${NC} Image Size: GOOD"
    else
        echo "⚠ Image Size: NEEDS IMPROVEMENT (> 200MB)" >> "$RESULTS_FILE"
        echo -e "${RED}⚠${NC} Image Size: NEEDS IMPROVEMENT"
    fi
fi

if [ -n "$STARTUP_TIME" ]; then
    if (( $(echo "$STARTUP_TIME < 3" | bc -l) )); then
        echo "✓ Startup Time: EXCELLENT (< 3s)" >> "$RESULTS_FILE"
        echo -e "${GREEN}✓${NC} Startup Time: EXCELLENT"
    elif (( $(echo "$STARTUP_TIME < 5" | bc -l) )); then
        echo "✓ Startup Time: GOOD (< 5s)" >> "$RESULTS_FILE"
        echo -e "${YELLOW}✓${NC} Startup Time: GOOD"
    else
        echo "⚠ Startup Time: NEEDS IMPROVEMENT (> 5s)" >> "$RESULTS_FILE"
        echo -e "${RED}⚠${NC} Startup Time: NEEDS IMPROVEMENT"
    fi
fi

echo ""
echo -e "${CYAN}To view full results:${NC} cat $RESULTS_FILE"
echo ""
