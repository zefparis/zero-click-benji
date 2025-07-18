#!/bin/bash

# Function to install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    pip install -r requirements.txt
}

# Function to run the GUI
run_gui() {
    echo "Running the GUI..."
    python3 src/app.py
}

# Function to handle environment variables for Hugging Face deployment
handle_env_variables() {
    echo "Setting up environment variables..."
    if [ -f .env ]; then 
        export $(cat .env | xargs)
    else
        echo ".env file not found. Please create one with the necessary environment variables."
        exit 1
    fi
}

# Function to deploy on Hugging Face
deploy_huggingface() {
    echo "Deploying on Hugging Face..."
    # Add deployment commands here
}

# Function to log deployment steps
log_deployment_step() {
    local step_message=$1
    echo "$(date +'%Y-%m-%d %H:%M:%S') - ${step_message}" >> deployment.log
}

# Function to handle errors
handle_error() {
    local error_message=$1
    echo "$(date +'%Y-%m-%d %H:%M:%S') - ERROR: ${error_message}" >> deployment.log
    exit 1
}

# Main function to execute all steps
main() {
    log_deployment_step "Starting deployment process"
    handle_env_variables || handle_error "Failed to handle environment variables"
    install_dependencies || handle_error "Failed to install dependencies"
    deploy_huggingface || handle_error "Failed to deploy on Hugging Face"
    run_gui || handle_error "Failed to run the GUI"
    log_deployment_step "Deployment process completed successfully"
}

# Execute the main function
main
