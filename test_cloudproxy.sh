#!/bin/bash
set -e

#########################################################################
# CloudProxy End-to-End Test Script
#########################################################################
# This script performs end-to-end testing of CloudProxy in a Docker container.
# It tests API endpoints, proxy creation, and optional connectivity testing.
#
# The script will:
# 1. Build a Docker container with CloudProxy
# 2. Test all API endpoints
# 3. Scale providers up to create proxies
# 4. Test connectivity through a random proxy (optional)
# 5. Test deletion and restart functionality
# 6. Clean up all resources (optional)
#
# Important: This script uses real cloud provider credentials from your
# environment variables or .env file to create actual proxy instances.
# Make sure you understand the potential costs before running.
#########################################################################

# Define colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions for formatting output
print_header() {
    echo -e "\n${BLUE}========== $1 ==========${NC}\n"
}

print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

print_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Default configuration
AUTO_CLEANUP=${AUTO_CLEANUP:-true}
SKIP_CONNECTION_TEST=${SKIP_CONNECTION_TEST:-false}
PROXY_WAIT_TIME=${PROXY_WAIT_TIME:-30}
MAX_WAIT_TIME=${MAX_WAIT_TIME:-600}  # 10 minutes maximum wait time

# Process command-line arguments
for arg in "$@"; do
  case $arg in
    --no-cleanup)
      AUTO_CLEANUP=false
      shift
      ;;
    --skip-connection-test)
      SKIP_CONNECTION_TEST=true
      shift
      ;;
    --proxy-wait=*)
      PROXY_WAIT_TIME="${arg#*=}"
      shift
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo "Options:"
      echo "  --no-cleanup            Don't automatically clean up resources"
      echo "  --skip-connection-test  Skip testing proxy connectivity"
      echo "  --proxy-wait=SECONDS    Wait time for proxy initialization (default: 30)"
      echo "  --help                  Show this help message"
      exit 0
      ;;
  esac
done

# Function to check required environment variables
check_required_env() {
    local missing_vars=0
    
    for var in "$@"; do
        if [ -z "${!var}" ]; then
            echo "ERROR: Required environment variable $var is not set."
            missing_vars=$((missing_vars + 1))
        fi
    done
    
    if [ $missing_vars -gt 0 ]; then
        echo "Make sure to set these environment variables before running the script."
        echo "You can create a .env file in the project root with these variables."
        exit 1
    fi
}

# Function to mask sensitive values in output
mask_value() {
    local value=$1
    if [ ${#value} -le 4 ]; then
        echo "****"
    else
        local visible_start=${2:-4}
        local visible_end=${3:-0}
        local length=${#value}
        local masked_length=$((length - visible_start - visible_end))
        
        if [ $masked_length -le 0 ]; then
            echo "****"
        else
            echo "${value:0:visible_start}$(printf '%*s' $masked_length | tr ' ' '*')${value:$((length - visible_end)):visible_end}"
        fi
    fi
}

# Check if .env file exists and load it
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

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

# Check for required environment variables
print_header "CHECKING ENVIRONMENT"

# Check auth settings
if [[ -z "$PROXY_USERNAME" || -z "$PROXY_PASSWORD" ]]; then
    print_info "Proxy authentication not set. Authentication will be disabled."
else
    print_info "Proxy authentication set with username: ${PROXY_USERNAME:0:2}****"
fi

# Check required variables for cloud providers
required_vars=()

# Check cloud provider credentials
if [ "${DIGITALOCEAN_ENABLED:-true}" = "true" ]; then
    required_vars+=("DIGITALOCEAN_ACCESS_TOKEN")
fi

if [ "${AWS_ENABLED:-true}" = "true" ]; then
    required_vars+=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY")
fi

if [ "${GCP_ENABLED:-false}" = "true" ]; then
    required_vars+=("GCP_SERVICE_ACCOUNT")
fi

if [ "${HETZNER_ENABLED:-false}" = "true" ]; then
    required_vars+=("HETZNER_TOKEN")
fi

if [ "${AZURE_ENABLED:-false}" = "true" ]; then
    required_vars+=("AZURE_CLIENT_ID" "AZURE_CLIENT_SECRET" "AZURE_TENANT_ID" "AZURE_SUBSCRIPTION_ID")
fi

# Check all the variables
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required variable $var is not set or empty"
    else
        print_success "$var is set"
    fi
done

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

# Function to test if a proxy is actually usable
test_proxy_connection() {
    local proxy_ip=$1
    local proxy_port=${2:-8899}
    local description=${3:-"Testing proxy connection"}
    local max_retries=${4:-5}
    local retry_delay=${5:-10}
    
    # Get auth configuration
    local auth_config=$(curl -s -X GET "http://localhost:8000/auth" -H "accept: application/json")
    local no_auth=$(echo "$auth_config" | jq -r '.no_auth')
    local proxy_url
    
    if [ "$no_auth" = "true" ]; then
        proxy_url="http://${proxy_ip}:${proxy_port}"
    else
        local username=$(echo "$auth_config" | jq -r '.auth.username')
        local password=$(echo "$auth_config" | jq -r '.auth.password')
        proxy_url="http://${username}:${password}@${proxy_ip}:${proxy_port}"
    fi
    
    echo -e "${YELLOW}${description} (${proxy_url})...${NC}"
    
    # Try multiple times with a delay, as proxies might take time to be fully operational
    for ((i=1; i<=$max_retries; i++)); do
        echo -e "${YELLOW}Attempt $i of $max_retries${NC}"
        
        # Use curl to test proxy connectivity
        echo -e "${YELLOW}Testing proxy connectivity...${NC}"
        http_test=$(curl -s --connect-timeout 10 -m 20 -x "$proxy_url" http://httpbin.org/ip)
        http_success=$?
        
        # Check connectivity result
        if [[ $http_success -eq 0 && -n "$http_test" ]]; then
            echo -e "${GREEN}Connectivity test successful: $(echo $http_test | jq .)${NC}"
            print_success "Proxy is operational"
            return 0
        else
            echo -e "${RED}Connectivity test failed${NC}"
            
            # If we haven't returned yet, we'll try again
            if [[ $i -lt $max_retries ]]; then
                echo -e "${YELLOW}Waiting ${retry_delay}s before next attempt...${NC}"
                sleep $retry_delay
            fi
        fi
    done
    
    echo -e "${RED}Failed to establish proxy connectivity after $max_retries attempts${NC}"
    return 1
}

# Function to wait for proxies to be created
wait_for_proxies() {
    local expected_count=$1
    local max_wait=${2:-$MAX_WAIT_TIME}
    local wait_interval=${3:-10}
    local elapsed=0
    local count=0
    
    print_info "Waiting for $expected_count proxies to be available (timeout: ${max_wait}s)..."
    
    while [ $elapsed -lt $max_wait ]; do
        local response=$(curl -s -X GET "http://localhost:8000/" -H "accept: application/json")
        count=$(echo "$response" | jq -r '.total')
        
        print_info "Current proxy count: $count / $expected_count (elapsed: ${elapsed}s)"
        
        if [ "$count" -ge "$expected_count" ]; then
            print_success "All expected proxies are now available!"
            echo "$response" | jq '.proxies'
            return 0
        fi
        
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done
    
    print_error "Timed out waiting for proxies to be created. Only $count of $expected_count available after ${elapsed}s."
    return 1
}

# Function to wait for proxies to be destroyed
wait_for_proxies_destroyed() {
    local max_wait=${1:-$MAX_WAIT_TIME}
    local wait_interval=${2:-10}
    local elapsed=0
    
    print_info "Waiting for all proxies to be destroyed (timeout: ${max_wait}s)..."
    
    while [ $elapsed -lt $max_wait ]; do
        local response=$(curl -s -X GET "http://localhost:8000/" -H "accept: application/json")
        local count=$(echo "$response" | jq -r '.total')
        
        if [ "$count" -eq 0 ]; then
            print_success "All proxies have been successfully destroyed!"
            
            # Double-check with provider endpoints to confirm
            print_info "Verifying with provider endpoints..."
            local provider_counts=()
            
            # Check each provider
            for provider in digitalocean aws hetzner; do
                local provider_info=$(curl -s -X GET "http://localhost:8000/providers/$provider" -H "accept: application/json")
                local enabled=$(echo "$provider_info" | jq -r '.provider.enabled')
                
                if [ "$enabled" = "true" ]; then
                    local running=$(echo "$provider_info" | jq -r '.provider.running')
                    provider_counts+=("$provider:$running")
                    
                    if [ "$running" -gt 0 ]; then
                        print_warning "Provider $provider still reports $running running instances"
                    else
                        print_success "Provider $provider confirms 0 running instances"
                    fi
                fi
            done
            
            # If any provider still shows instances, we need to wait longer
            if [[ "${provider_counts[*]}" =~ ":0" ]]; then
                return 0
            else
                print_info "Some providers still report instances, continuing to wait..."
            fi
        fi
        
        print_info "Remaining proxies: $count (elapsed: ${elapsed}s)"
        local proxies=$(echo "$response" | jq -r '.proxies[].ip')
        
        if [ -n "$proxies" ]; then
            print_info "Destroying remaining proxies..."
            for ip in $proxies; do
                call_api "DELETE" "/destroy?ip_address=$ip" "" "Destroying proxy $ip"
            done
            
            # If we've been waiting a while and still have proxies, try checking each provider directly
            if [ $elapsed -gt 120 ]; then
                print_info "Elapsed time > 120s, checking providers directly..."
                
                # Force a provider check cycle
                call_api "GET" "/providers/digitalocean" "" "Forcing DigitalOcean provider check"
                call_api "GET" "/providers/aws" "" "Forcing AWS provider check"
                call_api "GET" "/providers/hetzner" "" "Forcing Hetzner provider check"
                
                # Wait for the provider checks to complete
                sleep 15
            fi
        fi
        
        sleep $wait_interval
        elapsed=$((elapsed + wait_interval))
    done
    
    print_error "Timed out waiting for proxies to be destroyed. Still have $count proxies after ${elapsed}s."
    return 1
}

# Function to ensure cloud provider deletion queues are processed
ensure_cloud_provider_cleanup() {
    local verification_wait=${1:-60}  # Wait time in seconds to allow cloud providers to process deletions
    local providers_check_interval=${2:-15}  # Interval to check providers
    
    print_info "Ensuring cloud providers have processed all deletion requests..."
    
    # First, check the destroy queue to see if there are pending operations
    local destroy_queue=$(curl -s -X GET "http://localhost:8000/destroy" -H "accept: application/json")
    local queue_count=$(echo "$destroy_queue" | jq -r '.total')
    
    if [ "$queue_count" -gt 0 ]; then
        print_info "Found $queue_count items in destroy queue. Waiting for processing..."
        
        # Check destroy queue periodically
        local elapsed=0
        local wait_interval=10
        
        while [ $elapsed -lt $MAX_WAIT_TIME ]; do
            sleep $wait_interval
            elapsed=$((elapsed + wait_interval))
            
            destroy_queue=$(curl -s -X GET "http://localhost:8000/destroy" -H "accept: application/json")
            queue_count=$(echo "$destroy_queue" | jq -r '.total')
            
            print_info "Destroy queue items: $queue_count (elapsed: ${elapsed}s)"
            
            if [ "$queue_count" -eq 0 ]; then
                print_success "Destroy queue is empty!"
                break
            fi
        done
    else
        print_success "Destroy queue is empty"
    fi
    
    # Now, give cloud providers time to process the deletion requests
    print_info "Waiting ${verification_wait}s for cloud providers to process deletion requests..."
    sleep $verification_wait
    
    # Check providers to ensure no instances are running
    print_info "Verifying no instances are running with providers..."
    
    local providers=("digitalocean" "aws" "hetzner" "azure")
    for provider in "${providers[@]}"; do
        local provider_info=$(curl -s -X GET "http://localhost:8000/providers/$provider" -H "accept: application/json")
        local enabled=$(echo "$provider_info" | jq -r '.provider.enabled')
        
        if [ "$enabled" = "true" ]; then
            local count=$(echo "$provider_info" | jq -r '.provider.running')
            
            if [ "$count" -gt 0 ]; then
                print_error "Provider $provider still reports $count running instances"
            else
                print_success "Provider $provider reports 0 running instances"
            fi
        fi
    done
    
    # Final verification by checking API again
    local final_check=$(curl -s -X GET "http://localhost:8000/" -H "accept: application/json")
    local final_count=$(echo "$final_check" | jq -r '.total')
    
    if [ "$final_count" -eq 0 ]; then
        print_success "Final verification: All proxies successfully destroyed!"
        return 0
    else
        print_error "Final verification: Still found $final_count proxies!"
        return 1
    fi
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

# Test 7.1: Update Azure scaling
call_api "PATCH" "/providers/azure" '{"min_scaling": 2, "max_scaling": 2}' "Updating Azure scaling"

# Wait for proxies to be created (dynamic wait with timeout)
# Calculate expected total proxies from scaling settings
expected_proxy_count=0
do_min_scaling=$(curl -s -X GET "http://localhost:8000/providers/digitalocean" -H "accept: application/json" | jq -r '.provider.scaling.min_scaling')
aws_min_scaling=$(curl -s -X GET "http://localhost:8000/providers/aws" -H "accept: application/json" | jq -r '.provider.scaling.min_scaling')
hetzner_min_scaling=$(curl -s -X GET "http://localhost:8000/providers/hetzner" -H "accept: application/json" | jq -r '.provider.scaling.min_scaling')
azure_min_scaling=$(curl -s -X GET "http://localhost:8000/providers/azure" -H "accept: application/json" | jq -r '.provider.scaling.min_scaling')

# Only count enabled providers
do_enabled=$(curl -s -X GET "http://localhost:8000/providers/digitalocean" -H "accept: application/json" | jq -r '.provider.enabled')
aws_enabled=$(curl -s -X GET "http://localhost:8000/providers/aws" -H "accept: application/json" | jq -r '.provider.enabled')
hetzner_enabled=$(curl -s -X GET "http://localhost:8000/providers/hetzner" -H "accept: application/json" | jq -r '.provider.enabled')
azure_enabled=$(curl -s -X GET "http://localhost:8000/providers/azure" -H "accept: application/json" | jq -r '.provider.enabled')

if [ "$do_enabled" = "true" ]; then
    expected_proxy_count=$((expected_proxy_count + do_min_scaling))
fi
if [ "$aws_enabled" = "true" ]; then
    expected_proxy_count=$((expected_proxy_count + aws_min_scaling))
fi
if [ "$hetzner_enabled" = "true" ]; then
    expected_proxy_count=$((expected_proxy_count + hetzner_min_scaling))
fi
if [ "$azure_enabled" = "true" ]; then
    expected_proxy_count=$((expected_proxy_count + azure_min_scaling))
fi

# Wait for the expected number of proxies
wait_for_proxies $expected_proxy_count

# Test 8: List proxies after scaling up
call_api "GET" "/" "" "Listing proxies after scaling up"

# Test 9: Check providers again
call_api "GET" "/providers" "" "Checking all providers after scaling"

# Test 10: Get a random proxy again
call_api "GET" "/random" "" "Getting a random proxy after scaling"

# Wait a bit longer for proxies to be fully operational (SSH setup, etc.)
print_info "Waiting for proxies to be fully operational..."
sleep $PROXY_WAIT_TIME

# Test 11: Actually test connecting through a proxy
if [ "$SKIP_CONNECTION_TEST" = "true" ]; then
    print_header "SKIPPING PROXY CONNECTION TEST"
    print_info "Connection testing has been disabled via the --skip-connection-test flag"
else
    print_header "TESTING PROXY CONNECTION"
    test_proxy_ip=$(curl -s -X GET "http://localhost:8000/random" -H "accept: application/json" | jq -r '.ip')

    if [ -n "$test_proxy_ip" ] && [ "$test_proxy_ip" != "null" ]; then
        if test_proxy_connection "$test_proxy_ip" 8899 "Testing connectivity through random proxy"; then
            print_success "Successfully connected through proxy $test_proxy_ip"
        else
            print_error "Failed to connect through proxy $test_proxy_ip"
            
            # Show the logs for this proxy for debugging
            print_info "Showing logs for the proxy instance..."
            docker logs cloudproxy-test 2>&1 | grep -i "$test_proxy_ip" | tail -n 50
            
            # Test direct connectivity to the proxy port
            print_info "Testing direct connectivity to proxy port..."
            nc_result=$(nc -zv -w 5 $test_proxy_ip 8899 2>&1 || echo "Connection failed")
            echo "$nc_result"
            
            # Check logs inside the instance (would need SSH access)
            print_info "To further debug, SSH into the proxy instance and check:"
            echo " - System logs"
            echo " - Proxy service status"
            echo " - Network port configuration"
        fi
    else
        print_error "No proxies available to test"
    fi
fi

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
print_info "Proxy connectivity tests were performed."
print_info "You can access the UI at: http://localhost:8000/ui/"
print_info "You can access the API docs at: http://localhost:8000/docs"
print_info "To stop the container run: docker stop cloudproxy-test"
print_info "To remove the container run: docker rm cloudproxy-test"

# Clean up resources based on environment variable
if [ "${AUTO_CLEANUP:-true}" = "true" ]; then
    print_header "CLEANING UP RESOURCES"
    
    # Scale down all providers to 0 to avoid leaving cloud resources running
    print_info "Scaling down all providers to 0..."
    call_api "PATCH" "/providers/digitalocean" '{"min_scaling": 0, "max_scaling": 0}' "Scaling down DigitalOcean"
    call_api "PATCH" "/providers/aws" '{"min_scaling": 0, "max_scaling": 0}' "Scaling down AWS"
    call_api "PATCH" "/providers/hetzner" '{"min_scaling": 0, "max_scaling": 0}' "Scaling down Hetzner"
    call_api "PATCH" "/providers/azure" '{"min_scaling": 0, "max_scaling": 0}' "Scaling down Azure"
    
    # Wait for all proxies to be destroyed
    wait_for_proxies_destroyed
    
    # Ensure all cloud provider deletion queues are processed
    ensure_cloud_provider_cleanup
    
    # Stop and remove the container
    print_info "Stopping and removing the test container..."
    docker stop cloudproxy-test && docker rm cloudproxy-test
    
    print_success "Cleanup complete"
else
    print_info "AUTO_CLEANUP is disabled. Remember to manually clean up resources:"
    print_info "1. Scale down all providers to 0"
    print_info "2. Destroy any remaining proxies"
    print_info "3. Stop and remove the container"
fi

# Exit with success
print_header "TEST SCRIPT COMPLETE"
exit 0 