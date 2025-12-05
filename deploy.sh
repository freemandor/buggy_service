#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f ".deploy.env" ]]; then
  echo ".deploy.env not found. Create it with BACKEND_IMAGE, FRONTEND_IMAGE, DB_PASSWORD (and optional ALB_URL)." >&2
  exit 1
fi

# Load key=value pairs from .deploy.env (ignoring comments/blank lines)
while IFS='=' read -r key value; do
  [[ -z "${key// }" ]] && continue
  [[ "${key:0:1}" == "#" ]] && continue
  export "$key"="$value"
done < .deploy.env

REGION="${REGION:-eu-north-1}"
ECR_HOST="208017821414.dkr.ecr.${REGION}.amazonaws.com"
FRONTEND_API_BASE="${FRONTEND_API_BASE:-${ALB_URL%/}/api}"

echo "Logging into ECR (${ECR_HOST})..."
aws ecr get-login-password --region "${REGION}" | docker login --username AWS --password-stdin "${ECR_HOST}"

echo "Building backend image ${BACKEND_IMAGE}..."
docker build -t "${BACKEND_IMAGE}" backend

echo "Building frontend image ${FRONTEND_IMAGE} with VITE_API_BASE=${FRONTEND_API_BASE}..."
docker build -t "${FRONTEND_IMAGE}" --build-arg VITE_API_BASE="${FRONTEND_API_BASE}" frontend

echo "Pushing images..."
docker push "${BACKEND_IMAGE}"
docker push "${FRONTEND_IMAGE}"

aws cloudformation deploy \
  --region "${REGION}" \
  --stack-name buggy-service \
  --template-file stack.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    BackendImage="$BACKEND_IMAGE" \
    FrontendImage="$FRONTEND_IMAGE" \
    DbPassword="$DB_PASSWORD" \
    AcmCertificateArn="$ACM_CERTIFICATE_ARN" \
    HttpsListenerArn="$HTTPS_LISTENER_ARN"
