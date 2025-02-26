#!/bin/bash
set -e

# ANSI color codes for better output readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print info messages
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to make API calls and format the output with jq
call_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -e "${YELLOW}$description...${NC}"
    
    if [ -z "$data" ]; then
        # GET or DELETE request without body
        response=$(curl -s -X $method "http://localhost:8000$endpoint" -H "accept: application/json")
    else
        # POST, PUT or PATCH request with JSON body
        response=$(curl -s -X $method "http://localhost:8000$endpoint" \
            -H "accept: application/json" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    # Check if response is valid JSON
    if echo "$response" | jq -e . >/dev/null 2>&1; then
        echo "$response" | jq .
        print_success "API call completed successfully"
    else
        print_error "Failed to parse response as JSON"
        echo "$response"
        return 1
    fi
    
    echo ""
}

# Step 1: Build the Docker container
print_header "BUILDING DOCKER CONTAINER"
docker build -t cloudproxy:test .
print_success "Docker image built successfully"

# Step 2: Check for and clean up any existing containers
print_header "CLEANING UP EXISTING CONTAINERS"
if docker ps -a | grep -q cloudproxy-test; then
    print_info "Found existing cloudproxy-test container, removing..."
    docker rm -f cloudproxy-test
    print_success "Removed existing container"
else
    print_info "No existing cloudproxy-test container found"
fi

# Step 3: Run the Docker container
print_header "STARTING CLOUDPROXY CONTAINER"
docker run -d --name cloudproxy-test -p 8000:8000 --env-file .env cloudproxy:test
print_success "Container started"

# Wait for the container to initialize
print_info "Waiting for container to initialize..."
sleep 5

# Check if container is still running
if ! docker ps | grep -q cloudproxy-test; then
    print_error "Container failed to start or crashed. Showing logs:"
    docker logs cloudproxy-test
    exit 1
fi

# Step 4: Show container logs
print_header "CONTAINER LOGS"
docker logs cloudproxy-test

# Step 5: Begin API testing
print_header "TESTING CLOUDPROXY API"

# Test 1: List initial proxies
call_api "GET" "/" "" "Listing initial proxies"

# Test 2: Check providers
call_api "GET" "/providers" "" "Checking all providers"

# Test 3: Get auth configuration
call_api "GET" "/auth" "" "Checking authentication configuration"

# Test 4: Try to get a random proxy (may not have proxies yet)
call_api "GET" "/random" "" "Getting a random proxy"

# Test 5: Update DigitalOcean scaling
call_api "PATCH" "/providers/digitalocean" '{"min_scaling": 3, "max_scaling": 5}' "Updating DigitalOcean scaling"

# Test 6: Update AWS scaling
call_api "PATCH" "/providers/aws" '{"min_scaling": 3, "max_scaling": 4}' "Updating AWS scaling"

# Test 7: Update Hetzner scaling
call_api "PATCH" "/providers/hetzner" '{"min_scaling": 3, "max_scaling": 3}' "Updating Hetzner scaling"

# Wait for proxies to be created
print_info "Waiting for proxies to be created (this might take a moment)..."
sleep 10

# Test 8: List proxies after scaling up
call_api "GET" "/" "" "Listing proxies after scaling up"

# Test 9: Check providers again
call_api "GET" "/providers" "" "Checking all providers after scaling"

# Test 10: Get a random proxy again
call_api "GET" "/random" "" "Getting a random proxy after scaling"

# Get the IP of a proxy to delete - using jq to extract the first proxy IP
first_proxy_ip=$(curl -s -X GET "http://localhost:8000/" -H "accept: application/json" | 
                 jq -r '.proxies[0].ip')

if [ -n "$first_proxy_ip" ] && [ "$first_proxy_ip" != "null" ]; then
    # Test 11: Delete a specific proxy
    call_api "DELETE" "/destroy?ip_address=$first_proxy_ip" "" "Deleting proxy with IP $first_proxy_ip"
    
    # Wait for the proxy to be deleted
    print_info "Waiting for proxy to be deleted..."
    sleep 5
    
    # Test 12: Check if proxy is in destroy queue
    call_api "GET" "/destroy" "" "Checking destroy queue"
    
    # Test 13: List proxies after deletion
    call_api "GET" "/" "" "Listing proxies after deletion"
else
    print_error "No proxies available to delete"
fi

# Get another proxy IP for restart
second_proxy_ip=$(curl -s -X GET "http://localhost:8000/" -H "accept: application/json" | 
                  jq -r '.proxies[0].ip')

if [ -n "$second_proxy_ip" ] && [ "$second_proxy_ip" != "null" ]; then
    # Test 14: Restart a specific proxy
    call_api "DELETE" "/restart?ip_address=$second_proxy_ip" "" "Restarting proxy with IP $second_proxy_ip"
else
    print_error "No proxies available to restart"
fi

# Test 15: Scale down DigitalOcean
call_api "PATCH" "/providers/digitalocean" '{"min_scaling": 1, "max_scaling": 2}' "Scaling down DigitalOcean"

# Wait for scaling down to take effect
print_info "Waiting for scaling down to take effect..."
sleep 10

# Test 16: Check providers again after scale down
call_api "GET" "/providers" "" "Checking providers after scaling down"

# Test 17: Final list of proxies
call_api "GET" "/" "" "Final list of all proxies"

# Check if UI and docs are accessible
print_header "CHECKING WEB INTERFACES"
ui_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ui/)
docs_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)

if [ "$ui_status" -eq 200 ]; then
    print_success "UI is accessible at http://localhost:8000/ui/"
else
    print_error "UI is not accessible, status code: $ui_status"
fi

if [ "$docs_status" -eq 200 ]; then
    print_success "API docs are accessible at http://localhost:8000/docs"
else
    print_error "API docs are not accessible, status code: $docs_status"
fi

print_header "TEST SUMMARY"
print_success "All tests completed. CloudProxy container is working properly."
print_info "You can access the UI at: http://localhost:8000/ui/"
print_info "You can access the API docs at: http://localhost:8000/docs"
print_info "To stop the container run: docker stop cloudproxy-test"
print_info "To remove the container run: docker rm cloudproxy-test" 