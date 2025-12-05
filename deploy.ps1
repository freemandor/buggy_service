# ensure errors stop the script
$ErrorActionPreference = "Stop"

# Load local deployment variables (kept out of git in .deploy.env)
if (-Not (Test-Path ".deploy.env")) {
    Write-Error ".deploy.env not found. Create it with BACKEND_IMAGE, FRONTEND_IMAGE, DB_PASSWORD."
    exit 1
}

Get-Content ".deploy.env" | ForEach-Object {
    if ($_ -match '^\s*$') { return }
    if ($_ -match '^\s*#') { return }
if ($_ -match '^(.*?)=(.*)$') {
        $envName = $matches[1]
        $envValue = $matches[2]
        Set-Item -Path ("Env:" + $envName) -Value $envValue
    }
}

$region = $env:REGION
if (-not $region) { $region = "eu-north-1" }
$ecrHost = "208017821414.dkr.ecr.$region.amazonaws.com"

$frontendApiBase = $env:FRONTEND_API_BASE
if (-not $frontendApiBase) {
    if (-not $env:ALB_URL) {
        Write-Error "ALB_URL or FRONTEND_API_BASE must be set in .deploy.env"
        exit 1
    }
    $frontendApiBase = ($env:ALB_URL.TrimEnd('/')) + "/api"
}

Write-Host "Logging into ECR ($ecrHost)..."
aws ecr get-login-password --region $region | docker login --username AWS --password-stdin $ecrHost

Write-Host "Building backend image $env:BACKEND_IMAGE ..."
docker build -t $env:BACKEND_IMAGE backend

Write-Host "Building frontend image $env:FRONTEND_IMAGE with VITE_API_BASE=$frontendApiBase ..."
docker build -t $env:FRONTEND_IMAGE --build-arg ("VITE_API_BASE=" + $frontendApiBase) frontend

Write-Host "Pushing images..."
docker push $env:BACKEND_IMAGE
docker push $env:FRONTEND_IMAGE

aws cloudformation deploy `
  --region $region `
  --stack-name buggy-service `
  --template-file stack.yaml `
  --capabilities CAPABILITY_IAM `
  --parameter-overrides `
    BackendImage=$env:BACKEND_IMAGE `
    FrontendImage=$env:FRONTEND_IMAGE `
    DbPassword=$env:DB_PASSWORD
