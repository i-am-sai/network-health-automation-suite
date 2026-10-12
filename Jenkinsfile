    pipeline {
    agent any
    options { timestamps(); disableConcurrentBuilds() }
    environment {
        IMAGE = 'ghcr.io/i-am-sai/network-health-automation-suite'
    }
    stages {
        stage('Checkout') {
         steps {
         script {
           def scmVars = checkout scm
           env.BRANCH_REF = scmVars.GIT_BRANCH
           echo "Building branch: ${env.BRANCH_REF}"
    }
  }
}

        stage('Build image') {
        steps { sh 'docker build -t ${IMAGE}:build-${BUILD_NUMBER} .' }
        }

        stage('Test') {
        steps {
            withCredentials([
            string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID'),
            string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY'),
            string(credentialsId: 'ec2-host', variable: 'EC2_HOST'),
            sshUserPrivateKey(credentialsId: 'ec2-ssh-key', keyFileVariable: 'EC2_KEY', usernameVariable: 'EC2_USER')
            ]) {
            sh '''
                docker create --name suite-${BUILD_NUMBER} \
                -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
                -e EC2_SSH_HOST=${EC2_HOST} -e EC2_USER=${EC2_USER} \
                -e EC2_KEY_PATH=/tmp/ec2_key.pem \
                ${IMAGE}:build-${BUILD_NUMBER}
                docker cp "${EC2_KEY}" suite-${BUILD_NUMBER}:/tmp/ec2_key.pem
                set +e
                docker start -a suite-${BUILD_NUMBER}
                rc=$?
                mkdir -p reports
                docker cp suite-${BUILD_NUMBER}:/app/reports/logs ./reports/logs
                docker rm -f suite-${BUILD_NUMBER}
                exit $rc
            '''
            }
        }
        }

        stage('Push to GHCR') {
  steps {
    withCredentials([usernamePassword(credentialsId: 'ghcr-creds', usernameVariable: 'GH_USER', passwordVariable: 'GH_TOKEN')]) {
      sh '''
        echo "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin
        docker push ${IMAGE}:build-${BUILD_NUMBER}
      '''
      script {
        if (env.BRANCH_REF == 'origin/main') {
          sh '''
            docker tag ${IMAGE}:build-${BUILD_NUMBER} ${IMAGE}:latest
            docker push ${IMAGE}:latest
          '''
        }
      }
    }
  }
}

        stage('Deploy to EC2') {
            when { 
                expression { env.BRANCH_REF == 'origin/main' 
                }
        steps {
            withCredentials([
            string(credentialsId: 'ec2-host', variable: 'EC2_HOST'),
            sshUserPrivateKey(credentialsId: 'ec2-ssh-key', keyFileVariable: 'EC2_KEY', usernameVariable: 'EC2_USER')
            ]) {
            sh '''
                ssh -o StrictHostKeyChecking=no -i "${EC2_KEY}" ${EC2_USER}@${EC2_HOST} \
                "docker pull ${IMAGE}:latest && docker image prune -f"
            '''
            }
        }
        }
    }
    post {
     always {
     sh 'docker rm -f suite-${BUILD_NUMBER} || true'
    archiveArtifacts artifacts: 'reports/logs/*.log', allowEmptyArchive: true
        }
     }
    }
}