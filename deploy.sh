#!/bin/bash

set -ex

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-europe-west8}"  # Milan, Italy

# Export all environment variables so they're available to subcommands
# This allows variables to be passed inline: DATABASE_URL="..." OPENAI_API_KEY="..." ./deploy.sh
export DATABASE_URL
export QDRANT_HOST
export QDRANT_PORT
export OPENAI_API_KEY
export OPENAI_MODEL
export OPENAI_FINETUNED_MODEL
export OPENAI_COMMUNICATION_MODEL
export OPENAI_EMBEDDING_MODEL
export SUPABASE_URL
export SUPABASE_SERVICE_ROLE_KEY
export SUPABASE_STORAGE_BUCKET_QRCODES
export SUPABASE_STORAGE_BUCKET_WINE_LABELS
export SECRET_KEY
export JWT_SECRET_KEY

echo "🚀 Deploying Bacco Sommelier AI to Google Cloud Platform"
echo "📍 Region: ${REGION}"
echo "🏗️  Project: ${PROJECT_ID}"

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ Error: PROJECT_ID not set. Please set GCP_PROJECT_ID environment variable or edit this script."
    exit 1
fi

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com --project=${PROJECT_ID}
gcloud services enable run.googleapis.com --project=${PROJECT_ID}
gcloud services enable containerregistry.googleapis.com --project=${PROJECT_ID}

# Set project
gcloud config set project ${PROJECT_ID}

# Create a temporary env file
echo "📄 Creating temporary env.yaml file..."
cat << EOT > env.yaml
DATABASE_URL: "${DATABASE_URL}"
QDRANT_HOST: "${QDRANT_HOST}"
QDRANT_PORT: "${QDRANT_PORT:-6333}"
OPENAI_API_KEY: "${OPENAI_API_KEY}"
OPENAI_MODEL: "${OPENAI_MODEL}"
OPENAI_FINETUNED_MODEL: "${OPENAI_FINETUNED_MODEL}"
OPENAI_COMMUNICATION_MODEL: "${OPENAI_COMMUNICATION_MODEL}"
OPENAI_EMBEDDING_MODEL: "${OPENAI_EMBEDDING_MODEL}"
SUPABASE_URL: "${SUPABASE_URL}"
SUPABASE_SERVICE_ROLE_KEY: "${SUPABASE_SERVICE_ROLE_KEY}"
SUPABASE_STORAGE_BUCKET_QRCODES: "${SUPABASE_STORAGE_BUCKET_QRCODES:-qrcodes}"
SUPABASE_STORAGE_BUCKET_WINE_LABELS: "${SUPABASE_STORAGE_BUCKET_WINE_LABELS:-wine-labels}"
SECRET_KEY: "${SECRET_KEY}"
JWT_SECRET_KEY: "${JWT_SECRET_KEY}"
FLASK_ENV: "production"
EOT

echo "🔍 Content of env.yaml:"
cat env.yaml

# 1. Build and Deploy Backend
echo "🔨 Building and Deploying backend..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/liber-backend:latest ./backend

gcloud run deploy liber-backend \
    --image gcr.io/${PROJECT_ID}/liber-backend:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080 \
    --env-vars-file env.yaml

# Clean up the env.yaml file
rm env.yaml

# 2. Get backend URL
BACKEND_URL=$(gcloud run services describe liber-backend --region=${REGION} --format="value(status.url)")
echo "✓ Backend deployed at: ${BACKEND_URL}"

# 3. Build Frontend (with backend URL as build arg)
echo "🔨 Building frontend..."
if command -v docker &> /dev/null; then
    echo "Building frontend with Docker locally..."
    docker build --build-arg VITE_API_URL=${BACKEND_URL}/api -t gcr.io/${PROJECT_ID}/liber-frontend:latest -f frontend/Dockerfile.production frontend/
    docker push gcr.io/${PROJECT_ID}/liber-frontend:latest
else
    echo "Docker not found. Using Cloud Build with cloudbuild.yaml..."
    gcloud builds submit \
        --config frontend/cloudbuild.yaml \
        --substitutions=_VITE_API_URL=${BACKEND_URL}/api \
        ./frontend
fi

# 4. Deploy Frontend
echo "🚀 Deploying frontend..."
gcloud run deploy liber-frontend \
    --image gcr.io/${PROJECT_ID}/liber-frontend:latest \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 5 \
    --min-instances 0 \
    --port 80

# 5. Get frontend URL
FRONTEND_URL=$(gcloud run services describe liber-frontend --region=${REGION} --format="value(status.url)")
echo "✓ Frontend deployed at: ${FRONTEND_URL}"

# 6. Update backend with frontend URL (for CORS)
echo "🔄 Updating backend with frontend URL..."
gcloud run services update liber-backend \
    --region ${REGION} \
    --update-env-vars "FRONTEND_URL=${FRONTEND_URL}"

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Service URLs:"
echo "   Backend API: ${BACKEND_URL}"
echo "   Frontend: ${FRONTEND_URL}"
echo ""
echo "📋 Next steps:"
echo "   1. Test the application at ${FRONTEND_URL}"
echo "   2. Set up custom domains (optional)"
echo "   3. Configure monitoring and logging"
echo "   4. Set up CI/CD for automatic deployments"
