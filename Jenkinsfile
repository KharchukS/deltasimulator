// This shows a simple example of how to archive the build output artifacts.
node('linux') {
    stage('Checkout') {
        cleanWs()
        checkout scm
    }

    stage('Clean') {
        sh 'make clean'
    }

    stage('Build image and start container') {
        sh 'make container'
    }

    stage('License info') {
        sh 'make licenses'
        archiveArtifacts artifacts: 'licenses.csv, licenses.confluence'
    }

    stage('Docs') {
        sh 'make docs html'
        sh 'make docs epub'
        archiveArtifacts artifacts: 'docs/sphinx-build-html.log, docs/sphinx-build-epub.log'
        recordIssues(tools: [sphinxBuild(name: 'Docs',
                                         pattern: 'docs/sphinx-build-html.log',
                                         reportEncoding: 'UTF-8')])
        publishHTML([allowMissing: false,
                     alwaysLinkToLastBuild: true,
                     keepAll: false,
                     reportDir: '',
                     reportFiles: 'docs/_build/html/index.html',
                     reportName: 'Doxygen',
                     reportTitles: ''])
    }

    stage('Linting') {
        warnError('Error occured, continue to next stage.') {
            sh 'make pylint'
            archiveArtifacts artifacts: 'pylint.log'
            recordIssues(tools: [pyLint(name: 'Linting', 
                                        pattern: 'pylint.log')])
        }
    }

    stage('Style') {
        warnError('Error occured, continue to next stage.') {
            sh 'make pycodestyle'
            archiveArtifacts artifacts: 'pycodestyle.log'
            recordIssues(tools: [pep8(name: 'Style',
                                pattern: 'pycodestyle.log')])
        }
    }

    stage('Tests') {
        warnError('Error occured, catching exception and continuing to store test results.') {
            sh 'make test'
        }
    }

    if(env.BRANCH_NAME == 'release'){

        stage("Upload"){
            withCredentials([
                usernamePassword(credentialsId: 'PrivatePyPICreds',
                    usernameVariable: 'USERNAME',
                    passwordVariable: 'PASSWORD')
            ]) {
                sh 'make upload-package user=$USERNAME pass=$PASSWORD'
            }
        }

    } else if (env.CHANGE_ID || env.BRANCH_NAME == 'dev'){
        // On any pull request or a commit on dev branch

        stage('Package') {
            sh 'make test-package'
        }

    }

    stage('Clean container') {
        sh 'make clean-container'
    }

    stage ('Archive build outputs') {
        archiveArtifacts artifacts: '.coverage, coverage.xml, nosetests.xml'
        junit 'nosetests.xml'
        cobertura autoUpdateHealth: false,
        autoUpdateStability: false,
        coberturaReportFile: 'coverage.xml',
        conditionalCoverageTargets: '70, 0, 0',
        failUnhealthy: false,
        failUnstable: false,
        lineCoverageTargets: '80, 0, 0',
        maxNumberOfBuilds: 0,
        methodCoverageTargets: '80, 0, 0',
        onlyStable: false,
        sourceEncoding: 'ASCII',
        zoomCoverageChart: false
    }
}
