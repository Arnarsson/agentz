const http = require('http');
const { exec, execSync } = require('child_process');
const process = require('process');

const CONFIG = {
  port: 3000,
  checkInterval: 10000, // 10 seconds
  maxRetries: 3,
  startupGrace: 5000, // 5 seconds grace period after restart
  healthEndpoint: '/api/health'
};

let serverProcess = null;
let retryCount = 0;
let isRestarting = false;

function checkPort() {
  try {
    execSync(`lsof -i :${CONFIG.port} | grep LISTEN`);
    return true;
  } catch {
    return false;
  }
}

function killPort() {
  try {
    execSync(`lsof -ti :${CONFIG.port} | xargs kill -9`);
    console.log(`Killed processes on port ${CONFIG.port}`);
  } catch (err) {
    console.log(`No processes found on port ${CONFIG.port}`);
  }
}

function checkServer() {
  if (isRestarting) return;

  http.get(`http://localhost:${CONFIG.port}${CONFIG.healthEndpoint}`, (res) => {
    if (res.statusCode === 200) {
      console.log(`Server is healthy [${new Date().toISOString()}]`);
      retryCount = 0;
    } else {
      handleUnhealthyServer(`Unhealthy response: ${res.statusCode}`);
    }
  }).on('error', (err) => {
    handleUnhealthyServer(`Connection error: ${err.message}`);
  });
}

function handleUnhealthyServer(reason) {
  console.error(`Server unhealthy: ${reason} [${new Date().toISOString()}]`);
  retryCount++;
  
  if (retryCount >= CONFIG.maxRetries) {
    console.log('Max retries reached, restarting server...');
    restartServer();
  }
}

async function restartServer() {
  if (isRestarting) return;
  isRestarting = true;

  try {
    // Kill any existing processes on the port
    killPort();

    // Wait a moment for processes to fully terminate
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Start the server
    serverProcess = exec('npm run dev', (error, stdout, stderr) => {
      if (error) {
        console.error(`Error restarting server: ${error}`);
        isRestarting = false;
        return;
      }
    });

    // Pipe output to console
    serverProcess.stdout.pipe(process.stdout);
    serverProcess.stderr.pipe(process.stderr);

    // Reset state after grace period
    setTimeout(() => {
      console.log('Grace period ended, resuming health checks');
      retryCount = 0;
      isRestarting = false;
    }, CONFIG.startupGrace);

  } catch (err) {
    console.error('Failed to restart server:', err);
    isRestarting = false;
  }
}

// Clean up on exit
process.on('SIGINT', () => {
  console.log('\nShutting down monitor...');
  if (serverProcess) {
    serverProcess.kill();
  }
  killPort();
  process.exit();
});

// Initial start
console.log('Server monitoring started...');
if (checkPort()) {
  console.log(`Port ${CONFIG.port} is in use, killing existing processes...`);
  killPort();
}
restartServer();

// Start monitoring
setInterval(checkServer, CONFIG.checkInterval); 