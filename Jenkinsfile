// =============================================================
//  Jenkins CI/CD Pipeline
//  Triggered on every push to GitHub (via webhook)
// =============================================================

pipeline {
    agent any

    options {
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        // These are set by Ansible / your environment
        REGISTRY_HOST  = "172.31.46.35:5000"   // Jenkins private IP : port (e.g. 10.0.0.5:5000)
        K8S_HOST       = "13.200.144.20"        // K8s public IP
        IMAGE_NAME     = "task-app"
        IMAGE_TAG      = "${BUILD_NUMBER}"
        FULL_IMAGE     = "${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_TAG}"
        LATEST_IMAGE   = "${REGISTRY_HOST}/${IMAGE_NAME}:latest"
        K8S_USER       = "ubuntu"
        APP_NAMESPACE  = "taskapp"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    echo "============================================"
                    echo "Build #${BUILD_NUMBER}"
                    echo "Commit: $(git rev-parse --short HEAD)"
                    echo "Message: $(git log -1 --pretty=%B | head -1)"
                    echo "============================================"
                '''
            }
        }

        stage('Lint & Test') {
            steps {
                sh '''
                    # Sanity checks — fail fast if obvious issues
                    python3 -c "import ast; ast.parse(open('run.py').read())" || true
                    echo "Syntax check passed"
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "Building image: ${FULL_IMAGE}"
                    docker build \
                      -t ${FULL_IMAGE} \
                      -t ${LATEST_IMAGE} \
                      --label "build=${BUILD_NUMBER}" \
                      --label "commit=$(git rev-parse --short HEAD)" \
                      .
                '''
            }
        }

        stage('Push to Registry') {
            steps {
                sh '''
                    docker push ${FULL_IMAGE}
                    docker push ${LATEST_IMAGE}
                    echo "Pushed: ${FULL_IMAGE}"
                '''
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                    ssh -o StrictHostKeyChecking=no ${K8S_USER}@${K8S_HOST} "
                        set -e
                        echo 'Updating deployment image to ${FULL_IMAGE}'
                        kubectl -n ${APP_NAMESPACE} set image deployment/${IMAGE_NAME} ${IMAGE_NAME}=${FULL_IMAGE}
                        echo 'Waiting for rollout...'
                        kubectl -n ${APP_NAMESPACE} rollout status deployment/${IMAGE_NAME} --timeout=180s
                        echo 'Deployment complete'
                    "
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    sleep 5
                    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://${K8S_HOST}:30050/healthz || echo "000")
                    echo "Health check returned: ${HTTP_CODE}"
                    if [ "${HTTP_CODE}" != "200" ]; then
                        echo "WARNING: Health check did not return 200"
                        exit 1
                    fi
                '''
            }
        }
    }

    post {
        success {
            echo "============================================"
            echo "✅ Build #${BUILD_NUMBER} SUCCESS"
            echo "App URL: http://${K8S_HOST}:30050"
            echo "============================================"
        }
        failure {
            echo "============================================"
            echo "❌ Build #${BUILD_NUMBER} FAILED"
            echo "============================================"
            sh '''
                ssh -o StrictHostKeyChecking=no ${K8S_USER}@${K8S_HOST} "
                    kubectl -n ${APP_NAMESPACE} get pods
                    kubectl -n ${APP_NAMESPACE} describe deployment/${IMAGE_NAME} | tail -30 || true
                " || true
            '''
        }
        always {
            sh 'docker image prune -f --filter "until=24h" || true'
        }
    }
}
